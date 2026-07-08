"""catalog: categories + product stock and category_id

Revision ID: c8d2b3e4f5a6
Revises: b7c1a2d3e4f5
Create Date: 2025-07-08 13:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8d2b3e4f5a6"
down_revision: Union[str, None] = "b7c1a2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=True)

    op.add_column("products", sa.Column("stock", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("products", sa.Column("category_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_products_category_id", "products", "categories", ["category_id"], ["id"])
    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_constraint("fk_products_category_id", "products", type_="foreignkey")
    op.drop_column("products", "category_id")
    op.drop_column("products", "stock")
    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_table("categories")
