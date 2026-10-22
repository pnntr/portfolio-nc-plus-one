import asyncio
import json
from contextlib import asynccontextmanager
from datetime import UTC
from datetime import datetime as dt
from datetime import timezone
from typing import Dict, Tuple

import asyncpg
from dotenv import dotenv_values
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

DATABASE_NAME = dotenv_values(".env")["DATABASE_NAME"]

CREATE_USER_TABLE = """
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
	email VARCHAR(255) UNIQUE NOT NULL,
	password VARCHAR(255) NOT NULL,
	name VARCHAR(255) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

CREATE_VENUES_TABLE = """
DROP TABLE IF EXISTS venues CASCADE;
CREATE TABLE venues (
	venue_id SERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	address TEXT,
	capacity INT
);
"""

CREATE_EVENTS_TABLE = """
DROP TABLE IF EXISTS events CASCADE;
CREATE TABLE events (
	event_id SERIAL PRIMARY KEY,
	title VARCHAR(255) NOT NULL,
	description VARCHAR(255),
	starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
	ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
	organiser_id INT REFERENCES users(user_id),
	venue_id INT REFERENCES venues(venue_id),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

CREATE_RSVPS_TABLE = """
DROP TABLE IF EXISTS rsvps CASCADE;
CREATE TABLE rsvps (
	rsvp_id SERIAL PRIMARY KEY,
	attendee_id INT REFERENCES users(user_id),
	event_id INT REFERENCES events(event_id),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""


class ConnectToDB:
    def __init__(self):
        self.conn: asyncpg.Connection | None = None

    async def __aenter__(self) -> asyncpg.Connection:
        self.conn = await asyncpg.connect(database=DATABASE_NAME)
        assert self.conn is not None
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        assert self.conn is not None
        await self.conn.close()


def from_json(filename: str):
    with open(filename, "r") as f:
        return json.load(f)


def parse_user(row: Dict) -> Tuple[str, str, str] | None:
    return (
        row["name"],
        row["email"],
        pwd_context.hash(row["password"]),
    )


async def seed_users(conn: asyncpg.Connection):
    users = [parse_user(row) for row in from_json("db/data/users.json")]
    await conn.execute(CREATE_USER_TABLE)
    await conn.executemany(
        "INSERT INTO users (name, email, password) VALUES($1, $2, $3)", users
    )


async def seed_venues(conn: asyncpg.Connection):
    venues = [
        (row["name"], row["address"], row["capacity"])
        for row in from_json("db/data/venues.json")
    ]
    await conn.execute(CREATE_VENUES_TABLE)
    await conn.executemany(
        "INSERT INTO venues (name, address, capacity) VALUES($1, $2, $3)", venues
    )


async def seed_events(conn: asyncpg.Connection):
    events = [
        (
            row["title"],
            row["description"],
            dt.fromisoformat(row["starts_at"]),
            dt.fromisoformat(row["ends_at"]),
            row["organiser_id"],
            row["venue_id"],
        )
        for row in from_json("db/data/events.json")
    ]
    await conn.execute(CREATE_EVENTS_TABLE)
    await conn.executemany(
        "INSERT INTO events (title, description, starts_at, ends_at, organiser_id, venue_id) VALUES ($1, $2, $3, $4, $5, $6)",
        events,
    )


async def seed_rsvps(conn: asyncpg.Connection):
    rsvps = [
        (row["attendee_id"], row["event_id"]) for row in from_json("db/data/rsvps.json")
    ]
    await conn.execute(CREATE_RSVPS_TABLE)
    await conn.executemany(
        "INSERT INTO rsvps (attendee_id, event_id) VALUES ($1, $2)", rsvps
    )


async def seed_data():
    async with ConnectToDB() as conn:
        await seed_users(conn)
        await seed_venues(conn)
        await seed_events(conn)
        await seed_rsvps(conn)


if __name__ == "__main__":
    asyncio.run(seed_data())
