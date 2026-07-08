import math

from applications.products.models import Cart, CartProduct, Product
from applications.products.schemas import SearchParamsSchema, SortByEnum, SortEnum
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_product_in_db(product_uuid, title, description, price, main_image, images, session) -> Product:
    """
        uuid_data: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)

    title: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), index=True, default="")
    price: Mapped[float] = mapped_column(nullable=False)
    main_image: Mapped[str] = mapped_column(nullable=False)
    images: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    """
    new_product = Product(
        uuid_data=product_uuid,
        title=title.strip(),
        description=description.strip(),
        price=price,
        main_image=main_image,
        images=images,
    )
    session.add(new_product)

    await session.commit()
    return new_product


async def get_products_data(params: SearchParamsSchema, session: AsyncSession):
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    order_direction = asc if params.order_direction == SortEnum.ASC else desc
    if params.q:
        search_fields = [Product.title, Product.description]
        if params.use_sharp_q_filter:
            cleaned_query = params.q.strip().lower()
            search_condition = [func.lower(search_field) == cleaned_query for search_field in search_fields]
            query = query.filter(or_(*search_condition))
            count_query = count_query.filter(or_(*search_condition))
        else:
            words = [word for word in params.q.strip().split() if len(word) > 1]
            search_condition = or_(
                and_(*(search_field.icontains(word) for word in words)) for search_field in search_fields
            )
            query = query.filter(search_condition)
            count_query = count_query.filter(search_condition)

    sort_field = Product.price if params.sort_by == SortByEnum.PRICE else Product.id
    query = query.order_by(order_direction(sort_field))
    offset = (params.page - 1) * params.limit
    query = query.offset(offset).limit(params.limit)

    result = await session.execute(query)
    result_count = await session.execute(count_query)
    total = result_count.scalar()

    return {
        "items": result.scalars().all(),
        "total": total,
        "page": params.page,
        "limit": params.limit,
        "pages": math.ceil(total / params.limit),
    }


async def get_product_by_pk(pk: int, session: AsyncSession) -> Product | None:
    query = select(Product).filter(Product.id == pk)
    # query = select(Product).filter_by(id = pk)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_or_create_cart(user_id: int, session: AsyncSession) -> Cart:
    query = select(Cart).filter_by(user_id=user_id, is_closed=False)
    result = await session.execute(query)
    cart = result.scalar_one_or_none()

    if cart:
        return cart

    cart = Cart(user_id=user_id, is_closed=False)
    session.add(cart)
    await session.commit()
    return cart


async def get_or_create_cart_product(product_id: int, cart_id: int, session: AsyncSession) -> CartProduct:
    query = select(CartProduct).filter_by(cart_id=cart_id, product_id=product_id)
    result = await session.execute(query)
    cart_product = result.scalar_one_or_none()

    if cart_product:
        return cart_product

    cart_product = CartProduct(cart_id=cart_id, product_id=product_id)
    session.add(cart_product)
    await session.commit()
    return cart_product
