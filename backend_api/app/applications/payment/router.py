import stripe
from applications.auth.security import get_current_user
from applications.products.crud import get_or_create_cart
from applications.products.schemas import CartSchema
from applications.users.models import User
from database.session import get_async_session
from fastapi import APIRouter, Depends
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
        metadata={"user_id": user.id, "total": response.cost, "cart_id": cart.id},
    )
    return {"url": session_stripe["url"]}
