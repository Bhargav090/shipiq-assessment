from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Cargo:
    id: str
    volume: float

    def __post_init__(self) -> None:
        if not self.id or not str(self.id).strip():
            raise ValueError("cargo id must be non-empty")
        if self.volume < 0:
            raise ValueError("cargo volume cannot be negative")


@dataclass(frozen=True, slots=True)
class Tank:
    id: str
    capacity: float

    def __post_init__(self) -> None:
        if not self.id or not str(self.id).strip():
            raise ValueError("tank id must be non-empty")
        if self.capacity < 0:
            raise ValueError("tank capacity cannot be negative")


@dataclass(frozen=True, slots=True)
class AllocationRow:
    tank_id: str
    cargo_id: str
    volume: float


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    status: str
    total_loaded: float
    total_cargo_volume: float
    total_tank_capacity: float
    allocations: tuple[AllocationRow, ...] = field(default_factory=tuple)
    solver_message: str | None = None
