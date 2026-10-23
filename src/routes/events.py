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


async def raise_error_if_start_after_end_time(
    start: datetime.datetime | None, end: datetime.datetime | None, event_id: int | None
):
    start_before_end_exception = HTTPException(
        400,
        detail={
            "error": {
                "status": "Bad input",
                "message": "Start time cannot be before end time",
            }
        },
    )

    if start is None and end is None:
        return

    if start is not None and end is not None:
        if start > end:
            raise start_before_end_exception
        return

    # NOTE: if creating an event don't go down this
    assert event_id is not None

    if start is None:
        async with ConnectToDB() as conn:
            start = await conn.fetchrow(
                "SELECT starts_at FROM events WHERE event_id = $1",
                event_id,
            )
    else:
        async with ConnectToDB() as conn:
            end = await conn.fetchrow(
                "SELECT ends_at FROM events WHERE event_id = $1",
                event_id,
            )

    assert start is not None and end is not None
    if start > end:
        raise start_before_end_exception


class EventsPostRequest(BaseModel):
    title: str
    description: str
    starts_at: datetime.datetime
    ends_at: datetime.datetime
    venue_id: int


class EventPatchRequest(BaseModel):
    description: str | None = None
    starts_at: datetime.datetime | None = None
    ends_at: datetime.datetime | None = None


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

    await raise_error_if_start_after_end_time(
        request_params.starts_at,
        request_params.ends_at,
        None,
    )

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


@router.patch("/{id}", status_code=200)
async def patch_event_id(
    id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    request_params: EventPatchRequest,
):
    await raise_error_if_start_after_end_time(
        request_params.starts_at,
        request_params.ends_at,
        id,
    )

    async with ConnectToDB() as conn:
        found_event = await conn.fetchrow(
            "SELECT * FROM events WHERE event_id = $1", id
        )
        if found_event is None:
            raise default_404_exception("Event")
        is_organiser = await conn.fetchrow(
            "SELECT * FROM events WHERE event_id = $1 AND organiser_id = $2",
            id,
            user_id,
        )
        if is_organiser is None:
            raise HTTPException(403)

        # NOTE: doing update in a transaction so that a user update is
        # either applied or aborted but not partially applied
        async with conn.transaction():
            if request_params.description is not None:
                await conn.execute(
                    "UPDATE events SET description = $1 WHERE event_id = $2",
                    request_params.description,
                    id,
                )
            if request_params.starts_at is not None:
                await conn.execute(
                    "UPDATE events SET starts_at = $1 WHERE event_id = $2",
                    request_params.starts_at,
                    id,
                )
            if request_params.ends_at is not None:
                await conn.execute(
                    "UPDATE events SET starts_at = $1 WHERE event_id = $2",
                    request_params.starts_at,
                    id,
                )

        new_event = await conn.fetchrow("SELECT * FROM events WHERE event_id = $1", id)

    assert new_event is not None
    new_event = dict(new_event)

    new_event["id"] = new_event["event_id"]
    del new_event["event_id"]

    return {"event": new_event}


@router.get("/{id}/attendees")
async def get_event_id_attendees(
    id: int, user_id: Annotated[int, Depends(get_current_user_id)]
):
    async with ConnectToDB() as conn:
        found_event = await conn.fetchrow("SELECT * FROM rsvps WHERE event_id = $1", id)
        if found_event is None:
            raise default_404_exception("Event")

        is_organiser = await conn.fetchval(
            """SELECT r.event_id FROM rsvps as r JOIN events as e ON r.event_id = e.event_id WHERE e.event_id = $1 AND e.organiser_id = $2""",
            id,
            user_id,
        )
        print(is_organiser, id, user_id)
        if is_organiser is None:
            raise HTTPException(403)

        attendees = await conn.fetch(
            """WITH rsvps_for_event AS (
                    SELECT attendee_id FROM rsvps WHERE event_id = $1
                )
                SELECT user_id as id, name, email
                FROM users
                JOIN rsvps_for_event as r ON user_id = r.attendee_id
            """,
            id,
        )
    return {"attendees": [dict(a) for a in attendees]}


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
