"""FulcrumNews — an open-source Ground News replacement.

``create_app()`` is the Quart application factory.
"""

from __future__ import annotations

import logging

from quart import Quart

from .config import settings

__version__ = "0.1.0"


def create_app() -> Quart:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Quart(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = settings.openrouter_api_key or "dev-secret"

    # Database + seed (before/after_serving hooks).
    from .db import register_orm

    register_orm(app)

    # Jinja filters.
    from .web.filters import register_filters

    register_filters(app)

    # Blueprints.
    from .web.blueprints import admin, api, feed, outlets, story

    app.register_blueprint(feed.bp)
    app.register_blueprint(story.bp)
    app.register_blueprint(outlets.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)

    # Background scheduler lifecycle.
    from .scheduler import start_scheduler, stop_scheduler

    @app.before_serving
    async def _start_scheduler() -> None:
        start_scheduler()

    @app.after_serving
    async def _stop_scheduler() -> None:
        stop_scheduler()

    # Error handlers.
    from quart import render_template

    @app.errorhandler(404)
    async def _not_found(_e):
        return await render_template("errors/404.html"), 404

    return app
