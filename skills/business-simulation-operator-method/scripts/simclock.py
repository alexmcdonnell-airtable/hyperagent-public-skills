#!/usr/bin/env python3
"""
Generic real-time simulation clock for business simulations.

THE RULE: anchor Day 1 to a calendar date ONCE, then always count forward.
Never re-derive the anchor from a milestone day-number — that's how
off-by-one drift creeps in and compounds.

Works for ANY venture you run in simulation — a shop, a restaurant, a
SaaS product, a boutique, a fund, an agency, a nonprofit, a creator
business. The milestone names below are placeholders; rename them to
your venture's real beats.

Configure the three constants below for YOUR simulation, then:
  python3 simclock.py              # today's sim-day + countdowns
  python3 simclock.py 2026-07-04   # sim-day for a date
  python3 simclock.py --day 100    # date for a sim-day
  python3 simclock.py --check      # verify user-confirmed checkpoints

Add a checkpoint every time the user confirms "today is Day X" —
the --check self-test then catches any future anchor corruption.
"""
import sys
from datetime import date, timedelta

# ── CONFIGURE FOR YOUR SIMULATION (the values here are EXAMPLES) ──
DAY_ONE = date(2026, 1, 5)            # the calendar date you call sim Day 1
MILESTONES = {                        # name -> date (your venture's beats)
    "Soft Launch": date(2026, 4, 1),
    "Launch Day":  date(2026, 4, 15),
}
CHECKPOINTS = {                       # user-confirmed: date -> expected day
    # add one each time the user says "today is Day X"
    date(2026, 2, 3): 30,
    date(2026, 3, 6): 61,
}
# ──────────────────────────────────────────────────────────────────

def sim_day(d): return (d - DAY_ONE).days + 1
def date_for(n): return DAY_ONE + timedelta(days=n - 1)

def main(argv):
    if "--check" in argv:
        ok = True
        for d, exp in CHECKPOINTS.items():
            got = sim_day(d)
            print(f"[{'OK' if got==exp else 'FAIL'}] {d} -> Day {got} (expected {exp})")
            ok &= got == exp
        sys.exit(0 if ok else 1)
    if "--day" in argv:
        n = int(argv[argv.index("--day") + 1])
        print(f"Day {n} = {date_for(n).strftime('%A, %B %d, %Y')}"); return
    d = date.fromisoformat(argv[1]) if len(argv) > 1 else date.today()
    print(f"Day {sim_day(d)} · {d.strftime('%A, %B %d, %Y')}")
    for name, md in MILESTONES.items():
        print(f"  {(md - d).days} days to {name} ({md.strftime('%b %d')})")

if __name__ == "__main__":
    main(sys.argv)

