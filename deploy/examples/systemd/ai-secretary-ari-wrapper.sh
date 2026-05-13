#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${AI_SECRETARY_ARI_ENV_FILE:-/etc/ai-secretary/ari-app.env}"

if [[ ! -r "$ENV_FILE" ]]; then
  echo "ari_app wrapper: environment file is not readable: $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

PROJECT_DIR="${PROJECT_DIR:-/home/tulauser/AI-secrenar-with-Asterisk-node014}"
VENV_PYTHON="${VENV_PYTHON:-$PROJECT_DIR/.venv/bin/python}"
ARI_CONF_PATH="${ARI_CONF_PATH:-/home/tulauser/asterisk-config/ari.conf}"
ARI_USER="${ARI_USER:-ai_secretary2}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "ari_app wrapper: project directory is missing: $PROJECT_DIR" >&2
  exit 1
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "ari_app wrapper: virtualenv python is not executable: $VENV_PYTHON" >&2
  exit 1
fi

if [[ ! -r "$ARI_CONF_PATH" ]]; then
  echo "ari_app wrapper: ari.conf is not readable: $ARI_CONF_PATH" >&2
  exit 1
fi

ARI_PASSWORD_FROM_CONF="$(
  awk -v user="$ARI_USER" '
    BEGIN { in_user = 0 }
    /^[[:space:]]*\[/ {
      section = $0
      sub(/^[[:space:]]*\[/, "", section)
      sub(/\][[:space:]]*$/, "", section)
      in_user = (section == user)
      next
    }
    in_user && /^[[:space:]]*password[[:space:]]*=/ {
      line = $0
      sub(/^[[:space:]]*password[[:space:]]*=[[:space:]]*/, "", line)
      sub(/[[:space:]]*$/, "", line)
      print line
      exit
    }
  ' "$ARI_CONF_PATH" | tr -d '\r'
)"

if [[ -z "$ARI_PASSWORD_FROM_CONF" ]]; then
  echo "ari_app wrapper: ARI password was not found for user '$ARI_USER' in $ARI_CONF_PATH" >&2
  exit 1
fi

export ARI_PASSWORD="$ARI_PASSWORD_FROM_CONF"
export PYTHONPATH="${PYTHONPATH:-src}"
export PYTHONUNBUFFERED=1

cd "$PROJECT_DIR"
exec "$VENV_PYTHON" -u -m ai_secretary.telephony.ari_app
