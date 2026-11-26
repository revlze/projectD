#!/usr/bin/env bash
# Deploy the current commit to a VPS and run experiment series there in tmux:
#   scripts/vps/deploy.sh ne_vps E2 E3 E4-H1 E4-delay
# The VPS needs git, python3 >= 3.11, curl and tmux; no GitHub access (the repo goes as a bundle).
# Copies .env (MISTRAL_API_KEY) and, if present, $NOTIFY_ENV_LOCAL for Telegram notifications.
# Env: SESSION (series), NOTIFY_ENV_LOCAL (~/.config/project-d/notify.env), and MODEL, WORKERS,
#      EXTRA_ARGS, INTERVAL, written to ~/.series.env on the VPS for run_series.sh and watch.sh.
set -euo pipefail
[ "$#" -ge 2 ] || { echo "usage: deploy.sh HOST SERIES..." >&2; exit 2; }
HOST=$1; shift
cd "$(dirname "$0")/../.."
[ -z "$(git status --porcelain)" ] || { echo "commit or stash local changes first" >&2; exit 1; }
[ -r .env ] || { echo "no .env with MISTRAL_API_KEY" >&2; exit 1; }
COMMIT=$(git rev-parse HEAD)
SESSION=${SESSION:-series}
NOTIFY_ENV_LOCAL=${NOTIFY_ENV_LOCAL:-$HOME/.config/project-d/notify.env}
BUNDLE=$(mktemp -d)/project-d.bundle
git bundle create -q "$BUNDLE" HEAD
scp -q "$BUNDLE" "$HOST:/tmp/project-d.bundle"
rm -f "$BUNDLE"
ssh "$HOST" bash -s -- "$COMMIT" <<'EOF'
set -euo pipefail
COMMIT=$1
if [ -d ~/project-d/.git ]; then
  cd ~/project-d
  [ -z "$(git status --porcelain)" ] || { echo "remote tree is dirty" >&2; exit 1; }
  git fetch -q /tmp/project-d.bundle HEAD
else
  git clone -q /tmp/project-d.bundle ~/project-d
  cd ~/project-d
fi
git checkout -q --detach "$COMMIT"
rm -f /tmp/project-d.bundle
echo "remote at $(git rev-parse --short HEAD), dirty files: $(git status --porcelain | wc -l)"
EOF
scp -q .env "$HOST:project-d/.env"
ssh "$HOST" 'chmod 600 ~/project-d/.env'
WATCH=""
if [ -r "$NOTIFY_ENV_LOCAL" ]; then
  scp -q "$NOTIFY_ENV_LOCAL" "$HOST:.notify.env"
  ssh "$HOST" 'chmod 600 ~/.notify.env'
  WATCH=1
fi
# Run settings go to ~/.series.env, which run_series.sh and watch.sh source; unset ones keep
# the script defaults.
SETTINGS=$(
  for name in MODEL WORKERS INTERVAL EXTRA_ARGS; do
    if [ -n "${!name+x}" ]; then printf '%s=%q\n' "$name" "${!name}"; fi
  done
)
printf '%s\n' "$SETTINGS" | ssh "$HOST" 'cat > ~/.series.env'
ssh "$HOST" bash -s -- "$SESSION" "$WATCH" "$@" <<'EOF'
set -euo pipefail
SESSION=$1; WATCH=$2; shift 2
tmux has-session -t "$SESSION" 2>/dev/null && { echo "tmux session $SESSION exists" >&2; exit 1; }
tmux new-session -d -s "$SESSION" "bash ~/project-d/scripts/vps/run_series.sh $*; exec bash"
if [ -n "$WATCH" ]; then
  tmux new-window -d -t "$SESSION" -n notify "bash ~/project-d/scripts/vps/watch.sh; exec bash"
fi
tmux list-windows -t "$SESSION" -F "#{window_index}:#{window_name}"
EOF
echo "started: ssh $HOST, tmux attach -t $SESSION, log ~/series_progress.log"
