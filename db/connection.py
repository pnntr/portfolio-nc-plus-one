from contextlib import asynccontextmanager

import asyncpg
from dotenv import dotenv_values

DATABASE_NAME = dotenv_values(".env")["DATABASE_NAME"]


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
