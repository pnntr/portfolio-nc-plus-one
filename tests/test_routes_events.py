import pytest
from fastapi.testclient import TestClient

from db.utils import ConnectToDB
from main import app
from src.routes.events import default_404_message


@pytest.fixture
def client():
    return TestClient(app)


def login(client: TestClient):
    form = {"username": "alice@example.com", "password": "password123"}
    token = client.post("/auth/login", data=form)
    return token.json()["access_token"], 1


def event(client: TestClient):
    jwt, _ = login(client)
    headers = {"Authorization": f"Bearer {jwt}"}
    event_data = {
        "title": "Summer Rooftop Social",
        "description": "An evening of networking and good vibes.",
        "starts_at": "2025-08-15T18:00:00Z",
        "ends_at": "2025-08-15T21:00:00Z",
        "venue_id": 2,
    }

    return headers, event_data


async def clear_rsvps(attendee_id, event_id):
    async with ConnectToDB() as conn:
        await conn.execute(
            "DELETE FROM rsvps WHERE attendee_id = $1 AND event_id = $2",
            attendee_id,
            event_id,
        )


async def clear_events(event_id):
    async with ConnectToDB() as conn:
        await conn.execute("DELETE FROM events WHERE event_id = $1", event_id)


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
async def test_post_events_201(client):
    headers, event_data = event(client)
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 201

    data = res.json()["event"]

    await clear_events(data["id"])


@pytest.mark.asyncio
async def test_post_events_401_unauthenticated(client):
    headers, event_data = event(client)
    res = client.post("/events", headers={}, json=event_data)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_post_events_400_missing_fields(client):
    headers, event_data = event(client)
    del event_data["title"]
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_post_events_400_wrong_datetime_format(client):
    headers, event_data = event(client)
    # NOTE: added extra 'T's in datetime string to test
    event_data["ends_at"] = "2026-10-23TTT06:08:37+00:00 UTC+00:00"
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 400


# TODO: test if end is after start
@pytest.mark.asyncio
async def test_post_events_400_start_after_end_time(client):
    headers, event_data = event(client)
    # NOTE: added extra 'T's in datetime string to test
    event_data["starts_at"] = "2025-08-15T13:00:00Z"
    event_data["ends_at"] = "2025-08-15T12:00:00Z"
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 400


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


@pytest.mark.asyncio
async def test_patch_event_id_200_all_fields(client):
    headers, event_data = event(client)
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 201

    event_id = res.json()["event"]["id"]
    old_data = res.json()

    update_data = {
        "description": "Updated description, now with live music!",
        "starts_at": "2025-08-16T19:00:00Z",
        "ends_at": "2025-08-16T23:00:00Z",
    }
    res = client.patch(f"/events/{event_id}", headers=headers, json=update_data)
    assert res.status_code == 200
    assert res.json() != old_data

    await clear_events(event_id)


@pytest.mark.asyncio
async def test_patch_event_id_200_some_missing(client):
    headers, event_data = event(client)
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 201

    event_id = res.json()["event"]["id"]
    old_data = res.json()

    update_data = {
        "description": "Updated description, now with live music!",
    }
    res = client.patch(f"/events/{event_id}", headers=headers, json=update_data)
    assert res.status_code == 200
    assert res.json() != old_data

    await clear_events(event_id)


@pytest.mark.asyncio
async def test_patch_event_id_200_all_missing(client):
    headers, event_data = event(client)
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 201

    event_id = res.json()["event"]["id"]
    old_data = res.json()

    update_data = {}
    res = client.patch(f"/events/{event_id}", headers=headers, json=update_data)
    assert res.status_code == 200
    assert res.json() == old_data

    await clear_events(event_id)


@pytest.mark.asyncio
async def test_patch_event_id_404_event_not_found(client):
    headers, _ = event(client)
    event_id = -1

    update_data = {
        "description": "Updated description, now with live music!",
        "starts_at": "2025-08-16T19:00:00Z",
        "ends_at": "2025-08-16T23:00:00Z",
    }
    res = client.patch(f"/events/{event_id}", headers=headers, json=update_data)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_patch_event_id_400_end_before_start_time(client):
    headers, event_data = event(client)
    res = client.post("/events", headers=headers, json=event_data)
    assert res.status_code == 201

    event_id = res.json()["event"]["id"]
    old_data = res.json()

    update_data = {
        "description": "Updated description, now with live music!",
        "starts_at": "2025-08-16T19:00:00Z",
        "ends_at": "2025-08-16T12:00:00Z",
    }
    res = client.patch(f"/events/{event_id}", headers=headers, json=update_data)
    assert res.status_code == 400

    await clear_events(event_id)


