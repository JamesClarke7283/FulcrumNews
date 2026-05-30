"""Create the SQLite schema and seed the default outlet roster.

    python -m fulcrumnews.tools.dbinit
"""

from __future__ import annotations

import asyncio
import logging

from ..config import settings
from ..db import close_db, init_db, seed_outlets


async def _main() -> None:
    logging.basicConfig(level=settings.log_level, format="%(levelname)s: %(message)s")
    await init_db()
    created = await seed_outlets()
    print(f"Database ready at {settings.sqlite_path}. Seeded {created} new outlet(s).")
    await close_db()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
