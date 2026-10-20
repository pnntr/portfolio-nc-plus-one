from fastapi import APIRouter

from db.utils import ConnectToDB

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def get_events():
    async with ConnectToDB() as conn:
        rows = await conn.fetch("""
        SELECT e.event_id, e.title, e.starts_at, e.ends_at, v.name FROM events as e
            LEFT JOIN venues as v ON e.venue_id = v.venue_id
        """)
    return {
        "events": [
            {
                "id": row[0],
                "title": row[1],
                "starts_at": row[2],
                "ends_at": row[3],
                "location": row[4],
            }
            for row in rows
        ]
    }
