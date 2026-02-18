"""CLI entry point for demo runs."""

from __future__ import annotations

import json

from .config.settings import Settings
from .core.runner import run_pipeline


def main() -> None:
    """Main entry point for running demos."""
    settings = Settings.from_env()
    mode = settings.demo_mode
    result = run_pipeline(mode, settings)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
