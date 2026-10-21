import pytest
from fastapi.testclient import TestClient

from db.utils import ConnectToDB
from main import app
from src.routes.events import default_404_message


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_events_successfully_returns_all_events(client):
    res = client.get("/events/")
    assert res.status_code == 200

    data = res.json()
    assert "events" in data
    assert len(data["events"]) == 10


@pytest.mark.asyncio
async def test_get_events_first_event_location_is_named(client):
    res = client.get("/events/")
    assert res.status_code == 200

    data = res.json()
    assert "events" in data
    assert data["events"][0]["location"] == "Nexus, University of Leeds"


@pytest.mark.asyncio
async def test_get_events_id_success_on_found_id(client):
    res = client.get("/events/2")
    assert res.status_code == 200

    data = res.json()

    # NOTE: don't compare created at since every reseed will have a
    # different created at timestamp
    assert "created_at" in data["event"]
    del data["event"]["created_at"]

    sample_event = {
        "event": {
            "id": 2,
            "title": "Intro to Machine Learning Workshop",
            "description": "Hands-on workshop covering perceptrons, neural networks, and classifiers using NumPy and PyTorch.",
            "starts_at": "2026-06-25T09:00:00+00:00",
            "ends_at": "2026-06-25T12:00:00+00:00",
            "location": "Online – Zoom",
            "address": None,
            "capacity": 500,
        }
    }

    assert data == sample_event


@pytest.mark.asyncio
async def test_get_events_id_non_int_id(client):
    res = client.get("/events/hi")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_get_events_id_where_id_not_found(client):
    res = client.get("/events/-1")
    assert res.status_code == 404
    data = res.json()
    assert data == {"error": default_404_message("Event")}
