from __future__ import annotations

import logging
import os

from flask import Flask

from shipiq.api.errors import register_error_handlers
from shipiq.api.routes import bp
from shipiq.application.job_store import JobStore
from shipiq.config import Settings


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.extensions["job_store"] = JobStore()
    app.extensions["settings"] = settings

    register_error_handlers(app)
    app.register_blueprint(bp, url_prefix="")

    @app.before_request
    def _optional_api_key() -> None:
        if not settings.api_key:
            return
        from flask import jsonify, request

        if request.path == "/health":
            return
        provided = request.headers.get("X-API-Key", "")
        if provided != settings.api_key:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "unauthorized",
                            "message": "invalid or missing X-API-Key",
                        }
                    }
                ),
                401,
            )

    return app


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")


if __name__ == "__main__":
    main()
