#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skills_dir="$repo_root/skills"

command -v jq >/dev/null 2>&1 || {
  echo "convert.sh requires jq" >&2
  exit 1
}

rm -rf "$skills_dir"
mkdir -p "$skills_dir"

shopt -s nullglob
json_files=("$repo_root"/skill-*.json)

if ((${#json_files[@]} == 0)); then
  echo "No skill-*.json files found in $repo_root" >&2
  exit 1
fi

write_wrapped_description() {
  local text="$1"
  printf '%s\n' "$text" | fold -s -w 88 | sed 's/[[:space:]]*$//; s/^/  /'
}

write_bundled_scripts() {
  local json_file="$1"
  local skill_dir="$2"
  local count

  count="$(jq -r 'if .data.scripts == null then 0 else (.data.scripts | fromjson | length) end' "$json_file")"
  if ((count == 0)); then
    return
  fi

  mkdir -p "$skill_dir/scripts"

  for ((i = 0; i < count; i++)); do
    local filename
    filename="$(jq -r --argjson i "$i" '.data.scripts | fromjson | .[$i].filename' "$json_file")"

    case "$filename" in
      ""|/*|*..*)
        echo "Refusing unsafe script filename '$filename' in $json_file" >&2
        exit 1
        ;;
    esac

    jq -r --argjson i "$i" '.data.scripts | fromjson | .[$i].content' "$json_file" > "$skill_dir/scripts/$filename"
    if head -n 1 "$skill_dir/scripts/$filename" | grep -q '^#!'; then
      chmod +x "$skill_dir/scripts/$filename"
    fi
  done
}

write_bundled_references() {
  local json_file="$1"
  local skill_dir="$2"
  local count

  count="$(jq -r 'if .data.references == null then 0 else (.data.references | fromjson | length) end' "$json_file")"
  if ((count == 0)); then
    return
  fi

  mkdir -p "$skill_dir/references"

  for ((i = 0; i < count; i++)); do
    local filename
    filename="$(jq -r --argjson i "$i" '.data.references | fromjson | .[$i].filename' "$json_file")"

    case "$filename" in
      ""|/*|*..*)
        echo "Refusing unsafe reference filename '$filename' in $json_file" >&2
        exit 1
        ;;
    esac

    jq -r --argjson i "$i" '.data.references | fromjson | .[$i].content' "$json_file" > "$skill_dir/references/$filename"
  done
}

for json_file in "${json_files[@]}"; do
  base="$(basename "$json_file" .json)"
  skill_name="${base#skill-}"
  skill_dir="$skills_dir/$skill_name"
  skill_md="$skill_dir/SKILL.md"

  mkdir -p "$skill_dir"

  description="$(
    jq -r '
      def use_when:
        (.data.whenToUse // "")
        | if . == "" then empty
          elif test("^[Uu]se when") then .
          else "Use when: " + .
          end;
      [
        .data.description,
        use_when
      ]
      | map(select(. != null and . != ""))
      | join(" ")
    ' "$json_file"
  )"

  body="$(jq -r '.data.skillMdBody // .data.documentation // ""' "$json_file")"

  {
    printf '%s\n' "---"
    printf 'name: %s\n' "$skill_name"
    printf '%s\n' "description: >-"
    write_wrapped_description "$description"
    printf '%s\n\n' "---"
    printf '%s\n' "$body"
  } > "$skill_md"

  write_bundled_scripts "$json_file" "$skill_dir"
  write_bundled_references "$json_file" "$skill_dir"
done

echo "Generated ${#json_files[@]} skills in $skills_dir"
