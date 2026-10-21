import pytest
from fastapi.testclient import TestClient

from db.utils import ConnectToDB
from main import app


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
