#!/usr/bin/env bash
# Remove secrets from the VPS after a run; with --all also remove the clone and the run log.
#   scripts/vps/cleanup.sh ne_vps        # .env and .notify.env only
#   scripts/vps/cleanup.sh ne_vps --all  # everything deploy.sh created
# Copy the outputs first (see scripts/vps/README.md).
set -euo pipefail
[ "$#" -ge 1 ] || { echo "usage: cleanup.sh HOST [--all]" >&2; exit 2; }
HOST=$1; ALL=${2:-}
ssh "$HOST" bash -s -- "$ALL" <<'EOF'
set -u
pgrep -f "[p]roject_d.experiments.matrix" >/dev/null && { echo "a run is still active" >&2; exit 1; }
rm -f ~/project-d/.env ~/.notify.env
if [ "$1" = "--all" ]; then
  rm -rf ~/project-d ~/series_progress.log ~/.series.env
fi
ls -d ~/project-d ~/.notify.env ~/series_progress.log ~/.series.env 2>/dev/null || echo "nothing left"
EOF
