"""Entry point: `jarvis` or `python -m jarvis` boots the whole OS."""

from __future__ import annotations

import logging

import uvicorn

from jarvis.api.app import create_app
from jarvis.config import settings


def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    app = create_app()
    print(
        f"\n  J.A.R.V.I.S. AI OS\n"
        f"  Dashboard: http://{settings.host}:{settings.port}\n"
        f"  API-Docs:  http://{settings.host}:{settings.port}/docs\n"
    )
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
