from __future__ import annotations

import threading
from dataclasses import dataclass, field

from shipiq.domain.models import Cargo, OptimizationResult, Tank


@dataclass
class _JobState:
    cargos: tuple[Cargo, ...] | None = None
    tanks: tuple[Tank, ...] | None = None
    result: OptimizationResult | None = None


class JobStore:
    """Thread-safe in-memory store for the latest job (demo / single-tenant)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = _JobState()

    def set_input(self, cargos: tuple[Cargo, ...], tanks: tuple[Tank, ...]) -> None:
        with self._lock:
            self._state.cargos = cargos
            self._state.tanks = tanks
            self._state.result = None

    def get_input(self) -> tuple[tuple[Cargo, ...] | None, tuple[Tank, ...] | None]:
        with self._lock:
            return self._state.cargos, self._state.tanks

    def set_result(self, result: OptimizationResult) -> None:
        with self._lock:
            self._state.result = result

    def get_result(self) -> OptimizationResult | None:
        with self._lock:
            return self._state.result
