from applications.auth.security import get_current_user
from applications.reviews.crud import (
    create_review,
    delete_review,
    get_avg_rating,
    get_product_reviews,
    get_review_by_id,
    get_user_review,
)
from applications.reviews.schemas import ProductReviewsResponse, ReviewCreateSchema, ReviewSchema
from applications.users.models import User
from database.session import get_async_session
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

reviews_router = APIRouter()


@reviews_router.get("/product/{product_id}", response_model=ProductReviewsResponse)
async def list_reviews(product_id: int, session: AsyncSession = Depends(get_async_session)):
    reviews = await get_product_reviews(product_id, session)
    avg = await get_avg_rating(product_id, session)
    return {"reviews": reviews, "avg_rating": avg, "total": len(reviews)}


@reviews_router.post("/product/{product_id}", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def add_review(
    product_id: int,
    data: ReviewCreateSchema,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    existing = await get_user_review(user.id, product_id, session)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already reviewed this product")
    return await create_review(user.id, product_id, data.rating, data.comment, session)


@reviews_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_review(
    review_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    review = await get_review_by_id(review_id, session)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your review")
    await delete_review(review, session)
