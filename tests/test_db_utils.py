import pytest

from db.utils import ConnectToDB, seed_data


@pytest.mark.asyncio
async def test_seed_works():
    fresh_data = await seed_data()
    assert fresh_data == None


@pytest.mark.asyncio
async def test_first_row_of_users_is_correct():
    USER = {
        "name": "Alice Rahman",
        "email": "alice@example.com",
        "password": "password123",
    }

    fresh_data = await seed_data()
    async with ConnectToDB() as conn:
        user = await conn.fetchrow("SELECT * FROM users;")
        user = dict(user)
        del user["created_at"]
        del user["user_id"]

    assert USER == user
