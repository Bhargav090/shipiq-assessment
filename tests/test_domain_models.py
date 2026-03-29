import pytest

from shipiq.domain.models import Cargo, Tank


def test_cargo_rejects_negative_volume():
    with pytest.raises(ValueError, match="negative"):
        Cargo("C1", -1)


def test_cargo_rejects_blank_id():
    with pytest.raises(ValueError, match="non-empty"):
        Cargo("  ", 10)


def test_tank_rejects_negative_capacity():
    with pytest.raises(ValueError, match="negative"):
        Tank("T1", -0.01)


def test_tank_rejects_blank_id():
    with pytest.raises(ValueError, match="non-empty"):
        Tank("", 100)
