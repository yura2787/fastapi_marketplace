from enum import StrEnum

from pydantic import BaseModel, Field
from typing import Annotated, Optional

class ProductSchema(BaseModel):
    id: int
    title: str
    description: str
    price: float
    main_image: str
    images: list[str]


    class Config:
        from_attributes = True

class CartProductSchema(BaseModel):
    price: float
    quantity: float
    total: float
    product: ProductSchema


    class Config:
        from_attributes = True

class CartSchema(BaseModel):
    is_closed: bool
    user_id: int
    cost: float
    cart_products: list[CartProductSchema]


    class Config:
        from_attributes = True

    def filter_zero_quantity_products(self):
        self.cart_products = [product for product in self.cart_products if product.quantity > 0]
        return self



class SortEnum(StrEnum):
    ASC = 'asc'
    DESC = 'desc'


class SortByEnum(StrEnum):
    ID = 'id'
    PRICE = 'price'


class SearchParamsSchema(BaseModel):
    q: Annotated[Optional[str], Field(default=None)] = None
    page: Annotated[int, Field(default=1, ge=1)]
    limit: Annotated[int, Field(default=10, ge=1, le=50)]
    order_direction: SortEnum = SortEnum.DESC
    sort_by: SortByEnum = SortByEnum.ID
    use_sharp_q_filter: bool = Field(default=False, description='used to search exact q')