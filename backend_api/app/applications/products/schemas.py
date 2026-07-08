from enum import StrEnum
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class CategorySchema(BaseModel):
    id: int
    name: str
    slug: str
    description: str

    class Config:
        from_attributes = True


class CategoryCreateSchema(BaseModel):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=120, pattern=r"^[a-z0-9-]+$")
    description: str = Field(default="", max_length=500)


class ProductSchema(BaseModel):
    id: int
    title: str
    description: str
    price: float
    main_image: str
    images: list[str]
    stock: int
    category: Optional[CategorySchema] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: list[ProductSchema]
    total: int
    page: int
    limit: int
    pages: int


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
    ASC = "asc"
    DESC = "desc"


class SortByEnum(StrEnum):
    ID = "id"
    PRICE = "price"


class SearchParamsSchema(BaseModel):
    q: Annotated[Optional[str], Field(default=None)] = None
    page: Annotated[int, Field(default=1, ge=1)]
    limit: Annotated[int, Field(default=10, ge=1, le=50)]
    order_direction: SortEnum = SortEnum.DESC
    sort_by: SortByEnum = SortByEnum.ID
    use_sharp_q_filter: bool = Field(default=False, description="used to search exact q")
    category_id: Optional[int] = Field(default=None)
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)
    in_stock: Optional[bool] = Field(default=None)
