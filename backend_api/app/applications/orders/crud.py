from applications.orders.models import Order, OrderItem, OrderStatus
from applications.products.models import Cart
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_order_from_cart(
    user_id: int, cart: Cart, session: AsyncSession, stripe_session_id: str | None = None
) -> Order:
    order = Order(
        user_id=user_id,
        cart_id=cart.id,
        total=cart.cost,
        status=OrderStatus.PENDING,
        stripe_session_id=stripe_session_id,
    )
    session.add(order)
    await session.flush()

    for cart_product in cart.cart_products:
        if cart_product.quantity <= 0:
            continue
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=cart_product.product_id,
                title=cart_product.product.title,
                price=cart_product.price,
                quantity=cart_product.quantity,
            )
        )

    await session.commit()
    await session.refresh(order)
    return order


async def get_user_orders(user_id: int, session: AsyncSession) -> list[Order]:
    query = select(Order).where(Order.user_id == user_id).order_by(Order.id.desc())
    result = await session.execute(query)
    return result.scalars().all()


async def get_order_by_id(order_id: int, user_id: int, session: AsyncSession) -> Order | None:
    query = select(Order).where(Order.id == order_id, Order.user_id == user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_order_by_stripe_session(stripe_session_id: str, session: AsyncSession) -> Order | None:
    query = select(Order).where(Order.stripe_session_id == stripe_session_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def mark_order_paid(order: Order, session: AsyncSession) -> None:
    order.status = OrderStatus.PAID
    session.add(order)

    if order.cart_id is not None:
        cart = await session.get(Cart, order.cart_id)
        if cart is not None:
            cart.is_closed = True
            session.add(cart)

    await session.commit()
