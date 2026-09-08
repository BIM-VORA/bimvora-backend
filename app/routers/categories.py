from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import uuid

from app.database import get_db
from app.models.category import Category
from app.models.product import Product

router = APIRouter()


class CategoryChild(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    name: str
    discipline: str
    product_count: int = 0


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    discipline: str
    image_url: str | None
    product_count: int = 0
    children: list[CategoryChild] = []


@router.get("/", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .where(Category.is_active == True, Category.parent_id == None)
        .options(selectinload(Category.children))
        .order_by(Category.sort_order)
    )
    categories = result.scalars().all()

    out = []
    for cat in categories:
        count_result = await db.execute(
            select(func.count()).where(Product.category_id == cat.id, Product.status == "active")
        )
        cat_count = count_result.scalar_one()

        children = []
        for child in cat.children:
            child_count_result = await db.execute(
                select(func.count()).where(Product.category_id == child.id, Product.status == "active")
            )
            child_count = child_count_result.scalar_one()
            child_data = CategoryChild.model_validate(child)
            child_data.product_count = child_count
            children.append(child_data)

        cat_data = CategoryRead.model_validate(cat)
        cat_data.product_count = cat_count
        cat_data.children = children
        out.append(cat_data)

    return out


@router.get("/{slug}", response_model=CategoryRead)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .where(Category.slug == slug, Category.is_active == True)
        .options(selectinload(Category.children))
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    count_result = await db.execute(
        select(func.count()).where(Product.category_id == category.id, Product.status == "active")
    )
    cat_data = CategoryRead.model_validate(category)
    cat_data.product_count = count_result.scalar_one()
    return cat_data
