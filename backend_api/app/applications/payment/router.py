from sqlalchemy.ext.asyncio import AsyncSession

import settings
from applications.users.crud import create_user_in_db, get_user_by_email, activate_user_account
from applications.users.schemas import BaseUserInfo, RegisterUserFields
from services.rabbit.constants import SupportedQueues
from services.rabbit.rabbitmq_service import rabbitmq_broker
from typing import Annotated

from fastapi import APIRouter, Body, UploadFile, Depends, HTTPException, status
import uuid

from applications.auth.security import admin_required, get_current_user
from applications.products.crud import create_product_in_db, get_products_data, get_product_by_pk, get_or_create_cart, get_or_create_cart_product
from applications.products.schemas import ProductSchema, SearchParamsSchema, CartSchema
from applications.users.models import User
from services.s3.s3 import s3_storage
from sqlalchemy.ext.asyncio import AsyncSession

from applications.users.crud import create_user_in_db, get_user_by_email, activate_user_account
from applications.users.schemas import BaseUserInfo, RegisterUserFields
from database.session_dependenscise import get_async_session
import stripe

stripe.api_key = settings.settings.STRIPE_SECRET_KEY

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
                    'images': [cart_product.product.main_image] + cart_product.product.images
                },
                "unit_amount": int(cart_product.price) * 100,

            },
            "quantity": int(cart_product.quantity)

        }
        for cart_product in response.cart_products
    ]

    session_stripe = stripe.checkout.Session.create(
        line_items=line_items,
        mode="payment",
        success_url='https://c4bc-188-130-177-189.ngrok-free.app',
        cancel_url='https://c4bc-188-130-177-189.ngrok-free.app/api',
        customer_email=user.email,
        # locale='fr',
        metadata={"user_id": user.id, 'total': response.cost, 'cart_id': cart.id}
    )
    print(session_stripe)
    return {"url": session_stripe['url']}
