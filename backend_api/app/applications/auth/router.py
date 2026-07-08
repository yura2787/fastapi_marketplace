from applications.auth.auth_handler import auth_handler
from applications.auth.security import get_current_user
from applications.users.models import User
from applications.users.schemas import BaseUserInfo
from database.session import get_async_session
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router_auth = APIRouter()


class RefreshRequest(BaseModel):
    refresh_token: str


@router_auth.post("/login")
async def user_login(
    data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    token_pair = await auth_handler.get_login_token_pairs(data, session)
    return token_pair


@router_auth.post("/refresh")
async def refresh_token(data: RefreshRequest):
    return await auth_handler.refresh_access_token(data.refresh_token)


@router_auth.get("/get-my-info")
async def get_my_info(user: User = Depends(get_current_user)) -> BaseUserInfo:
    return user
