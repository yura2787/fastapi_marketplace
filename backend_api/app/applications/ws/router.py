from applications.auth.auth_handler import auth_handler
from applications.users.crud import get_user_by_email
from database.session import get_async_session
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from services.websocket.manager import ws_manager
from sqlalchemy.ext.asyncio import AsyncSession

ws_router = APIRouter()


@ws_router.websocket("/orders")
async def orders_ws(
    websocket: WebSocket,
    token: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        payload = await auth_handler.decode_token(token)
        user = await get_user_by_email(payload["user_email"], session)
        if not user:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user.id, websocket)
