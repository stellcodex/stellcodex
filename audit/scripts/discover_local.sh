#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-/root/workspace/audit/output}"
mkdir -p "$OUT_DIR"
MAX_SIZE_BYTES="${MAX_SIZE_BYTES:-5242880}" # 5 MiB default

ROOTS=(
  /root
  /home
  /opt
  /var/www
  /workspace
  /mnt
  /srv
  /minio
)

PRUNE_PATHS=(
  '/root/.cache'
  '/root/.cargo'
  '/root/.rustup'
  '/root/.npm'
  '/root/.local/share/pnpm/store'
  '/root/.vscode-server'
  '/root/.config/google-chrome'
  '/root/.config/chromium'
  '/root/workspace/node_modules'
  '/root/workspace/.git'
)

INCLUDE_FIND_EXPR=(
  -iname '*.md' -o
  -iname '*.txt' -o
  -iname '*.yaml' -o
  -iname '*.yml' -o
  -iname '*.json' -o
  -iname '*.prompt' -o
  -iname '*.config' -o
  -iname '.env' -o
  -iname '.env.*' -o
  -iname '*prompt*' -o
  -iname '*instruction*' -o
  -iname '*policy*' -o
  -iname '*constitution*' -o
  -iname '*identity*' -o
  -iname '*role*' -o
  -iname '*agent*' -o
  -iname '*worker*' -o
  -iname '*protocol*' -o
  -iname '*playbook*' -o
  -iname '*rules*'
)

ARCHIVE_EXPR=(
  -iname '*.zip' -o
  -iname '*.tar' -o
  -iname '*.tar.gz' -o
  -iname '*.tgz' -o
  -iname '*.gz' -o
  -iname '*.bz2' -o
  -iname '*.xz'
)

FILELIST="$OUT_DIR/local_candidates.paths"
CONTENT_HITS="$OUT_DIR/local_content_hits.paths"
MERGED="$OUT_DIR/local_candidates_merged.paths"
INVENTORY="$OUT_DIR/local_inventory.csv"
ARCHIVES="$OUT_DIR/local_archives.csv"
ERRORS="$OUT_DIR/local_discovery.errors.log"

rm -f "$FILELIST" "$CONTENT_HITS" "$MERGED" "$INVENTORY" "$ARCHIVES" "$ERRORS"

for root in "${ROOTS[@]}"; do
  if [[ -d "$root" ]]; then
    find_cmd=(find "$root" -xdev)
    for p in "${PRUNE_PATHS[@]}"; do
      find_cmd+=( \( -path "$p" -o -path "$p/*" \) -prune -o )
    done
    find_cmd+=( -type f \( "${INCLUDE_FIND_EXPR[@]}" \) -print )
    "${find_cmd[@]}" 2>>"$ERRORS" || true
  fi
done | sort -u > "$FILELIST"

# Content keyword hits on common text-like files.
for root in "${ROOTS[@]}"; do
  if [[ -d "$root" ]]; then
    rg -i -l \
      -g '*.md' -g '*.txt' -g '*.yaml' -g '*.yml' -g '*.json' -g '*.prompt' -g '*.config' \
      -g '.env' -g '.env.*' \
      -g '!**/.cache/**' -g '!**/.cargo/**' -g '!**/.rustup/**' -g '!**/.npm/**' \
      -g '!**/.vscode-server/**' -g '!**/node_modules/**' -g '!**/.git/**' \
      '(stell|system prompt|worker prompt|agent role|constitution|global policy|tool policy|playbook|identity|routing rules)' \
      "$root" 2>>"$ERRORS" || true
  fi
done | sort -u > "$CONTENT_HITS"

cat "$FILELIST" "$CONTENT_HITS" | sort -u > "$MERGED"

printf 'source,path,filename,ext,mime,size_bytes,sha256,mtime_utc,snippet\n' > "$INVENTORY"

while IFS= read -r f; do
  [[ -f "$f" ]] || continue

  filename="$(basename "$f" | tr '"' "'")"
  ext="${filename##*.}"
  if [[ "$filename" == "$ext" ]]; then
    ext=""
  fi

  mime="$(file -b --mime-type "$f" 2>/dev/null || echo unknown)"
  size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
  sha=""
  if [[ "$size" -le "$MAX_SIZE_BYTES" ]]; then
    sha="$(sha256sum "$f" 2>/dev/null | awk '{print $1}' || echo '')"
  fi
  mtime="$(date -u -d "@$(stat -c '%Y' "$f" 2>/dev/null || echo 0)" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo '')"

  snippet=""
  if [[ "$mime" == text/* || "$mime" == application/json || "$mime" == application/x-yaml ]]; then
    if [[ "$size" -le "$MAX_SIZE_BYTES" ]]; then
      snippet="$(head -n 5 "$f" 2>/dev/null | tr '\n' ' ' | sed 's/"/'\''/g' | sed 's/[[:space:]]\+/ /g' | cut -c1-240)"
    else
      snippet="[SKIPPED_LARGE_FILE_FOR_SNIPPET]"
    fi
  fi

  printf '"%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' \
    "local_fs" \
    "$(printf '%s' "$f" | sed 's/"/'\''/g')" \
    "$filename" \
    "$ext" \
    "$mime" \
    "$size" \
    "$sha" \
    "$mtime" \
    "$snippet" >> "$INVENTORY"
done < "$MERGED"

printf 'path,size_bytes,sha256,mtime_utc\n' > "$ARCHIVES"
for root in "${ROOTS[@]}"; do
  if [[ -d "$root" ]]; then
    find_cmd=(find "$root" -xdev)
    for p in "${PRUNE_PATHS[@]}"; do
      find_cmd+=( \( -path "$p" -o -path "$p/*" \) -prune -o )
    done
    find_cmd+=( -type f \( "${ARCHIVE_EXPR[@]}" \) -print )
    "${find_cmd[@]}" 2>>"$ERRORS" || true
  fi
done | sort -u | while IFS= read -r f; do
  [[ -f "$f" ]] || continue
  size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
  sha="$(sha256sum "$f" 2>/dev/null | awk '{print $1}' || echo '')"
  mtime="$(date -u -d "@$(stat -c '%Y' "$f" 2>/dev/null || echo 0)" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo '')"
  printf '"%s","%s","%s","%s"\n' \
    "$(printf '%s' "$f" | sed 's/"/'\''/g')" \
    "$size" \
    "$sha" \
    "$mtime" >> "$ARCHIVES"
done

echo "Wrote:"
echo "  $INVENTORY"
echo "  $ARCHIVES"
echo "  $MERGED"
echo "  $ERRORS"
