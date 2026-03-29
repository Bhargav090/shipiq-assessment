import json

import pytest

from shipiq.api.app import create_app
from shipiq.config import Settings


@pytest.fixture()
def client():
    app = create_app(Settings(log_level="INFO", api_key=None))
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def client_with_api_key():
    app = create_app(Settings(log_level="INFO", api_key="test-secret-key"))
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_optimize_flow(client):
    payload = {
        "cargos": [{"id": "A", "volume": 150}],
        "tanks": [{"id": "T1", "capacity": 100}, {"id": "T2", "capacity": 100}],
    }
    r1 = client.post("/input", data=json.dumps(payload), content_type="application/json")
    assert r1.status_code == 202

    r2 = client.post("/optimize")
    assert r2.status_code == 200
    data = r2.get_json()
    assert data["total_loaded"] == pytest.approx(150)

    r3 = client.get("/results")
    assert r3.status_code == 200
    assert r3.get_json()["total_loaded"] == pytest.approx(150)


def test_results_404_without_optimize(client):
    client.post(
        "/input",
        data=json.dumps(
            {
                "cargos": [{"id": "A", "volume": 1}],
                "tanks": [{"id": "T1", "capacity": 1}],
            }
        ),
        content_type="application/json",
    )
    rv = client.get("/results")
    assert rv.status_code == 404


def test_optimize_409_without_input(client):
    rv = client.post("/optimize")
    assert rv.status_code == 409


def test_health(client):
    rv = client.get("/health")
    assert rv.status_code == 200
    assert rv.get_json() == {"status": "ok"}


def test_input_invalid_json_object(client):
    rv = client.post("/input", data="not-json", content_type="application/json")
    assert rv.status_code == 400


def test_input_validation_error(client):
    rv = client.post(
        "/input",
        data=json.dumps({"cargos": [], "tanks": "bad"}),
        content_type="application/json",
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert body["error"]["code"] == "invalid_payload"


def test_input_duplicate_cargo_id(client):
    rv = client.post(
        "/input",
        data=json.dumps(
            {
                "cargos": [
                    {"id": "A", "volume": 1},
                    {"id": "A", "volume": 2},
                ],
                "tanks": [{"id": "T1", "capacity": 10}],
            }
        ),
        content_type="application/json",
    )
    assert rv.status_code == 400


def test_new_input_clears_previous_results(client):
    client.post(
        "/input",
        data=json.dumps(
            {
                "cargos": [{"id": "A", "volume": 10}],
                "tanks": [{"id": "T1", "capacity": 10}],
            }
        ),
        content_type="application/json",
    )
    client.post("/optimize")
    assert client.get("/results").status_code == 200

    client.post(
        "/input",
        data=json.dumps(
            {
                "cargos": [{"id": "B", "volume": 5}],
                "tanks": [{"id": "T2", "capacity": 5}],
            }
        ),
        content_type="application/json",
    )
    assert client.get("/results").status_code == 404


def test_api_key_required_on_protected_routes(client_with_api_key):
    payload = json.dumps(
        {"cargos": [{"id": "A", "volume": 1}], "tanks": [{"id": "T1", "capacity": 1}]}
    )
    assert client_with_api_key.post(
        "/input", data=payload, content_type="application/json"
    ).status_code == 401

    assert (
        client_with_api_key.post(
            "/input",
            data=payload,
            content_type="application/json",
            headers={"X-API-Key": "test-secret-key"},
        ).status_code
        == 202
    )

    assert client_with_api_key.get("/health").status_code == 200
