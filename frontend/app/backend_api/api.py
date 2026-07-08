import httpx
from fastapi import Request
from settings import settings

BACKEND = settings.BACKEND_API


async def _get(url: str, params: dict = None, token: str = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, headers=headers)
        return r.json() if r.status_code < 400 else {}


async def _post(url: str, data: dict = None, json: dict = None, token: str = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.post(url, data=data, json=json, headers=headers)
        return r.json()


async def login_user(user_email: str, password: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BACKEND}auth/login", data={"username": user_email, "password": password})
        return r.json()


async def register_user(user_email: str, password: str, name: str) -> dict:
    return await _post(f"{BACKEND}users/create", json={"name": name, "password": password, "email": user_email})


async def get_user_info(access_token: str) -> dict:
    return await _get(f"{BACKEND}auth/get-my-info", token=access_token)


async def get_current_user_with_token(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        return {}
    user = await get_user_info(token)
    if user.get("email"):
        user["access_token"] = token
    return user


async def get_products(
    q: str = "",
    page: int = 1,
    category_id: int = None,
    min_price: float = None,
    max_price: float = None,
    in_stock: bool = None,
) -> dict:
    params = {"q": q, "page": page, "limit": 12}
    if category_id:
        params["category_id"] = category_id
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if in_stock is not None:
        params["in_stock"] = in_stock
    result = await _get(f"{BACKEND}products/", params=params)
    return result if result else {"items": [], "total": 0, "page": 1, "pages": 1}


async def get_product(pk: int) -> dict:
    return await _get(f"{BACKEND}products/{pk}")


async def get_categories() -> list:
    result = await _get(f"{BACKEND}categories/")
    return result if isinstance(result, list) else []


async def get_cart(access_token: str) -> dict:
    return await _get(f"{BACKEND}carts/", token=access_token)


async def update_cart(access_token: str, product_id: int, quantity: float) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{BACKEND}carts/change-products",
            params={"product_id": product_id, "quantity": quantity},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return r.json()


async def get_product_reviews(product_id: int) -> dict:
    result = await _get(f"{BACKEND}reviews/product/{product_id}")
    return result if isinstance(result, dict) else {"reviews": [], "avg_rating": 0.0, "total": 0}


async def get_checkout_url(access_token: str) -> dict:
    return await _get(f"{BACKEND}payment/payment-stripe-data", token=access_token)


async def submit_review(product_id: int, rating: int, comment: str | None, access_token: str) -> tuple[int, dict]:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BACKEND}reviews/product/{product_id}",
            json={"rating": rating, "comment": comment},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        try:
            body = r.json()
        except Exception:
            body = {"detail": "Помилка сервера"}
        return r.status_code, body
