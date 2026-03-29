import pytest

from shipiq.domain.models import Cargo, Tank
from shipiq.services.allocation_optimizer import allocate_cargo_to_tanks


def test_single_tank_single_cargo_fits():
    r = allocate_cargo_to_tanks([Cargo("C1", 50)], [Tank("T1", 100)])
    assert r.status == "optimal"
    assert r.total_loaded == pytest.approx(50)
    assert len(r.allocations) == 1
    assert r.allocations[0].volume == pytest.approx(50)


def test_split_one_cargo_across_two_tanks():
    r = allocate_cargo_to_tanks(
        [Cargo("A", 150)],
        [Tank("T1", 100), Tank("T2", 100)],
    )
    assert r.status == "optimal"
    assert r.total_loaded == pytest.approx(150)
    by_tank = {a.tank_id: a.volume for a in r.allocations}
    assert len(by_tank) == 2
    assert sum(by_tank.values()) == pytest.approx(150)
    assert all(a.cargo_id == "A" for a in r.allocations)


def test_tank_exclusive_cargo_assignment_maximizes_volume():
    """Greedy tank ordering can fail; MILP should pick the global optimum."""
    r = allocate_cargo_to_tanks(
        [Cargo("A", 100), Cargo("B", 50)],
        [Tank("big", 80), Tank("small", 60)],
    )
    assert r.status == "optimal"
    assert r.total_loaded == pytest.approx(130)


def test_no_tanks():
    r = allocate_cargo_to_tanks([Cargo("C1", 10)], [])
    assert r.status == "optimal"
    assert r.total_loaded == 0
    assert r.total_cargo_volume == pytest.approx(10)
    assert r.solver_message == "no tanks"


def test_no_cargo():
    r = allocate_cargo_to_tanks([], [Tank("T1", 10)])
    assert r.status == "optimal"
    assert r.total_loaded == 0
    assert r.solver_message == "no cargo"


def test_total_tank_capacity_bottleneck():
    """Cannot load more than sum of tank capacities."""
    r = allocate_cargo_to_tanks(
        [Cargo("A", 1000), Cargo("B", 1000)],
        [Tank("T1", 100), Tank("T2", 100)],
    )
    assert r.status == "optimal"
    assert r.total_loaded == pytest.approx(200)


def test_allocations_respect_per_tank_capacity():
    cargos = [Cargo("A", 50), Cargo("B", 40)]
    tanks = [Tank("T1", 30), Tank("T2", 25), Tank("T3", 100)]
    r = allocate_cargo_to_tanks(cargos, tanks)
    assert r.status == "optimal"
    caps = {t.id: t.capacity for t in tanks}
    used: dict[str, float] = {}
    for a in r.allocations:
        used[a.tank_id] = used.get(a.tank_id, 0) + a.volume
    for tid, vol in used.items():
        assert vol <= caps[tid] + 1e-6


def test_at_most_one_cargo_id_per_tank_in_output():
    r = allocate_cargo_to_tanks(
        [Cargo("X", 100), Cargo("Y", 100), Cargo("Z", 100)],
        [Tank("a", 40), Tank("b", 40), Tank("c", 40), Tank("d", 40)],
    )
    assert r.status == "optimal"
    by_tank: dict[str, set[str]] = {}
    for a in r.allocations:
        by_tank.setdefault(a.tank_id, set()).add(a.cargo_id)
    assert all(len(s) == 1 for s in by_tank.values())


def test_cannot_mix_two_cargos_in_one_tank():
    """One tank may only use one cargo ID; pick the cargo that fills capacity."""
    r = allocate_cargo_to_tanks(
        [Cargo("A", 20), Cargo("B", 20)],
        [Tank("T1", 15)],
    )
    assert r.status == "optimal"
    assert r.total_loaded == pytest.approx(15)
    assert len(r.allocations) == 1
    assert r.allocations[0].cargo_id in ("A", "B")


def test_sample_assignment_numbers():
    """Sanity check on scales similar to the brief."""
    cargos = [
        Cargo("C1", 1234),
        Cargo("C2", 4352),
        Cargo("C3", 3321),
        Cargo("C4", 2456),
        Cargo("C5", 5123),
        Cargo("C6", 1879),
        Cargo("C7", 4987),
        Cargo("C8", 2050),
        Cargo("C9", 3678),
        Cargo("C10", 5432),
    ]
    tanks = [
        Tank("C1", 1234),
        Tank("C2", 4352),
        Tank("C3", 3321),
        Tank("C4", 2456),
        Tank("C5", 5123),
        Tank("C6", 1879),
        Tank("C7", 4987),
        Tank("C8", 2050),
        Tank("C9", 3678),
        Tank("C10", 5432),
    ]
    r = allocate_cargo_to_tanks(cargos, tanks)
    assert r.status == "optimal"
    assert r.total_loaded == pytest.approx(sum(c.volume for c in cargos))
    per_tank: dict[str, list[str]] = {}
    for a in r.allocations:
        per_tank.setdefault(a.tank_id, []).append(a.cargo_id)
    for ids in per_tank.values():
        assert len(set(ids)) == 1
