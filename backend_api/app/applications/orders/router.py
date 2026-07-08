from applications.auth.security import get_current_user
from applications.orders.crud import get_order_by_id, get_user_orders
from applications.orders.schemas import OrderSchema
from applications.users.models import User
from database.session import get_async_session
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router_orders = APIRouter()


@router_orders.get("/", response_model=list[OrderSchema])
async def list_orders(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await get_user_orders(user.id, session)


@router_orders.get("/{order_id}", response_model=OrderSchema)
async def order_detail(
    order_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    order = await get_order_by_id(order_id, user.id, session)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
