import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    discipline: str


class ProductImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    url: str
    alt_text: str | None
    sort_order: int
    is_thumbnail: bool


class ProductFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    file_name: str
    file_type: str
    file_size: int | None
    revit_version: str | None
    version: str


class ProductBrief(BaseModel):
    """Used in lists, cards, cross-sells."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    sku: str
    name: str
    short_description: str
    discipline: str
    price_cents: int
    compare_at_price_cents: int | None
    currency: str
    revit_versions: list[str]
    lod: str
    has_connectors: bool
    has_shared_params: bool
    is_parametric: bool
    average_rating: float | None
    review_count: int
    total_sales: int
    thumbnail_url: str | None = None
    category: CategoryBrief | None


class ProductDetail(ProductBrief):
    """Full product page data."""
    description: str | None
    file_formats: list[str]
    manufacturer: str | None
    model_number: str | None
    specifications: dict
    seo_title: str | None
    seo_description: str | None
    images: list[ProductImageRead]
    files: list[ProductFileRead]
    cross_sells: list[ProductBrief] = []
    created_at: datetime
    updated_at: datetime


class ProductList(BaseModel):
    items: list[ProductBrief]
    total: int
    page: int
    per_page: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.per_page - 1) // self.per_page)


class ProductCreate(BaseModel):
    slug: str
    sku: str
    name: str
    short_description: str
    description: str | None = None
    status: str = "draft"
    discipline: str
    category_id: uuid.UUID | None = None
    price_cents: int
    compare_at_price_cents: int | None = None
    currency: str = "USD"
    revit_versions: list[str] = []
    lod: str = "lod_300"
    file_formats: list[str] = [".rfa"]
    has_connectors: bool = True
    has_shared_params: bool = True
    is_parametric: bool = True
    manufacturer: str | None = None
    specifications: dict = {}
    seo_title: str | None = None
    seo_description: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    short_description: str | None = None
    description: str | None = None
    status: str | None = None
    price_cents: int | None = None
    compare_at_price_cents: int | None = None
    revit_versions: list[str] | None = None
    specifications: dict | None = None
    seo_title: str | None = None
    seo_description: str | None = None
