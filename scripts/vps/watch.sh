#!/usr/bin/env bash
# Forward run_series.sh events to Telegram at once, send a progress summary every INTERVAL
# seconds (default 300) and alert if the run stops without "ALL DONE".
# Env: PROGRESS_LOG (~/series_progress.log), INTERVAL (300), NOTIFY_ENV (see notify.sh).
set -u
cd "$(dirname "$0")/../.." || exit 1
# Settings written by deploy.sh.
[ -r "$HOME/.series.env" ] && . "$HOME/.series.env"
HERE=scripts/vps
LOG=${PROGRESS_LOG:-$HOME/series_progress.log}
INTERVAL=${INTERVAL:-300}
C=$(git rev-parse --short HEAD)
touch "$LOG"
sent=$(wc -l < "$LOG"); last_summary=0; idle=0
summary() {
  python3 - "$C" <<'PY'
import glob, json, os, sys
commit = sys.argv[1]; parts = []; fail = audit = 0
for d in sorted(glob.glob(f"outputs/*-{commit}")):
    for sub in glob.glob(d + "/*/run_manifest.json"):
        root = os.path.dirname(sub)
        rows = [json.load(open(f)) for f in glob.glob(root + "/*.summary.json")]
        planned = len(json.load(open(sub))["episodes"])
        name = os.path.basename(d)[: -len(commit) - 1].upper()
        parts.append(f"{name} {len(rows)}/{planned}")
        fail += sum(r["failure"] is not None for r in rows)
        audit += sum(r["audit_issues"] or 0 for r in rows)
print(f"project-d {commit}: " + (", ".join(parts) or "нет серий") + f"; сбоев {fail}, ошибок аудита {audit}")
PY
}
while true; do
  n=$(wc -l < "$LOG")
  if [ "$n" -gt "$sent" ]; then
    tail -n +$((sent + 1)) "$LOG" | while IFS= read -r line; do "$HERE/notify.sh" "project-d: $line" >/dev/null; done
    sent=$n
  fi
  if tail -n 1 "$LOG" | grep -qE "ALL DONE|stop|abort"; then "$HERE/notify.sh" "$(summary)" >/dev/null; exit 0; fi
  if pgrep -f "[p]roject_d.experiments.matrix" >/dev/null || pgrep -f "[r]un_series.sh" >/dev/null; then
    idle=0
  else
    idle=$((idle + 1))
  fi
  if [ "$idle" -ge 2 ]; then
    "$HERE/notify.sh" "project-d: ВНИМАНИЕ, прогон не запущен и не завершён. $(summary)" >/dev/null
    exit 1
  fi
  now=$(date +%s)
  if [ $((now - last_summary)) -ge "$INTERVAL" ]; then "$HERE/notify.sh" "$(summary)" >/dev/null; last_summary=$now; fi
  sleep 30
done
