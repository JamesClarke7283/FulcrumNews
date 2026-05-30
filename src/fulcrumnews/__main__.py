"""Entrypoint: ``python -m fulcrumnews`` serves the app via Hypercorn."""

from __future__ import annotations

import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

from . import create_app
from .config import settings


def main() -> None:
    app = create_app()
    config = Config()
    config.bind = [f"{settings.host}:{settings.port}"]
    config.loglevel = settings.log_level.lower()
    asyncio.run(serve(app, config))


if __name__ == "__main__":
    main()
