#!/usr/bin/env python3
"""
build_trailer.py — Assemble a cinematic ~30s "coming soon" trailer from a JSON
cut-sheet, OOM-safely (render each shot to its own file, concat-demux, then a
single light grade+audio pass).

WHY PER-SEGMENT: a single ffmpeg filtergraph with ~20+ looped image/video inputs
at 1080p will spike memory and get OOM-killed (SIGKILL / rc -9) in a sandbox.
Rendering shot-by-shot keeps peak memory tiny and is far more debuggable.

USAGE:
  python3 build_trailer.py cutsheet.json

CUT-SHEET SCHEMA:
{
  "output":"trailer.mp4",
  "width":1920,"height":1080,"fps":24,
  "letterbox":132,                      # px of top/bottom cinematic bars (0 to disable)
  "grade":{"brightness":-0.02,"saturation":0.96,"vignette":true},
  "audio":{"mode":"synth_tension","ambient_from":"c2.mp4"},  # ambient_from optional; "none" for silent bed
  "shots":[
    {"type":"card","image":"card1.png","dur":2.0,"fade":0.3},
    {"type":"footage","video":"c1.mp4","in":0.0,"out":2.0,"caption":"cap2.png","dur":2.0},
    {"type":"insert","image":"t_email.png","caption":"cap3.png","dur":2.0,"push":true},
    {"type":"endcard","image":"end.png","dur":3.4,"fade_in":0.9}
  ]
}

Shot types:
  card     -> full-frame opaque PNG, gentle fade in/out
  footage  -> trimmed video clip, cover-cropped, with optional transparent caption overlay
  insert   -> still image (e.g. email/dashboard screenshot), cover-crop + slow push, optional caption
  endcard  -> still image, slow fade-in, hold (title / "coming soon")

All paths are resolved relative to the cut-sheet file's directory.
"""
import json, os, subprocess, sys

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("FAIL rc %s\n%s\n" % (r.returncode, r.stderr[-2500:]))
        raise SystemExit(1)
    return r

def have_filter(name):
    r = subprocess.run(["ffmpeg","-hide_banner","-filters"], capture_output=True, text=True)
    return any(line.split()[1:2]==[name] or (" "+name+" ") in line for line in r.stdout.splitlines())

