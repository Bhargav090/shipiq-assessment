from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from shipiq.api.errors import ApiError
from shipiq.api.validation import parse_cargos_tanks
from shipiq.domain.models import OptimizationResult
from shipiq.services.allocation_optimizer import allocate_cargo_to_tanks

logger = logging.getLogger(__name__)

bp = Blueprint("shipiq", __name__)


def _serialize_result(r: OptimizationResult) -> dict[str, Any]:
    return {
        "status": r.status,
        "total_loaded": r.total_loaded,
        "total_cargo_volume": r.total_cargo_volume,
        "total_tank_capacity": r.total_tank_capacity,
        "allocations": [
            {"tank_id": a.tank_id, "cargo_id": a.cargo_id, "volume": a.volume}
            for a in r.allocations
        ],
        "solver_message": r.solver_message,
    }


@bp.get("/health")
def health() -> Any:
    return jsonify({"status": "ok"}), 200


@bp.post("/input")
def post_input() -> Any:
    body = request.get_json(silent=True)
    cargos, tanks = parse_cargos_tanks(body)
    store = current_app.extensions["job_store"]
    store.set_input(cargos, tanks)
    logger.info("stored input cargos=%s tanks=%s", len(cargos), len(tanks))
    return (
        jsonify(
            {
                "accepted": True,
                "cargos": len(cargos),
                "tanks": len(tanks),
            }
        ),
        202,
    )


@bp.post("/optimize")
def post_optimize() -> Any:
    store = current_app.extensions["job_store"]
    cargos, tanks = store.get_input()
    if cargos is None or tanks is None:
        raise ApiError("no_input", "call POST /input first", http_status=409)

    result = allocate_cargo_to_tanks(cargos, tanks)
    store.set_result(result)
    logger.info(
        "optimize status=%s total_loaded=%s",
        result.status,
        result.total_loaded,
    )
    return jsonify(_serialize_result(result)), 200


@bp.get("/results")
def get_results() -> Any:
    store = current_app.extensions["job_store"]
    result = store.get_result()
    if result is None:
        raise ApiError("no_results", "run POST /optimize first", http_status=404)
    return jsonify(_serialize_result(result)), 200
