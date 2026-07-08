import json

import stripe
from applications.auth.security import get_current_user
from applications.orders.crud import create_order_from_cart, get_order_by_stripe_session, mark_order_paid
from applications.orders.models import OrderStatus
from applications.products.crud import get_or_create_cart
from applications.products.schemas import CartSchema
from applications.users.models import User
from database.session import get_async_session
from fastapi import APIRouter, Depends, HTTPException, Request, status
from settings import settings
from sqlalchemy.ext.asyncio import AsyncSession

stripe.api_key = settings.STRIPE_SECRET_KEY

router_payment = APIRouter()


@router_payment.get("/payment-stripe-data")
async def payment_stripe_data(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    cart = await get_or_create_cart(user_id=user.id, session=session)
    response = CartSchema.from_orm(cart)
    response = response.filter_zero_quantity_products()

    if not response.cart_products:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    line_items: list[dict] = [
        {
            "price_data": {
                "currency": "uah",
                "product_data": {
                    "name": cart_product.product.title,
                    "description": cart_product.product.description,
                    "images": [cart_product.product.main_image] + cart_product.product.images,
                },
                "unit_amount": round(cart_product.price * 100),
            },
            "quantity": int(cart_product.quantity),
        }
        for cart_product in response.cart_products
    ]

    session_stripe = stripe.checkout.Session.create(
        line_items=line_items,
        mode="payment",
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        customer_email=user.email,
        metadata={"user_id": user.id, "cart_id": cart.id},
    )

    order = await create_order_from_cart(user.id, cart, session, stripe_session_id=session_stripe["id"])
    return {"url": session_stripe["url"], "order_id": order.id}


@router_payment.post("/webhook")
async def stripe_webhook(request: Request, session: AsyncSession = Depends(get_async_session)):
    payload = await request.body()

    if settings.STRIPE_WEBHOOK_SECRET:
        signature = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")
    else:
        event = json.loads(payload)

    if event["type"] == "checkout.session.completed":
        stripe_session = event["data"]["object"]
        order = await get_order_by_stripe_session(stripe_session["id"], session)
        if order is not None and order.status != OrderStatus.PAID:
            await mark_order_paid(order, session)

    return {"status": "ok"}
