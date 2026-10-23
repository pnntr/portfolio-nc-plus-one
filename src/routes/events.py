import datetime
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.utils import ConnectToDB
from src.routes.auth import get_current_user_id

router = APIRouter(prefix="/events", tags=["events"])


def default_404_message(name_of_item: str):
    return {"detail": {"status": f"{name_of_item} NOT FOUND"}}


def default_404_exception(name_of_item: str):
    return HTTPException(404, detail=default_404_message(name_of_item))


class EventsPostRequest(BaseModel):
    title: str
    description: str
    starts_at: datetime.datetime
    ends_at: datetime.datetime
    venue_id: int


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


@router.post("/", status_code=201)
async def post_events(
    user_id: Annotated[int, Depends(get_current_user_id)],
    request_params: EventsPostRequest,
):
    """Post a event as a given user"""
    async with ConnectToDB() as conn:
        event = await conn.fetchrow(
            """INSERT INTO events (title, description, starts_at, ends_at, venue_id, organiser_id)
         VALUES ($1, $2, $3, $4, $5, $6) RETURNING *""",
            request_params.title,
            request_params.description,
            request_params.starts_at,
            request_params.ends_at,
            request_params.venue_id,
            user_id,
        )

    assert event is not None
    event = dict(event)

    event["id"] = event["event_id"]
    del event["event_id"]

    return {"event": event}


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
        raise default_404_exception("Event")

    return {"event": row}


@router.post("/{id}/rsvp", status_code=201)
async def post_rsvp_to_event_id(
    id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Post an rsvp record according to the logged in user id"""

    async with ConnectToDB() as conn:
        already_exists = await conn.fetchrow(
            "SELECT * FROM rsvps WHERE event_id = $1 AND attendee_id = $2",
            user_id,
            id,
        )
        if already_exists is not None:
            raise HTTPException(
                409, detail={"error": {"message": "already RSVP'd to event"}}
            )

        try:
            rsvp = await conn.fetchrow(
                "INSERT INTO rsvps (event_id, attendee_id) VALUES ($1, $2) RETURNING *",
                id,
                user_id,
            )
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise default_404_exception("Event")

    if rsvp is None:
        raise HTTPException(500)

    return {"rsvp": dict(rsvp)}


@router.delete("/{id}/rsvp/me", status_code=204)
async def delete_rsvp_to_event_id(
    id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Delete a rsvp for an event that I (the user) have rsvp'd to"""
    async with ConnectToDB() as conn:
        already_exists = await conn.fetchrow(
            "SELECT * FROM rsvps WHERE event_id = $1 AND attendee_id = $2",
            user_id,
            id,
        )
        if already_exists is None:
            raise default_404_exception("RSVP")

        await conn.execute(
            "DELETE FROM rsvps WHERE event_id = $1 AND attendee_id = $2",
            id,
            user_id,
        )
