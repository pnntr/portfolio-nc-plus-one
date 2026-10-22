import pytest

from db.utils import ConnectToDB, pwd_context, seed_data


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
        assert user is not None
        user = dict(user)
        del user["created_at"]
        del user["user_id"]

    password = user["password"]
    assert pwd_context.verify(USER["password"], password)

    del user["password"]
    del USER["password"]
    assert USER == user
