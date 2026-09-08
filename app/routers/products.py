from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.product import Product, ProductImage
from app.models.cross_sell import CrossSell
from app.schemas.product import ProductBrief, ProductDetail, ProductList

router = APIRouter()


@router.get("/", response_model=ProductList)
async def list_products(
    db: AsyncSession = Depends(get_db),
    category_slug: str | None = Query(None),
    discipline: str | None = Query(None),
    search: str | None = Query(None),
    revit_version: str | None = Query(None),
    lod: str | None = Query(None),
    sort: str = Query("popular"),  # popular|newest|price_asc|price_desc
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=96),
):
    query = (
        select(Product)
        .where(Product.status == "active")
        .options(selectinload(Product.category), selectinload(Product.images))
    )

    if discipline:
        query = query.where(Product.discipline == discipline)
    if lod:
        query = query.where(Product.lod == lod)
    if search:
        query = query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.short_description.ilike(f"%{search}%"),
            )
        )
    if revit_version:
        query = query.where(Product.revit_versions.any(revit_version))
    if category_slug:
        from app.models.category import Category
        query = query.join(Product.category).where(Category.slug == category_slug)

    # Sorting
    sort_map = {
        "popular": Product.total_sales.desc(),
        "newest": Product.created_at.desc(),
        "price_asc": Product.price_cents.asc(),
        "price_desc": Product.price_cents.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.total_sales.desc()))

    # Count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    products = result.scalars().all()

    items = []
    for p in products:
        thumbnail = next((img.url for img in p.images if img.is_thumbnail), None)
        brief = ProductBrief.model_validate(p)
        brief.thumbnail_url = thumbnail
        items.append(brief)

    return ProductList(items=items, total=total, page=page, per_page=per_page)


@router.get("/{slug}", response_model=ProductDetail)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product)
        .where(Product.slug == slug, Product.status == "active")
        .options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.files),
            selectinload(Product.reviews),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get cross-sells
    cs_result = await db.execute(
        select(Product)
        .join(CrossSell, CrossSell.target_product_id == Product.id)
        .where(CrossSell.source_product_id == product.id, Product.status == "active")
        .options(selectinload(Product.category), selectinload(Product.images))
        .order_by(CrossSell.sort_order)
        .limit(4)
    )
    cross_sell_products = cs_result.scalars().all()

    detail = ProductDetail.model_validate(product)
    thumbnail = next((img.url for img in product.images if img.is_thumbnail), None)
    detail.thumbnail_url = thumbnail
    detail.cross_sells = [ProductBrief.model_validate(p) for p in cross_sell_products]

    return detail
