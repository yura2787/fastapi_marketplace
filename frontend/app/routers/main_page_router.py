import asyncio

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend_api.api import (
    get_cart,
    get_categories,
    get_checkout_url,
    get_current_user_with_token,
    get_product,
    get_product_reviews,
    get_products,
    login_user,
    register_user,
    submit_review,
    update_cart,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _price_fmt(value) -> str:
    v = float(value)
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ")


templates.env.filters["price"] = _price_fmt


async def _fetch_base(user: dict) -> tuple[list, dict]:
    token = user.get("access_token")
    if token:
        categories, cart = await asyncio.gather(get_categories(), get_cart(token))
    else:
        categories, cart = await get_categories(), {}
    return categories, cart


def _base_ctx(request: Request, user: dict, categories: list, cart: dict) -> dict:
    cart_count = sum(int(p["quantity"]) for p in cart.get("cart_products", []) if p.get("quantity", 0) > 0)
    ctx = {"request": request, "categories": categories, "cart_count": cart_count}
    if user.get("name"):
        ctx["user"] = user
    return ctx


@router.get("/")
@router.post("/")
async def index(
    request: Request,
    query: str = Form(""),
    user: dict = Depends(get_current_user_with_token),
):
    q = request.query_params.get("q", query)
    page = int(request.query_params.get("page", 1))
    category_id = request.query_params.get("category_id")
    min_price = request.query_params.get("min_price")
    max_price = request.query_params.get("max_price")
    in_stock = request.query_params.get("in_stock")

    (data, (categories, cart)) = await asyncio.gather(
        get_products(
            q=q,
            page=page,
            category_id=int(category_id) if category_id else None,
            min_price=float(min_price) if min_price else None,
            max_price=float(max_price) if max_price else None,
            in_stock=True if in_stock == "true" else None,
        ),
        _fetch_base(user),
    )

    ctx = _base_ctx(request, user, categories, cart)
    ctx.update(
        {
            "products": data.get("items", []),
            "total": data.get("total", 0),
            "page": data.get("page", 1),
            "pages": data.get("pages", 1),
        }
    )
    return templates.TemplateResponse("index.html", ctx)


@router.get("/product/{product_id}")
async def product_detail(
    request: Request,
    product_id: int,
    user: dict = Depends(get_current_user_with_token),
):
    (product, reviews_data, (categories, cart)) = await asyncio.gather(
        get_product(product_id),
        get_product_reviews(product_id),
        _fetch_base(user),
    )
    ctx = _base_ctx(request, user, categories, cart)
    ctx.update({"product": product, "reviews_data": reviews_data})
    return templates.TemplateResponse("product_detail.html", ctx)


@router.get("/cart")
async def cart_page(request: Request, user: dict = Depends(get_current_user_with_token)):
    if not user.get("access_token"):
        return RedirectResponse(request.url_for("login"), status_code=status.HTTP_303_SEE_OTHER)
    categories, cart = await _fetch_base(user)
    ctx = _base_ctx(request, user, categories, cart)
    ctx["cart"] = cart
    return templates.TemplateResponse("cart.html", ctx)


@router.post("/review/{product_id}")
async def post_review(
    product_id: int,
    request: Request,
    user: dict = Depends(get_current_user_with_token),
):
    if not user.get("access_token"):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    body = await request.json()
    status_code, result = await submit_review(
        product_id=product_id,
        rating=body.get("rating"),
        comment=body.get("comment"),
        access_token=user["access_token"],
    )
    return JSONResponse(result, status_code=status_code)


@router.get("/checkout")
async def checkout_redirect(request: Request, user: dict = Depends(get_current_user_with_token)):
    if not user.get("access_token"):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    result = await get_checkout_url(user["access_token"])
    return JSONResponse(result)


@router.post("/cart/update")
async def cart_update(
    request: Request,
    product_id: int = Form(...),
    quantity: float = Form(...),
    user: dict = Depends(get_current_user_with_token),
):
    if not user.get("access_token"):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    result = await update_cart(user["access_token"], product_id, quantity)
    return JSONResponse(result)


@router.get("/login")
@router.post("/login")
async def login(
    request: Request,
    user: dict = Depends(get_current_user_with_token),
    user_email: str = Form(""),
    password: str = Form(""),
):
    if user.get("name"):
        return RedirectResponse(request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)

    categories = await get_categories()
    ctx = {"request": request, "entered_email": user_email, "categories": categories, "cart_count": 0}

    if request.method == "GET":
        return templates.TemplateResponse("login.html", ctx)

    tokens = await login_user(user_email, password)
    access_token = tokens.get("access_token")
    if not access_token:
        ctx["errors"] = ["Невірний email або пароль"]
        return templates.TemplateResponse("login.html", ctx)

    response = RedirectResponse(request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=False, max_age=60 * 50)
    return response


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(request.url_for("login"), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@router.get("/register")
@router.post("/register")
async def register(
    request: Request,
    user: dict = Depends(get_current_user_with_token),
    user_email: str = Form(""),
    password: str = Form(""),
    user_name: str = Form(""),
):
    if user.get("name"):
        return RedirectResponse(request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)

    categories = await get_categories()
    ctx = {
        "request": request,
        "entered_email": user_email,
        "entered_name": user_name,
        "categories": categories,
        "cart_count": 0,
    }

    if request.method == "GET":
        return templates.TemplateResponse("register.html", ctx)

    created = await register_user(user_email=user_email, password=password, name=user_name)
    if created.get("email"):
        tokens = await login_user(user_email, password)
        access_token = tokens.get("access_token")
        response = RedirectResponse(request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=access_token, httponly=False, max_age=60 * 50)
        return response

    ctx["errors"] = [created.get("detail", "Помилка реєстрації")]
    return templates.TemplateResponse("register.html", ctx)
