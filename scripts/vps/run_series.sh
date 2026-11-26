#!/usr/bin/env bash
# Run experiment series one after another on the checked-out commit; stop on the first series
# that is not clean (any failed episode or audit issue).
#   run_series.sh E2 E3 E4-H1 E4-delay
# Env: MODEL (deepseek-v4-1-flash-1017), WORKERS (30), PROGRESS_LOG (~/series_progress.log),
#      EXTRA_ARGS (e.g. "--allow-test" for the test split; "" for dev).
set -u
[ "$#" -ge 1 ] || { echo "usage: run_series.sh SERIES..." >&2; exit 2; }
cd "$(dirname "$0")/../.." || exit 1
# Settings written by deploy.sh.
[ -r "$HOME/.series.env" ] && . "$HOME/.series.env"
MODEL=${MODEL:-deepseek-v4-1-flash-1017}
WORKERS=${WORKERS:-30}
LOG=${PROGRESS_LOG:-$HOME/series_progress.log}
EXTRA_ARGS=${EXTRA_ARGS---allow-test}
set -a; . ./.env; set +a
export PYTHONPATH=src
C=$(git rev-parse --short HEAD)
stamp() { date -u +%FT%TZ; }
[ -z "$(git status --porcelain)" ] || { echo "$(stamp) dirty tree, abort" >> "$LOG"; exit 1; }
for S in "$@"; do
  OUT=outputs/$(echo "$S" | tr 'A-Z' 'a-z')-$C
  mkdir -p "$OUT/$MODEL"
  echo "$(stamp) $S start -> $OUT" >> "$LOG"
  # shellcheck disable=SC2086
  python3 -m project_d.experiments.matrix "$S" $EXTRA_ARGS --provider mistral --model "$MODEL" \
    --reasoning-effort none --workers "$WORKERS" --output-dir "$OUT/$MODEL" > "$OUT/console.log" 2>&1
  rc=$?
  last=$(tail -1 "$OUT/console.log")
  echo "$(stamp) $S rc=$rc $last" >> "$LOG"
  python3 -c 'import json,sys; r=json.loads(sys.argv[1]); sys.exit(0 if r.get("failed")==0 and r.get("audit_issues")==0 else 1)' "$last" 2>/dev/null \
    || { echo "$(stamp) $S not clean, stop" >> "$LOG"; exit 1; }
  [ "$rc" -eq 0 ] || { echo "$(stamp) $S rc=$rc, stop" >> "$LOG"; exit 1; }
done
echo "$(stamp) ALL DONE" >> "$LOG"
