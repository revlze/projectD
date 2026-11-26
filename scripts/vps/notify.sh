#!/usr/bin/env bash
# Send one Telegram message from the control bot: notify.sh "text".
# Reads TG_TOKEN and TG_CHAT from $NOTIFY_ENV (default ~/.notify.env). Prints the HTTP status.
set -u
NOTIFY_ENV=${NOTIFY_ENV:-$HOME/.notify.env}
[ -r "$NOTIFY_ENV" ] || { echo "no $NOTIFY_ENV" >&2; exit 1; }
set -a; . "$NOTIFY_ENV"; set +a
curl -s -m 20 -o /dev/null -w "%{http_code}" "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TG_CHAT}" --data-urlencode "text=$1"
