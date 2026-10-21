from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, HTTPException
from pydantic.main import BaseModel

from db.utils import ConnectToDB

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterModel(BaseModel):
    name: str
    email: str
    password: str


def encrypt_password(password):
    """NOTE: currently dummy hashing before we learn how to do it proper"""
    return password


@router.post("/register", status_code=201)
async def post_register_user(register: RegisterModel):
    encrypted = encrypt_password(register.password)
    async with ConnectToDB() as conn:
        try:
            user = await conn.fetchrow(
                "INSERT INTO users (name, email, password) VALUES ($1, $2, $3) RETURNING *",
                register.name,
                register.email,
                encrypted,
            )
        except UniqueViolationError:
            raise HTTPException(409)

    if user is None:
        raise HTTPException(500)

    user = dict(user)
    return { 'user': {
            'id': user['user_id'],
            'name': user['name'],
            'email': user['email'],
            'created_at': user['created_at']
        }
    }