def main():
    cs_path = sys.argv[1] if len(sys.argv)>1 else "cutsheet.json"
    cs = json.load(open(cs_path))
    base = os.path.dirname(os.path.abspath(cs_path))
    def P(p): return p if os.path.isabs(p) else os.path.join(base, p)

    W = cs.get("width",1920); H = cs.get("height",1080); FPS = cs.get("fps",24)
    out = P(cs.get("output","trailer.mp4"))
    shots = cs["shots"]
    ENC = ["-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-r",str(FPS),"-an"]

    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"

    def render(out_seg, inputs, fc, vmap="[v]"):
        run(["ffmpeg","-y","-hide_banner","-loglevel","error"]+inputs+
            ["-filter_complex",fc,"-map",vmap]+ENC+[out_seg])

    def capfade(D, idx=1):
        d = 0.25
        return (f"[{idx}:v]format=rgba,fps={FPS},setsar=1,"
                f"fade=t=in:st=0:d={d}:alpha=1,fade=t=out:st={round(D-d,3)}:d={d}:alpha=1[c]")

    seg_files = []
    tmpdir = os.path.join(base, "_segs"); os.makedirs(tmpdir, exist_ok=True)

    for i, s in enumerate(shots):
        seg = os.path.join(tmpdir, f"seg{i:03d}.mp4"); seg_files.append(seg)
        t = s["type"]; D = float(s.get("dur",2.0))

        if t == "card":
            fade = float(s.get("fade",0.3))
            inputs = ["-loop","1","-t",str(D),"-i",P(s["image"])]
            fc = (f"[0:v]{cover},fade=t=in:st=0:d={fade},"
                  f"fade=t=out:st={round(D-fade,3)}:d={fade},format=yuv420p[v]")
            render(seg, inputs, fc)

        elif t == "endcard":
            fin = float(s.get("fade_in",0.9))
            inputs = ["-loop","1","-t",str(D),"-i",P(s["image"])]
            fc = f"[0:v]{cover},fade=t=in:st=0:d={fin},format=yuv420p[v]"
            render(seg, inputs, fc)

        elif t == "footage":
            t0 = float(s.get("in",0.0)); t1 = float(s.get("out", t0+D))
            cap = s.get("caption")
            inputs = ["-i",P(s["video"])]
            vbg = f"[0:v]trim={t0}:{t1},setpts=PTS-STARTPTS,{cover},format=yuv420p"
            if cap:
                inputs += ["-loop","1","-t",str(D),"-i",P(cap)]
                fc = (f"{vbg}[bg];{capfade(D)};"
                      f"[bg][c]overlay=0:0:format=auto,trim=0:{D},setpts=PTS-STARTPTS,format=yuv420p[v]")
            else:
                fc = f"{vbg},trim=0:{D},setpts=PTS-STARTPTS[v]"
            render(seg, inputs, fc)

        elif t == "insert":
            cap = s.get("caption"); push = s.get("push", True)
            fr = max(1, round(D*FPS))
            if push:
                z = (f"scale={int(W*1.25)}:{int(H*1.25)}:force_original_aspect_ratio=increase,"
                     f"crop={int(W*1.25)}:{int(H*1.25)},setsar=1,"
                     f"zoompan=z='min(1.06,1.0+0.05*on/{fr})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                     f"d=1:s={W}x{H}:fps={FPS}")
            else:
                z = cover
            inputs = ["-loop","1","-t",str(D),"-i",P(s["image"])]
            vbg = f"[0:v]{z},format=yuv420p"
            if cap:
                inputs += ["-loop","1","-t",str(D),"-i",P(cap)]
                fc = (f"{vbg}[bg];{capfade(D)};"
                      f"[bg][c]overlay=0:0:format=auto,trim=0:{D},setpts=PTS-STARTPTS,format=yuv420p[v]")
            else:
                fc = f"{vbg}[v]"
            render(seg, inputs, fc)
        else:
            raise SystemExit(f"unknown shot type: {t}")
        print(f"  shot {i:02d} [{t}] {D}s -> {os.path.basename(seg)}")

    # concat-demux (low memory)
    listf = os.path.join(tmpdir, "concat_list.txt")
    with open(listf,"w") as f:
        for sf in seg_files: f.write(f"file '{sf}'\n")
    joined = os.path.join(tmpdir, "joined_silent.mp4")
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",listf,"-c","copy",joined])

    T = round(sum(float(s.get("dur",2.0)) for s in shots), 2)

    # ---- grade + letterbox ----
    g = cs.get("grade",{})
    gchain = [f"eq=brightness={g.get('brightness',-0.02)}:saturation={g.get('saturation',0.96)}"]
    if g.get("vignette", True): gchain.append("vignette=angle=PI/5")
    lb = int(cs.get("letterbox",132))
    if lb > 0:
        gchain.append(f"drawbox=x=0:y=0:w={W}:h={lb}:color=black@1:t=fill")
        gchain.append(f"drawbox=x=0:y={H-lb}:w={W}:h={lb}:color=black@1:t=fill")
    gchain.append("format=yuv420p")
    grade = "[0:v]" + ",".join(gchain) + "[vout]"

    # ---- audio bed ----
    au = cs.get("audio",{}); amode = au.get("mode","synth_tension")
    amb = au.get("ambient_from")
    extra_inputs = []
    if amode == "none":
        audio = f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=0:{T}[aout]"
    else:
        boom_at = round(T-6,2)
        a = (f"sine=frequency=55:sample_rate=48000:duration={T}[d1];"
             f"sine=frequency=110:sample_rate=48000:duration={T}[d2];"
             f"[d1][d2]amix=inputs=2:duration=longest,volume='0.05+0.22*t/{T}':eval=frame,"
             f"tremolo=f=0.15:d=0.5,lowpass=f=320[drone];"
             f"sine=frequency=44:sample_rate=48000:duration={T},"
             f"volume='if(gt(t,{boom_at}),0.5*(t-{boom_at})/6,0)':eval=frame,lowpass=f=120[boom];")
        if amb and amb != "none":
            extra_inputs = ["-i", P(amb)]
            a += (f"[1:a]atrim=0:8,asetpts=PTS-STARTPTS,aloop=loop=8:size=384000,atrim=0:{T},"
                  f"volume=0.16,lowpass=f=1400,highpass=f=80[amb];"
                  f"[drone][boom][amb]amix=inputs=3:duration=first:weights='1 1 0.8',")
        else:
            a += f"[drone][boom]amix=inputs=2:duration=first:weights='1 1',"
        a += f"afade=t=in:st=0:d=0.6,afade=t=out:st={round(T-1.0,2)}:d=1.0,alimiter=limit=0.95[aout]"
        audio = a

    fc = grade + ";" + audio
    cmd = (["ffmpeg","-y","-hide_banner","-loglevel","error","-i",joined] + extra_inputs +
           ["-filter_complex",fc,"-map","[vout]","-map","[aout]","-t",str(T),"-r",str(FPS),
            "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart", out])
    print("final grade+audio pass...")
    run(cmd)
    print("DONE ->", out, f"({T}s)")

if __name__ == "__main__":
    main()

