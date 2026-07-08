from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewAuthorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ReviewSchema(BaseModel):
    id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    user: ReviewAuthorSchema

    class Config:
        from_attributes = True


class ReviewCreateSchema(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ProductReviewsResponse(BaseModel):
    reviews: list[ReviewSchema]
    avg_rating: float
    total: int
