"""Initial BIMVORA schema

Revision ID: 001
Revises: 
Create Date: 2026-08-30
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("discipline", sa.String(50), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("image_url", sa.Text),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("seo_title", sa.String(255)),
        sa.Column("seo_desc", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("sku", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_description", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("discipline", sa.String(50), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("compare_at_price_cents", sa.Integer),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("revit_versions", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("lod", sa.String(20), nullable=False, server_default="lod_300"),
        sa.Column("file_formats", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("has_connectors", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("has_shared_params", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_parametric", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("manufacturer", sa.String(255)),
        sa.Column("model_number", sa.String(100)),
        sa.Column("specifications", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("seo_title", sa.String(255)),
        sa.Column("seo_description", sa.Text),
        sa.Column("total_sales", sa.Integer, nullable=False, server_default="0"),
        sa.Column("average_rating", sa.Numeric(3, 2)),
        sa.Column("review_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_products_slug", "products", ["slug"], unique=True)
    op.create_index("ix_products_discipline", "products", ["discipline"])
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_category", "products", ["category_id"])

    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("alt_text", sa.String(255)),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_thumbnail", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_product_images_product", "product_images", ["product_id"])

    op.create_table(
        "product_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("revit_version", sa.String(20)),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "bundles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("compare_at_price_cents", sa.Integer),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("badge", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "bundle_products",
        sa.Column("bundle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bundles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100)),
        sa.Column("company", sa.String(255)),
        sa.Column("customer_type", sa.String(20), nullable=False, server_default="individual"),
        sa.Column("country", sa.String(2)),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("stripe_customer_id", sa.String(100), unique=True),
        sa.Column("total_spent_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("order_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_customers_email", "customers", ["email"], unique=True)

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_number", sa.String(50), nullable=False, unique=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("customer_first_name", sa.String(100), nullable=False),
        sa.Column("customer_last_name", sa.String(100)),
        sa.Column("customer_company", sa.String(255)),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("subtotal_cents", sa.Integer, nullable=False),
        sa.Column("discount_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("coupon_code", sa.String(50)),
        sa.Column("stripe_payment_intent_id", sa.String(200), unique=True),
        sa.Column("stripe_session_id", sa.String(200)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("event_id", sa.String(100)),
        sa.Column("fbclid", sa.String(200)),
        sa.Column("gclid", sa.String(200)),
        sa.Column("fbc", sa.String(500)),
        sa.Column("fbp", sa.String(200)),
        sa.Column("ttp", sa.String(200)),
        sa.Column("ga_client_id", sa.String(100)),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("user_agent", sa.Text),
        sa.Column("sheets_synced", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("email_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("downloads_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_orders_email", "orders", ["customer_email"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created", "orders", ["created_at"])

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("bundle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bundles.id", ondelete="SET NULL")),
        sa.Column("item_type", sa.String(20), nullable=False, server_default="product"),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(100)),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer, nullable=False),
        sa.Column("total_price_cents", sa.Integer, nullable=False),
    )
    op.create_index("ix_order_items_order", "order_items", ["order_id"])

    op.create_table(
        "download_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("token", sa.String(100), nullable=False, unique=True),
        sa.Column("download_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_downloads", sa.Integer, nullable=False, server_default="10"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_download_tokens_token", "download_tokens", ["token"], unique=True)

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="SET NULL")),
        sa.Column("rating", sa.SmallInteger, nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("body", sa.Text),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cross_sells",
        sa.Column("source_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("target_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "coupons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("discount_type", sa.String(10), nullable=False),
        sa.Column("discount_value", sa.Integer, nullable=False),
        sa.Column("max_uses", sa.Integer),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("minimum_order_cents", sa.Integer),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "newsletter_subscribers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("source", sa.String(50)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed initial categories
    op.execute("""
        INSERT INTO categories (id, slug, name, description, discipline, sort_order, is_active)
        VALUES 
          (gen_random_uuid(), 'hvac-revit-families', 'HVAC Revit Families', 
           'Professional HVAC equipment families — chillers, FCUs, AHUs, fans, diffusers and more.', 
           'hvac', 1, true),
          (gen_random_uuid(), 'plumbing-revit-families', 'Plumbing Revit Families', 
           'Complete plumbing system families — fixtures, pipes, drainage, water heaters and more.', 
           'plumbing', 2, true),
          (gen_random_uuid(), 'clean-room-revit-families', 'Clean Room Revit Families', 
           'Pharmaceutical and cleanroom families — HEPA filters, FFUs, LAF units, air showers.', 
           'clean_room', 3, true)
    """)


def downgrade() -> None:
    op.drop_table("newsletter_subscribers")
    op.drop_table("coupons")
    op.drop_table("cross_sells")
    op.drop_table("reviews")
    op.drop_table("download_tokens")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("bundle_products")
    op.drop_table("bundles")
    op.drop_table("product_files")
    op.drop_table("product_images")
    op.drop_table("products")
    op.drop_table("categories")
