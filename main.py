import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Form, Depends
from fastapi.responses import RedirectResponse
from starlette import status

import setting
from setting import BASE_DIR, conn_str, per_page, DB_PATH
from DataBase import users
from DataBase import products as pd
from fastapi import Query
from contextlib import contextmanager


app = FastAPI()

# монтируем /static → папка static/ в корне проекта
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# указываем Jinja2Templates, папка templates/ в корне проекта
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@contextmanager
def get_db():
    conn = sqlite3.connect(setting.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.get("/home", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Главная страница
    """
    return templates.TemplateResponse(
        "home1.html",
        {"request": request,}
    )


@app.get("/products", response_class=HTMLResponse)
async def products(request: Request):
    """
    Список товаров
    """
    return templates.TemplateResponse(
        "products.html",
        {"request": request}
    )


@app.get("/categories", response_class=HTMLResponse)
async def categories(request: Request):
    """
    Категории
    """
    return templates.TemplateResponse(
        "categories.html",
        {"request": request}
    )


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """
    Личный кабинет
    """
    return templates.TemplateResponse(
        "profile.html",
        {"request": request}
    )


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """
    Форма входа
    """
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

# Тестовые данные с id
list_users = users.list_users(conn_str)


product_header = pd.products_table_info(conn_str)

list_product = pd.list_products(conn_str)

@app.get("/admin", response_class=HTMLResponse, name="admin")
async def admin(
    request: Request,
    tab: str = "users",
    login_search: str = Query("", alias="login_search"),
    page: int = Query(1, ge=1)
):
    # перехватываем удаление до формирования страницы
    action = request.query_params.get("action")
    delete_id = request.query_params.get("id")

    if tab == "users" and action == "delete_user" and delete_id:
        with sqlite3.connect(DB_PATH) as conn:
            ok = users.delete_user(conn, delete_id)

        # редиректим обратно на /admin без action/id, сохранив фильтры/страницу
        url = request.url_for("admin").include_query_params(
            tab="users",
            page=page,
            login_search=login_search
        )
        # можете прокинуть флаг результата, если нужно отобразить сообщение
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # дальше — ваш текущий код построения страницы
    per_page = 10
    paged_users = []
    list_product_page = []

    if tab == "users":
        all_users = users.list_users(conn_str)  # оставил как у вас
        if login_search:
            filtered_users = [
                u for u in all_users
                if login_search.lower() in u.login.lower()
                or login_search.lower() in u.last_name.lower()
            ]
        else:
            filtered_users = all_users

        total_count = len(filtered_users)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1
        start = (page - 1) * per_page
        end = start + per_page
        paged_users = filtered_users[start:end]

    elif tab == "products":
        total_count = len(list_product)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1
        start = (page - 1) * per_page
        end = start + per_page
        list_product_page = list_product[start:end]
    else:
        total_pages = 1

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "active_tab": tab,
            "list_users": paged_users,
            "users_header": users.users_table_info(conn_str),
            "product_header": product_header,
            "list_product": list_product_page if tab == "products" else [],
            "login_search": login_search,
            "page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            # можете вывести сообщение об ошибке, если передан error=...
            "error": request.query_params.get("error", "")
        }
    )


@app.get("/admin/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    prod = next(p for p in list_product if p["id"] == product_id)
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "product": prod,
    })


@app.get("/admin/users/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: int):
    # найдите нужного пользователя
    user = next(u for u in list_users if u["id"] == user_id)
    return templates.TemplateResponse("profile_edit.html", {
        "request": request,
        "user": user,
    })

@app.get(
    "/profile/edit/{user_id}",
    response_class=HTMLResponse,
    name="profile_edit_form"
)
async def profile_edit_form(request: Request, user_id: str):
    """
    Показать форму редактирования профиля пользователя.
    user_id — строка, например 'us0', 'abc123' и т.п.
    """
    with get_db() as conn:
        user = users.get_user(conn, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        fields = users.users_table_info(conn)

    return templates.TemplateResponse(
        "profile_edit.html",
        {
            "request": request,
            "user": user,
            "fields": fields,
        },
    )


@app.post("/profile/edit/{user_id}", name="profile_edit_save")
async def profile_edit_save(request: Request, user_id: str):
    form = await request.form()

    with get_db() as conn:
        user = users.get_user(conn, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # обновляем поля из формы
        user.first_name = form.get("first_name")
        user.last_name = form.get("last_name")
        user.middle_name = form.get("middle_name")
        user.birthdate = form.get("birthdate")
        user.phone = form.get("phone")
        user.email = form.get("email")
        user.login = form.get("login")
        user.vip = bool(form.get("vip"))

        # пароли и фото трогать не будем
        users.update_user(conn, user)

    return RedirectResponse(
        url=request.url_for("profile_view", user_id=user_id),
        status_code=status.HTTP_303_SEE_OTHER,
    )

@app.get("/profile/{user_id}", response_class=HTMLResponse)
async def profile_view(request: Request, user_id: str):

    with sqlite3.connect(DB_PATH) as conn:
        u = users.get_user(conn, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user_dict = {}
    for key, value in vars(u).items():
        user_dict[key] = value

    return templates.TemplateResponse("profile_view.html", {"request": request, "user": user_dict})