@pytest.mark.asyncio
async def test_patch_event_id_403_non_organiser_tries_to_patch(client):
    headers, _ = event(client)
    update_data = {
        "description": "Updated description, now with live music!",
        "starts_at": "2025-08-16T19:00:00Z",
        "ends_at": "2025-08-16T23:00:00Z",
    }
    # NOTE: check seed data to verify that event_id=2
    # is not owned by user_id=1
    res = client.patch(f"/events/{2}", headers=headers, json=update_data)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_event_attendees_200(client):
    jwt, user_id = login(client)
    event_id = 1

    res = client.get(
        f"/events/{event_id}/attendees", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert res.status_code == 200

    attendees = {
        "attendees": [
            {"id": 2, "name": "Bob Nguyen", "email": "bob@example.com"},
            {"id": 3, "name": "Carol Singh", "email": "carol@example.com"},
            {"id": 4, "name": "David Okafor", "email": "david@example.com"},
            {"id": 5, "name": "Eve Martinez", "email": "eve@example.com"},
        ]
    }
    assert res.json() == attendees


@pytest.mark.asyncio
async def test_get_event_attendees_401_no_token(client):
    event_id = 1

    res = client.get(
        f"/events/{event_id}/attendees", headers={"Authorization": f"Bearer updog"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_event_attendees_403_non_organiser_cannot_edit_event(client):
    jwt, user_id = login(client)
    event_id = 2

    res = client.get(
        f"/events/{event_id}/attendees", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_event_attendees_404_event_not_found(client):
    jwt, user_id = login(client)
    event_id = -1

    res = client.get(
        f"/events/{event_id}/attendees", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_post_rsvp_to_event_id_201(client):
    event_id = 1
    jwt, user_id = login(client)
    res = client.post(
        f"/events/{event_id}/rsvp", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert res.status_code == 201

    data = res.json()["rsvp"]
    assert data["attendee_id"] == user_id
    assert data["event_id"] == event_id

    await clear_rsvps(user_id, event_id)


@pytest.mark.asyncio
async def test_post_rsvp_to_event_id_401_missing_token(client):
    event_id = 2
    jwt, user_id = login(client)
    res = client.post(f"/events/{event_id}/rsvp")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_post_rsvp_to_event_id_404_no_event(client):
    event_id = -1
    jwt, user_id = login(client)
    res = client.post(
        f"/events/{event_id}/rsvp", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_post_rsvp_to_event_id_409_already_rsvpd(client):
    event_id = 1
    jwt, user_id = login(client)
    res = client.post(
        f"/events/{event_id}/rsvp", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert res.status_code == 201

    res = client.post(
        f"/events/{event_id}/rsvp", headers={"Authorization": f"Bearer {jwt}"}
    )
    assert res.status_code == 409

    await clear_rsvps(user_id, event_id)


@pytest.mark.asyncio
async def test_delete_rsvp_to_event_id_204(client):
    event_id = 1
    jwt, _ = login(client)
    headers = {"Authorization": f"Bearer {jwt}"}
    res = client.post(f"/events/{event_id}/rsvp", headers=headers)
    assert res.status_code == 201

    res = client.delete(f"/events/{event_id}/rsvp/me", headers=headers)
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_delete_rsvp_to_event_id_invalid_jwt_401(client):
    event_id = 1
    jwt, _ = login(client)
    headers = {"Authorization": f"Bearer updog"}
    res = client.post(f"/events/{event_id}/rsvp", headers=headers)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_delete_rsvp_to_event_id_double_delete_404(client):
    event_id = 1
    jwt, _ = login(client)
    headers = {"Authorization": f"Bearer {jwt}"}
    res = client.post(f"/events/{event_id}/rsvp", headers=headers)
    assert res.status_code == 201

    res = client.delete(f"/events/{event_id}/rsvp/me", headers=headers)
    assert res.status_code == 204

    res = client.delete(f"/events/{event_id}/rsvp/me", headers=headers)
    assert res.status_code == 404
