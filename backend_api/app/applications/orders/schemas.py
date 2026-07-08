from datetime import datetime

from pydantic import BaseModel


class OrderItemSchema(BaseModel):
    product_id: int
    title: str
    price: float
    quantity: float
    total: float

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    id: int
    status: str
    total: float
    created_at: datetime
    items: list[OrderItemSchema]

    class Config:
        from_attributes = True
