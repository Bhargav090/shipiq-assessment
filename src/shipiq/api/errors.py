from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import jsonify


@dataclass
class ApiError(Exception):
    code: str
    message: str
    http_status: int = 400

    def to_body(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message}}


def register_error_handlers(app: Any) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):  # type: ignore[no-untyped-def]
        body = err.to_body()
        return jsonify(body), err.http_status
