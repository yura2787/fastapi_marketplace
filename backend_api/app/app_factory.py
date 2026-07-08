import sentry_sdk
from applications.auth.router import router_auth
from applications.orders.router import router_orders
from applications.payment.router import router_payment
from applications.products.router import cart_router, categories_router, products_router
from applications.reviews.router import reviews_router
from applications.users.router import router_users
from applications.ws.router import ws_router
from fastapi import FastAPI
from settings import settings

sentry_sdk.init(
    dsn=settings.SENTRY,
    send_default_pii=False,
)


def get_application() -> FastAPI:
    app = FastAPI(root_path="/api", root_path_in_servers=True, debug=settings.DEBUG)
    app.include_router(router_users, prefix="/users", tags=["Users"])
    app.include_router(router_auth, prefix="/auth", tags=["Auth"])
    app.include_router(categories_router, prefix="/categories", tags=["Categories"])
    app.include_router(products_router, prefix="/products", tags=["Products"])
    app.include_router(cart_router, prefix="/carts", tags=["Cart"])
    app.include_router(router_orders, prefix="/orders", tags=["Orders"])
    app.include_router(reviews_router, prefix="/reviews", tags=["Reviews"])
    app.include_router(router_payment, prefix="/payment", tags=["Payment"])
    app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
    return app
