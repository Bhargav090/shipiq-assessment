from __future__ import annotations

from typing import Any, Iterable

from shipiq.api.errors import ApiError
from shipiq.domain.models import Cargo, Tank


def _as_positive_number(name: str, raw: Any, *, allow_zero: bool) -> float:
    if raw is None:
        raise ApiError("invalid_payload", f"missing numeric field: {name}")
    try:
        v = float(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError("invalid_payload", f"{name} must be a number") from exc
    if v < 0 or (not allow_zero and v == 0):
        raise ApiError("invalid_payload", f"{name} must be {'non-negative' if allow_zero else 'positive'}")
    return v


def _unique_ids(items: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for i in items:
        if i in seen:
            raise ApiError("invalid_payload", f"duplicate {label} id: {i}")
        seen.add(i)


def parse_cargos_tanks(body: Any) -> tuple[tuple[Cargo, ...], tuple[Tank, ...]]:
    if not isinstance(body, dict):
        raise ApiError("invalid_payload", "JSON object expected")

    cargos_raw = body.get("cargos")
    tanks_raw = body.get("tanks")
    if not isinstance(cargos_raw, list) or not isinstance(tanks_raw, list):
        raise ApiError("invalid_payload", "cargos and tanks must be arrays")

    cargos: list[Cargo] = []
    for idx, row in enumerate(cargos_raw):
        if not isinstance(row, dict):
            raise ApiError("invalid_payload", f"cargos[{idx}] must be an object")
        cid = row.get("id")
        if not isinstance(cid, str) or not cid.strip():
            raise ApiError("invalid_payload", f"cargos[{idx}].id must be a non-empty string")
        vol = _as_positive_number(f"cargos[{idx}].volume", row.get("volume"), allow_zero=False)
        try:
            cargos.append(Cargo(id=cid.strip(), volume=vol))
        except ValueError as exc:
            raise ApiError("invalid_payload", str(exc)) from exc

    tanks: list[Tank] = []
    for idx, row in enumerate(tanks_raw):
        if not isinstance(row, dict):
            raise ApiError("invalid_payload", f"tanks[{idx}] must be an object")
        tid = row.get("id")
        if not isinstance(tid, str) or not tid.strip():
            raise ApiError("invalid_payload", f"tanks[{idx}].id must be a non-empty string")
        cap = _as_positive_number(f"tanks[{idx}].capacity", row.get("capacity"), allow_zero=False)
        try:
            tanks.append(Tank(id=tid.strip(), capacity=cap))
        except ValueError as exc:
            raise ApiError("invalid_payload", str(exc)) from exc

    _unique_ids((c.id for c in cargos), "cargo")
    _unique_ids((t.id for t in tanks), "tank")

    return tuple(cargos), tuple(tanks)
