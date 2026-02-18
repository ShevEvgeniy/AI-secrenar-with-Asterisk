#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=src
poetry run python -m ai_secretary.api.main
