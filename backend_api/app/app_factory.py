from fastapi import FastAPI
from applications.auth.router import router_auth
from applications.payment.router import router_payment
from applications.users.router import router_users
from applications.products.router import products_router, cart_router
from settings import settings
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY,
    send_default_pii=True,
)

def get_application() -> FastAPI:
    app = FastAPI(root_path="/api", root_path_in_servers=True, debug=settings.DEBUG)
    app.include_router(router_users, prefix="/users", tags=["Users"])
    app.include_router(router_auth, prefix="/auth", tags=["Auth"])
    app.include_router(products_router, prefix="/products", tags=["Products"])
    app.include_router(cart_router, prefix="/carts", tags=["Cart"])
    app.include_router(router_payment, prefix="/payment", tags=["Payment"])
    return app
