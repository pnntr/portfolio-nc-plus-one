import datetime
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from asyncpg.exceptions import UniqueViolationError
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from db.utils import ConnectToDB, pwd_context

load_dotenv()

SECRET_KEY = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    async with ConnectToDB() as conn:
        fetched_id = await conn.fetchval(
            "SELECT user_id FROM users WHERE user_id = $1",
            int(user_id),
        )

    if fetched_id is None:
        raise credentials_exception

    return fetched_id


@router.post("/register", status_code=201)
async def post_register_user(register: RegisterRequest):
    encrypted = pwd_context.hash(register.password)
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
    return {
        "user": {
            "id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"],
        }
    }


@router.post("/login", response_model=LoginResponse)
async def post_login_user(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    async with ConnectToDB() as conn:
        res = await conn.fetchrow(
            "SELECT password, user_id FROM users WHERE email = $1;",
            form.username,
        )

    if res is None:
        raise HTTPException(
            status_code=401, detail={"error": "email or password incorrect"}
        )

    stored_password, user_id = tuple(res)
    print(tuple(res), stored_password, pwd_context.hash(form.password))

    if not pwd_context.verify(form.password, stored_password):
        raise HTTPException(
            status_code=401, detail={"error": "email or password incorrect"}
        )

    token_data = create_access_token(user_id)
    return LoginResponse(access_token=token_data, token_type="bearer")
