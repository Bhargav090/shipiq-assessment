import pytest

from shipiq.api.errors import ApiError
from shipiq.api.validation import parse_cargos_tanks


def test_rejects_non_object_body():
    with pytest.raises(ApiError) as exc:
        parse_cargos_tanks(None)
    assert exc.value.code == "invalid_payload"


def test_rejects_missing_arrays():
    with pytest.raises(ApiError) as exc:
        parse_cargos_tanks({"cargos": []})
    assert "arrays" in exc.value.message


def test_rejects_zero_volume():
    with pytest.raises(ApiError) as exc:
        parse_cargos_tanks(
            {
                "cargos": [{"id": "A", "volume": 0}],
                "tanks": [{"id": "T1", "capacity": 1}],
            }
        )
    assert exc.value.code == "invalid_payload"


def test_rejects_duplicate_cargo_ids():
    with pytest.raises(ApiError) as exc:
        parse_cargos_tanks(
            {
                "cargos": [
                    {"id": "A", "volume": 1},
                    {"id": "A", "volume": 2},
                ],
                "tanks": [{"id": "T1", "capacity": 10}],
            }
        )
    assert "duplicate" in exc.value.message


def test_rejects_duplicate_tank_ids():
    with pytest.raises(ApiError) as exc:
        parse_cargos_tanks(
            {
                "cargos": [{"id": "A", "volume": 10}],
                "tanks": [
                    {"id": "T1", "capacity": 5},
                    {"id": "T1", "capacity": 5},
                ],
            }
        )
    assert "duplicate" in exc.value.message


def test_accepts_integer_like_numbers():
    cargos, tanks = parse_cargos_tanks(
        {
            "cargos": [{"id": "A", "volume": 100}],
            "tanks": [{"id": "T1", "capacity": 50}],
        }
    )
    assert cargos[0].volume == 100.0
    assert tanks[0].capacity == 50.0
