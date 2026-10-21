from fastapi import APIRouter, HTTPException

from db.utils import ConnectToDB

router = APIRouter(prefix="/events", tags=["events"])


def default_404_message(name_of_item: str):
    return {"detail": {"status": f"{name_of_item} NOT FOUND"}}


@router.get("/")
async def get_events():
    """Get all events from the database

    Gets the event name, start, end times and location name NOT just id.
    Events are returned in event ID order, which is roughly by which event
    was created first.
    """

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


@router.get("/{id}")
async def get_event_id(id: int):
    """Get event by id if that event id exists in database"""

    async with ConnectToDB() as conn:
        row = await conn.fetchrow(
            """
        SELECT e.event_id as id, e.title, e.description, e.starts_at, e.ends_at, v.name as location, v.address, v.capacity, e.created_at FROM events as e
            LEFT JOIN venues as v ON e.venue_id = v.venue_id
            WHERE e.event_id = $1
        """,
            id,
        )
    if row is None:
        raise HTTPException(404, default_404_message("Event"))

    return {"event": row}
