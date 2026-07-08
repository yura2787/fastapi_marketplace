import uuid
from datetime import datetime

from database.base_model import Base
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class ModelCommonMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class Product(ModelCommonMixin, Base):
    __tablename__ = "products"

    uuid_data: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)

    title: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), index=True, default="")
    price: Mapped[float] = mapped_column(nullable=False)
    main_image: Mapped[str] = mapped_column(nullable=False)
    images: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    cart_products = relationship(
        "CartProduct",
        back_populates="product",
        lazy="selectin",
    )

    def __str__(self):
        return f"Product {self.title} - {self.id}"


class Cart(ModelCommonMixin, Base):
    __tablename__ = "carts"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_closed: Mapped[bool] = mapped_column(default=False)

    cart_products = relationship(
        "CartProduct",
        back_populates="cart",
        lazy="selectin",
    )

    @property
    def cost(self):
        return sum([cart_product.total for cart_product in self.cart_products])


class CartProduct(ModelCommonMixin, Base):
    __tablename__ = "cart_products"

    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    price: Mapped[float] = mapped_column(default=0.0)
    quantity: Mapped[float] = mapped_column(default=0.0)

    cart = relationship(
        "Cart",
        back_populates="cart_products",
        lazy="selectin",
    )
    product = relationship(
        "Product",
        back_populates="cart_products",
        lazy="selectin",
    )

    @property
    def total(self) -> float:
        return self.price * self.quantity
