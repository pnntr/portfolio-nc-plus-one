import pytest
import pytest_asyncio
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security.oauth2 import OAuth2PasswordRequestFormStrict
from fastapi.testclient import TestClient

from db.utils import ConnectToDB, pwd_context
from main import app

DUMMY_USER = {"name": "dummydummy", "email": "dummy@gmail.com", "password": "password"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def clean_dummy_user():
    async with ConnectToDB() as conn:
        await conn.execute("DELETE from users WHERE email = $1", DUMMY_USER["email"])


@pytest.mark.asyncio
async def test_post_register_user_201(client):
    user = client.post("/auth/register", json=DUMMY_USER)
    assert user.status_code == 201
    assert "user" in user.json()

    user = user.json()["user"]
    assert "id" in user
    assert "created_at" in user
    assert user["name"] == DUMMY_USER["name"]
    assert user["email"] == DUMMY_USER["email"]
    assert "password" not in user


@pytest.mark.asyncio
async def test_post_register_user_email_already_exists(client):
    user = client.post("/auth/register", json=DUMMY_USER)
    assert user.status_code == 201

    user = client.post("/auth/register", json=DUMMY_USER)
    assert user.status_code == 409


@pytest.mark.asyncio
async def test_post_register_user_missing_field(client):
    dummy = DUMMY_USER.copy()
    del dummy["email"]
    user = client.post("/auth/register", json=dummy)
    assert user.status_code == 400

# FIX: for some reason it doesn't like raw json
@pytest.mark.asyncio
async def test_post_login_200(client):
    user = client.post("/auth/register", json=DUMMY_USER)
    assert user.status_code == 201

    form = {"username": DUMMY_USER["email"], "password": DUMMY_USER["password"]}
    token = client.post("/auth/login", json=form)
    assert token.status_code == 200
    assert "token" in token.json()
