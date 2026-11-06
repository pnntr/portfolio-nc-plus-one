import pytest
from fastapi.testclient import TestClient

from db.utils import ConnectToDB
from main import app


def login(client: TestClient):
    form = {"username": "alice@example.com", "password": "password123"}
    token = client.post("/auth/login", data=form)
    return token.json()["access_token"], 1


def header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_user_me_events_200(client):
    headers = header(login(client)[0])
    res = client.get("/user/me/events", headers=headers)
    assert res.status_code == 200

    assert res.json() == "data"
