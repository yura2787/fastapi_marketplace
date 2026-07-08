import uuid
from typing import Annotated, Optional

from applications.auth.security import admin_required, get_current_user
from applications.products.crud import (
    create_category,
    create_product_in_db,
    delete_category,
    delete_product,
    get_all_categories,
    get_category_by_id,
    get_category_by_slug,
    get_or_create_cart,
    get_or_create_cart_product,
    get_product_by_pk,
    get_products_data,
)
from applications.products.schemas import (
    CartSchema,
    CategoryCreateSchema,
    CategorySchema,
    ProductListResponse,
    ProductSchema,
    SearchParamsSchema,
)
from applications.users.models import User
from database.session import get_async_session
from fastapi import APIRouter, Body, Depends, Form, HTTPException, UploadFile, status
from services.redis.redis_client import cache_get, cache_invalidate_prefix, cache_set, get_redis, make_cache_key
from services.s3.s3 import s3_storage
from sqlalchemy.ext.asyncio import AsyncSession

products_router = APIRouter()
cart_router = APIRouter()
categories_router = APIRouter()


@cart_router.get("/")
async def get_current_cart(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> CartSchema:
    cart = await get_or_create_cart(user_id=user.id, session=session)

    response = CartSchema.from_orm(cart)
    response = response.filter_zero_quantity_products()
    return response


@cart_router.patch("/change-products")
async def change_products(
    quantity: float,
    product_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> CartSchema:
    cart = await get_or_create_cart(user_id=user.id, session=session)
    product = await get_product_by_pk(product_id, session)
    if not product:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No product")

    cart_product = await get_or_create_cart_product(product_id, cart.id, session)
    cart_product.quantity += quantity
    if cart_product.quantity < 0:
        cart_product.quantity = 0

    cart_product.price = product.price

    session.add(cart_product)
    await session.commit()

    cart = await get_or_create_cart(user_id=user.id, session=session)
    return cart


@categories_router.get("/", response_model=list[CategorySchema])
async def list_categories(session: AsyncSession = Depends(get_async_session)):
    return await get_all_categories(session)


@categories_router.post("/", response_model=CategorySchema, dependencies=[Depends(admin_required)])
async def add_category(data: CategoryCreateSchema, session: AsyncSession = Depends(get_async_session)):
    existing = await get_category_by_slug(data.slug, session)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category with this slug already exists")
    return await create_category(data, session)


@categories_router.delete("/{pk}", dependencies=[Depends(admin_required)], status_code=204)
async def remove_category(pk: int, session: AsyncSession = Depends(get_async_session)):
    category = await get_category_by_id(pk, session)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category #{pk} not found")
    await delete_category(category, session)


@products_router.post("/", dependencies=[Depends(admin_required)])
async def create_product(
    main_image: UploadFile,
    images: list[UploadFile] = None,
    title: str = Body(max_length=100),
    description: str = Body(max_length=1000),
    price: float = Body(gt=1),
    stock: int = Body(default=0, ge=0),
    category_id: Optional[int] = Form(default=None),
    session: AsyncSession = Depends(get_async_session),
) -> ProductSchema:
    product_uuid = uuid.uuid4()
    main_image = await s3_storage.upload_product_image(main_image, product_uuid=product_uuid)
    images = images or []
    images_urls = []
    for image in images:
        url = await s3_storage.upload_product_image(image, product_uuid=product_uuid)
        images_urls.append(url)

    create_product = await create_product_in_db(
        product_uuid=product_uuid,
        title=title,
        description=description,
        price=price,
        main_image=main_image,
        images=images_urls,
        stock=stock,
        category_id=category_id,
        session=session,
    )
    redis = await get_redis()
    await cache_invalidate_prefix(redis, "products_list")
    return create_product


@products_router.delete("/{pk}", dependencies=[Depends(admin_required)], status_code=204)
async def remove_product(
    pk: int,
    session: AsyncSession = Depends(get_async_session),
):
    product = await get_product_by_pk(pk, session)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product #{pk} not found")
    await delete_product(product, session)
    redis = await get_redis()
    await cache_invalidate_prefix(redis, "products_list")


@products_router.get("/{pk}")
async def get_product(
    pk: int,
    session: AsyncSession = Depends(get_async_session),
) -> ProductSchema:
    product = await get_product_by_pk(pk, session)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with pk #{pk} not found")
    return product


@products_router.get("/", response_model=ProductListResponse)
async def get_products(
    params: Annotated[SearchParamsSchema, Depends()], session: AsyncSession = Depends(get_async_session)
):
    redis = await get_redis()
    cache_key = make_cache_key("products_list", params.model_dump())
    cached = await cache_get(redis, cache_key)
    if cached:
        return ProductListResponse.model_validate_json(cached)

    result = await get_products_data(params, session)
    response = ProductListResponse.model_validate(result)
    await cache_set(redis, cache_key, response.model_dump_json(), ttl=60)
    return response
