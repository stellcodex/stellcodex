#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-/root/workspace/audit/output}"
mkdir -p "$OUT_DIR"

ROOTS=(
  /root/workspace
  /root
  /home
  /opt
  /var/www
  /mnt
  /minio
)

MAX_HASH_SIZE_BYTES="${MAX_HASH_SIZE_BYTES:-10485760}" # 10 MiB

PRUNE_GLOBS=(
  '/proc/*'
  '/sys/*'
  '/dev/*'
  '/run/*'
  '/tmp/*'
  '/root/.cache/*'
  '/root/.cargo/*'
  '/root/.rustup/*'
  '/root/.npm/*'
  '/root/.vscode-server/*'
  '/root/workspace/node_modules/*'
  '/root/workspace/.git/*'
)

KW_PATH='prompt|instruction|policy|constitution|identity|role|agent|worker|protocol|playbook|rules|stell'
KW_CONTENT='stell|system prompt|worker prompt|agent role|global policy|constitution|tool policy|playbook|identity|routing rules|STELL_PROMPT|ACTIVE_PROMPT'

PATH_HITS="$OUT_DIR/focused_path_hits.paths"
CONTENT_HITS="$OUT_DIR/focused_content_hits.paths"
MERGED="$OUT_DIR/focused_candidates.paths"
INVENTORY="$OUT_DIR/focused_inventory.csv"
ARCHIVES="$OUT_DIR/focused_archives.csv"
ERRORS="$OUT_DIR/focused_discovery.errors.log"

rm -f "$PATH_HITS" "$CONTENT_HITS" "$MERGED" "$INVENTORY" "$ARCHIVES" "$ERRORS"

for root in "${ROOTS[@]}"; do
  [[ -d "$root" ]] || continue
  find "$root" -xdev -type f \
    \( -iname '*.md' -o -iname '*.txt' -o -iname '*.yaml' -o -iname '*.yml' -o -iname '*.json' -o -iname '*.prompt' -o -iname '*.config' -o -iname '.env' -o -iname '.env.*' \) \
    ! -path '/proc/*' ! -path '/sys/*' ! -path '/dev/*' ! -path '/run/*' ! -path '/tmp/*' \
    ! -path '/root/.cache/*' ! -path '/root/.cargo/*' ! -path '/root/.rustup/*' ! -path '/root/.npm/*' ! -path '/root/.vscode-server/*' \
    ! -path '/root/workspace/node_modules/*' ! -path '/root/workspace/.git/*' \
    | rg -i "/(${KW_PATH})" >> "$PATH_HITS" 2>>"$ERRORS" || true
done

for root in "${ROOTS[@]}"; do
  [[ -d "$root" ]] || continue
  rg -i -l --max-filesize 2M \
    -g '*.md' -g '*.txt' -g '*.yaml' -g '*.yml' -g '*.json' -g '*.prompt' -g '*.config' -g '.env' -g '.env.*' \
    -g '!**/.cache/**' -g '!**/.cargo/**' -g '!**/.rustup/**' -g '!**/.npm/**' -g '!**/.vscode-server/**' -g '!**/node_modules/**' -g '!**/.git/**' \
    "(${KW_CONTENT})" "$root" >> "$CONTENT_HITS" 2>>"$ERRORS" || true
done

cat "$PATH_HITS" "$CONTENT_HITS" 2>/dev/null | sort -u > "$MERGED"

printf 'source,path,filename,ext,mime,size_bytes,sha256,mtime_utc,snippet\n' > "$INVENTORY"
while IFS= read -r f; do
  [[ -f "$f" ]] || continue
  filename="$(basename "$f" | tr '"' "'")"
  ext="${filename##*.}"
  [[ "$filename" == "$ext" ]] && ext=""
  mime="$(file -b --mime-type "$f" 2>/dev/null || echo unknown)"
  size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
  mtime="$(date -u -d "@$(stat -c '%Y' "$f" 2>/dev/null || echo 0)" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo '')"
  sha=""
  if [[ "$size" -le "$MAX_HASH_SIZE_BYTES" ]]; then
    sha="$(sha256sum "$f" 2>/dev/null | awk '{print $1}' || echo '')"
  fi
  snippet=""
  if [[ "$mime" == text/* || "$mime" == application/json || "$mime" == application/x-yaml ]]; then
    snippet="$(head -n 5 "$f" 2>/dev/null | tr '\n' ' ' | sed 's/"/'\''/g' | sed 's/[[:space:]]\+/ /g' | cut -c1-240)"
  fi
  printf '"%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' \
    "focused_fs" \
    "$(printf '%s' "$f" | sed 's/"/'\''/g')" \
    "$filename" "$ext" "$mime" "$size" "$sha" "$mtime" "$snippet" >> "$INVENTORY"
done < "$MERGED"

printf 'path,size_bytes,sha256,mtime_utc\n' > "$ARCHIVES"
for root in "${ROOTS[@]}"; do
  [[ -d "$root" ]] || continue
  find "$root" -xdev -type f \
    \( -iname '*.zip' -o -iname '*.tar' -o -iname '*.tar.gz' -o -iname '*.tgz' -o -iname '*.gz' -o -iname '*.bz2' -o -iname '*.xz' \) \
    ! -path '/proc/*' ! -path '/sys/*' ! -path '/dev/*' ! -path '/run/*' ! -path '/tmp/*' \
    ! -path '/root/.cache/*' ! -path '/root/.cargo/*' ! -path '/root/.rustup/*' ! -path '/root/.npm/*' ! -path '/root/.vscode-server/*' \
    ! -path '/root/workspace/node_modules/*' ! -path '/root/workspace/.git/*'
done | sort -u | while IFS= read -r f; do
  [[ -f "$f" ]] || continue
  size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
  mtime="$(date -u -d "@$(stat -c '%Y' "$f" 2>/dev/null || echo 0)" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo '')"
  sha="$(sha256sum "$f" 2>/dev/null | awk '{print $1}' || echo '')"
  printf '"%s","%s","%s","%s"\n' "$(printf '%s' "$f" | sed 's/"/'\''/g')" "$size" "$sha" "$mtime" >> "$ARCHIVES"
done

echo "Wrote:"
echo "  $INVENTORY"
echo "  $ARCHIVES"
echo "  $MERGED"
echo "  $ERRORS"
