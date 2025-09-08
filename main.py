import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from DataBase.users import get_user_by_login
from setting import BASE_DIR, conn_str, per_page
from DataBase import users
from fastapi import Query


app = FastAPI()

# монтируем /static → папка static/ в корне проекта
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# указываем Jinja2Templates, папка templates/ в корне проекта
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


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


product_header = [
    "Товар", "Категория", "Цена", "Остаток", "Статус", "Добавлен"
]

list_product = [
    {
      "id": 1,
      "Товар": "Whey Protein", "Категория": "Протеин", "Цена": "1500 ₽",
      "Остаток": 20, "Статус": "В наличии", "Добавлен": "2024-01-15"
    },
    {
      "id": 2,
      "Товар": "Vitamin C", "Категория": "Витамины", "Цена": "800 ₽",
      "Остаток": 0, "Статус": "Нет в наличии", "Добавлен": "2024-02-01"
    },
]

users_header = users.users_table_info(conn_str)
@app.get("/admin", response_class=HTMLResponse, name="admin")
async def admin(
    request: Request,
    tab: str = "users",
    login_search: str = Query("", alias="login_search"),
    page: int = Query(1, ge=1)
):
    per_page = 10
    paged_users = []
    list_product_page = []

    if tab == "users":
        all_users = users.list_users(conn_str)

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
            "users_header": users_header,
            "product_header": product_header,
            "list_product": list_product_page if tab == "products" else [],
            "login_search": login_search,
            "page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
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
    return templates.TemplateResponse("user_detail.html", {
        "request": request,
        "user": user,
    })
