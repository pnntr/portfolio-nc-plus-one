from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db.utils import ConnectToDB
from src.routes.auth import get_current_user_id

router = APIRouter(prefix="/user", tags=["users"])


def default_404_message(name_of_item: str):
    return {"detail": {"status": f"{name_of_item} NOT FOUND"}}


def default_404_exception(name_of_item: str):
    return HTTPException(404, detail=default_404_message(name_of_item))


@router.get("/me/events")
def get_me_events(user_id: Annotated[int, Depends(get_current_user_id)]):
    pass
