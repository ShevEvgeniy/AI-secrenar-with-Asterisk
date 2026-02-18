"""API entry point."""

from __future__ import annotations

import os
from typing import Any


def create_app() -> Any:
    """Create the API application if dependencies are available."""
    try:
        from fastapi import FastAPI
    except ImportError as exc:
        raise RuntimeError("fastapi is not installed") from exc

    from .health import router as health_router
    from .calls import router as calls_router

    app = FastAPI(title="AI Secretary API")
    app.include_router(health_router)
    app.include_router(calls_router)
    return app


def main() -> None:
    """CLI entry point."""
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn is not installed") from exc

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("ai_secretary.api.main:create_app", host="0.0.0.0", port=port, factory=True)


if __name__ == "__main__":
    main()
