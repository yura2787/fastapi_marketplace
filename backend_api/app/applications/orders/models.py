from datetime import datetime
from enum import StrEnum

from database.base_model import Base
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class ModelCommonMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class Order(ModelCommonMixin, Base):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cart_id: Mapped[int | None] = mapped_column(ForeignKey("carts.id"), nullable=True)
    total: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.PENDING)
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    items = relationship("OrderItem", back_populates="order", lazy="selectin")


class OrderItem(ModelCommonMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    title: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(default=0.0)
    quantity: Mapped[float] = mapped_column(default=0.0)

    order = relationship("Order", back_populates="items", lazy="selectin")

    @property
    def total(self) -> float:
        return self.price * self.quantity
