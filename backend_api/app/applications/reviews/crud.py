from applications.reviews.models import Review
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_product_reviews(product_id: int, session: AsyncSession) -> list[Review]:
    result = await session.execute(select(Review).filter(Review.product_id == product_id).order_by(Review.id.desc()))
    return result.scalars().all()


async def get_avg_rating(product_id: int, session: AsyncSession) -> float:
    result = await session.execute(select(func.avg(Review.rating)).filter(Review.product_id == product_id))
    avg = result.scalar()
    return round(float(avg), 1) if avg else 0.0


async def get_user_review(user_id: int, product_id: int, session: AsyncSession) -> Review | None:
    result = await session.execute(select(Review).filter(Review.user_id == user_id, Review.product_id == product_id))
    return result.scalar_one_or_none()


async def get_review_by_id(review_id: int, session: AsyncSession) -> Review | None:
    result = await session.execute(select(Review).filter(Review.id == review_id))
    return result.scalar_one_or_none()


async def create_review(
    user_id: int, product_id: int, rating: int, comment: str | None, session: AsyncSession
) -> Review:
    review = Review(user_id=user_id, product_id=product_id, rating=rating, comment=comment)
    session.add(review)
    await session.commit()
    return review


async def delete_review(review: Review, session: AsyncSession) -> None:
    await session.delete(review)
    await session.commit()
