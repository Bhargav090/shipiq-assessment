"""
Cargo–tank allocation with a single-cargo-type-per-tank constraint.

We model the problem as a mixed-integer linear program (MILP):

- Binary y[i,j]: tank j is dedicated to cargo i (at most one i per j).
- Continuous x[i,j] >= 0: volume of cargo i placed in tank j.

Constraints:
- sum_i y[i,j] <= 1  (each tank uses at most one cargo id)
- sum_i x[i,j] <= capacity[j]
- x[i,j] <= capacity[j] * y[i,j]
- sum_j x[i,j] <= volume[i]

Objective: maximize sum_{i,j} x[i,j].

This yields an optimal allocation for the stated objective and constraints.
For very large instances, the same module could be swapped for a heuristic
without changing the REST contract.
"""

from __future__ import annotations

import logging
from typing import Sequence

import pulp

from shipiq.domain.models import AllocationRow, Cargo, OptimizationResult, Tank

logger = logging.getLogger(__name__)


def allocate_cargo_to_tanks(
    cargos: Sequence[Cargo],
    tanks: Sequence[Tank],
    *,
    time_limit_seconds: int | None = 300,
) -> OptimizationResult:
    if not tanks:
        total_cargo = sum(c.volume for c in cargos)
        return OptimizationResult(
            status="optimal",
            total_loaded=0.0,
            total_cargo_volume=total_cargo,
            total_tank_capacity=0.0,
            allocations=(),
            solver_message="no tanks",
        )

    if not cargos:
        total_cap = sum(t.capacity for t in tanks)
        return OptimizationResult(
            status="optimal",
            total_loaded=0.0,
            total_cargo_volume=0.0,
            total_tank_capacity=total_cap,
            allocations=(),
            solver_message="no cargo",
        )

    cargo_list = list(cargos)
    tank_list = list(tanks)
    n_c, n_t = len(cargo_list), len(tank_list)

    total_cargo_volume = sum(c.volume for c in cargo_list)
    total_tank_capacity = sum(t.capacity for t in tank_list)

    prob = pulp.LpProblem("shipiq_allocation", pulp.LpMaximize)

    y: dict[tuple[int, int], pulp.LpVariable] = {}
    x: dict[tuple[int, int], pulp.LpVariable] = {}

    for i in range(n_c):
        for j in range(n_t):
            y[i, j] = pulp.LpVariable(f"y_{i}_{j}", cat=pulp.LpBinary)
            x[i, j] = pulp.LpVariable(f"x_{i}_{j}", lowBound=0)

    prob += pulp.lpSum(x[i, j] for i in range(n_c) for j in range(n_t))

    for j in range(n_t):
        prob += pulp.lpSum(y[i, j] for i in range(n_c)) <= 1
        cap_j = tank_list[j].capacity
        prob += pulp.lpSum(x[i, j] for i in range(n_c)) <= cap_j
        for i in range(n_c):
            prob += x[i, j] <= cap_j * y[i, j]

    for i in range(n_c):
        vol_i = cargo_list[i].volume
        prob += pulp.lpSum(x[i, j] for j in range(n_t)) <= vol_i

    solver = pulp.PULP_CBC_CMD(msg=False)
    if time_limit_seconds is not None:
        solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit_seconds)

    prob.solve(solver)
    status = pulp.LpStatus[prob.status]
    logger.debug("solver status=%s objective=%s", status, pulp.value(prob.objective))

    allocations: list[AllocationRow] = []
    if prob.status == pulp.LpStatusOptimal:
        for i in range(n_c):
            for j in range(n_t):
                val = pulp.value(x[i, j])
                if val is not None and val > 1e-9:
                    allocations.append(
                        AllocationRow(
                            tank_id=tank_list[j].id,
                            cargo_id=cargo_list[i].id,
                            volume=float(val),
                        )
                    )
        allocations.sort(key=lambda r: (r.tank_id, r.cargo_id))
        total_loaded = float(sum(a.volume for a in allocations))
    else:
        total_loaded = 0.0

    return OptimizationResult(
        status=status.lower(),
        total_loaded=total_loaded,
        total_cargo_volume=total_cargo_volume,
        total_tank_capacity=total_tank_capacity,
        allocations=tuple(allocations),
        solver_message=None,
    )
