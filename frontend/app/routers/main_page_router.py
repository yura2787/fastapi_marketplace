from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from backend_api.api import get_current_user_with_token, login_user, register_user, get_products, get_product


router = APIRouter()


templates = Jinja2Templates(directory='templates')



@router.get('/')
@router.post('/')
async def index(request: Request, query: str = Form(''), user: dict = Depends(get_current_user_with_token)):
    products = await get_products(query)
    context = {
        'request': request,
        "products": products['items']
    }
    if user.get('name'):
        context['user'] = user
    response = templates.TemplateResponse('index.html', context=context)
    return response


@router.get('/product/{product_id}')
async def product_detail(request: Request, product_id: int, user: dict = Depends(get_current_user_with_token)):
    product = await get_product(product_id)
    context = {
        'request': request,
        "product": product,
    }
    if user.get('name'):
        context['user'] = user
    response = templates.TemplateResponse('product_detail.html', context=context)
    return response


@router.get('/login')
@router.post('/login')
async def login(request: Request, user: dict = Depends(get_current_user_with_token), user_email: str = Form(''),
                password: str = Form('')):
    context = {'request': request, "entered_email": user_email}
    redirect_url = request.url_for("index")
    if user.get('name'):
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return response


    if request.method == "GET":
        response = templates.TemplateResponse('login.html', context=context)
        response.delete_cookie('access_token')
        return response

    user_tokens = await login_user(user_email, password)
    access_token = user_tokens.get('access_token')
    if not access_token:
        errors = ["Incorrect login or password"]
        context['errors'] = errors
        return templates.TemplateResponse('login.html', context=context)
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=60 * 5)
    return response



@router.get('/logout')
async def logout(request: Request):
    redirect_url = request.url_for("login")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('access_token')
    return response



@router.get('/register')
@router.post('/register')
async def register(
        request: Request,
        user: dict = Depends(get_current_user_with_token),
        user_email: str = Form(''),
        password: str = Form(''),
        user_name: str = Form(''),
):
    context = {'request': request, "entered_email": user_email, 'entered_name': user_name}
    redirect_url = request.url_for("index")
    if user.get('name'):
        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return response

    if request.method == "GET":
        response = templates.TemplateResponse('register.html', context=context)
        response.delete_cookie('access_token')
        return response



    created_user = await register_user(user_email=user_email, password=password, name=user_name)
    if created_user.get('email'):
        user_tokens = await login_user(user_email, password)
        access_token = user_tokens.get('access_token')

        response = RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=60*5)
        return response

    context['errors'] = [created_user['detail']]
    response = templates.TemplateResponse('register.html', context=context)
    return response


