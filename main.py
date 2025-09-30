import ipaddress
import mimetypes
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from starlette import status
import setting
from setting import *
from DataBase import users, addres
from DataBase import products as pd
from DataBase import orders as ords
from DataBase import authorization as au
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

@app.on_event("startup")
async def on_startup():
    with sqlite3.connect(DB_PATH) as conn:
        pd.init_products_table(conn)
        pd.upgrade_products_add_category(conn)
        pd.upgrade_products_add_weight(conn)

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
        "all_products.html",
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


@app.get("/admin", response_class=HTMLResponse, name="admin")
async def admin(
        request: Request,
        tab: str = "users",
        login_search: str = Query("", alias="login_search"),
        address_search: str = Query("", alias="address_search"),
        order_search: str = Query("", alias="order_search"),
        page: int = Query(1, ge=1)
):
    # перехватываем удаление до формирования страницы
    action = request.query_params.get("action")
    delete_id = request.query_params.get("id")

    # Обработка удаления пользователя
    if tab == "users" and action == "delete_user" and delete_id:
        with sqlite3.connect(DB_PATH) as conn:
            ok = users.delete_user(conn, delete_id)
        url = request.url_for("admin").include_query_params(
            tab="users",
            page=page,
            login_search=login_search
        )
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # Обработка удаления адреса
    elif tab == "addresses" and action == "delete_address" and delete_id:
        with sqlite3.connect(DB_PATH) as conn:
            ok = addres.delete_address(conn, delete_id)
        url = request.url_for("admin").include_query_params(
            tab="addresses",
            page=page,
            address_search=address_search
        )
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # Обработка удаления товара
    elif tab == "products" and action == "delete_product" and delete_id:
        with sqlite3.connect(DB_PATH) as conn:
            ok = pd.delete_product(conn, delete_id)
        url = request.url_for("admin").include_query_params(
            tab="products",
            page=page
        )
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # Обработка удаления заказа
    elif tab == "orders" and action == "delete_order" and delete_id:
        with sqlite3.connect(DB_PATH) as conn:
            ok = ords.delete_order(conn, delete_id)
        url = request.url_for("admin").include_query_params(
            tab="orders",
            page=page,
            order_search=order_search
        )
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # Получаем данные для отображения
    per_page = 10
    paged_users = []
    list_product_page = []
    paged_addresses = []
    paged_orders = []

    if tab == "users":
        with sqlite3.connect(DB_PATH) as conn:
            all_users = users.list_users(conn)
            users_header = users.users_table_info(conn)

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
        with sqlite3.connect(DB_PATH) as conn:
            all_products = pd.list_products(conn)
            product_header = pd.products_table_info(conn)

        total_count = len(all_products)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1
        start = (page - 1) * per_page
        end = start + per_page
        list_product_page = all_products[start:end]

    elif tab == "addresses":
        with sqlite3.connect(DB_PATH) as conn:
            all_addresses = addres.list_addresses(conn)
            addresses_header = addres.address_table_info(conn)

        if address_search:
            filtered_addresses = [
                a for a in all_addresses
                if address_search.lower() in a.country.lower()
                   or address_search.lower() in a.city.lower()
                   or address_search.lower() in a.street.lower()
                   or address_search.lower() in a.user_id.lower()
            ]
        else:
            filtered_addresses = all_addresses

        total_count = len(filtered_addresses)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1
        start = (page - 1) * per_page
        end = start + per_page
        paged_addresses = filtered_addresses[start:end]

    elif tab == "orders":
        with sqlite3.connect(DB_PATH) as conn:
            # Получаем заказы с деталями через новую структуру
            all_orders = ords.orders_with_details(conn)
            orders_header = ords.orders_table_info(conn)
            # Получаем статистику для отображения
            orders_stats = ords.get_orders_statistics(conn)

        if order_search:
            filtered_orders = [
                o for o in all_orders
                if order_search.lower() in o['id'].lower()
                   or order_search.lower() in o.get('product_name', '').lower()
                   or order_search.lower() in o['product_id'].lower()
                   or (o.get('first_name') and order_search.lower() in o['first_name'].lower())
                   or (o.get('last_name') and order_search.lower() in o['last_name'].lower())
                   or (o.get('user_id') and order_search.lower() in o['user_id'].lower())
                   or (o.get('country') and order_search.lower() in o['country'].lower())
                   or (o.get('city') and order_search.lower() in o['city'].lower())
                   or (o.get('street') and order_search.lower() in o['street'].lower())
            ]
        else:
            filtered_orders = all_orders

        total_count = len(filtered_orders)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1
        start = (page - 1) * per_page
        end = start + per_page
        paged_orders = filtered_orders[start:end]

    else:
        total_pages = 1

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "active_tab": tab,
            "list_users": paged_users,
            "users_header": users_header if tab == "users" else [],
            "product_header": product_header if tab == "products" else [],
            "list_product": list_product_page if tab == "products" else [],
            "addresses_header": addresses_header if tab == "addresses" else [],
            "list_addresses": paged_addresses if tab == "addresses" else [],
            "orders_header": orders_header if tab == "orders" else [],
            "list_orders": paged_orders if tab == "orders" else [],
            "login_search": login_search,
            "address_search": address_search,
            "order_search": order_search,
            "page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "error": request.query_params.get("error", "")
        }
    )

@app.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: str):
    prod = next(p for p in  pd.list_products(conn_str) if p.id == product_id)
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "product": prod,
    })


@app.get("/admin/users/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: int):
    # найдите нужного пользователя
    user = next(u for u in users.list_users(conn_str) if u["id"] == user_id)
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

@app.get("/add_user", response_class=HTMLResponse, name="add_user_form")
async def add_user_form(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        fields = users.users_table_info(conn)
    if not fields:
        raise HTTPException(status_code=404, detail="Структура таблицы не найдена")
    return templates.TemplateResponse("add_user.html", {"request": request, "fields": fields})

@app.post("/add_user", name="add_user_submit")
async def add_user_submit(request: Request):
    return await process_add_user(request)

def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def choose_ext(content_type: str) -> str:
    ext = (mimetypes.guess_extension(content_type) or ".jpg").lower()
    if ext in (".jpeg", ".jpe"):
        ext = ".jpg"
    if ext not in (".jpg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    return ext

async def save_image_bytes(blob: bytes, content_type: str) -> str:
    ensure_upload_dir()
    ext = choose_ext(content_type)
    filename = f"{uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(blob)
    return f"/static/img/{filename}"

def is_public_host(host: str) -> bool:
    if not host:
        return False
    if host in {"localhost"}:
        return False
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        # доменное имя — пускаем
        pass
    return True

async def download_image_to_static(url: str) -> str | None:
    url = (url or "").strip()
    pr = urlparse(url)
    if pr.scheme not in ("http", "https") or not is_public_host(pr.hostname or ""):
        return None
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.get(url, headers={"Accept": "image/*"})
        if resp.status_code != 200:
            return None
        ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if ctype not in ALLOWED_MIME:
            return None
        cl = resp.headers.get("content-length")
        if cl and int(cl) > MAX_IMAGE_SIZE:
            return None
        data_bytes = await resp.aread()
        if len(data_bytes) > MAX_IMAGE_SIZE:
            return None
        return await save_image_bytes(data_bytes, ctype)

async def process_add_user(request: Request):
    form = await request.form()
    data = {k: v for k, v in form.items() if not hasattr(v, "filename")}

    vip_value = str(data.get("vip", "")).lower() in ("true", "on", "1")

    local_photo_url = None

    # 1) Приоритет — файл
    photo_file = form.get("photo_file")
    if photo_file and getattr(photo_file, "filename", ""):
        content = await photo_file.read()
        ctype = (photo_file.content_type or "").split(";")[0].strip().lower()
        if content and len(content) <= MAX_IMAGE_SIZE and ctype in ALLOWED_MIME:
            local_photo_url = await save_image_bytes(content, ctype)
        await photo_file.close()
    # 2) Если файл не выбран — пробуем URL
    elif data.get("photo"):
        local_photo_url = await download_image_to_static(data["photo"])

    with sqlite3.connect(DB_PATH) as conn:
        fields = users.users_table_info(conn)

        user_data = {}
        for field in fields:
            if field == "vip":
                user_data[field] = vip_value
            elif field == "photo":
                continue
            else:
                user_data[field] = data.get(field)

        user_obj = users.User(
            id=users.get_next_user_id(conn),
            **user_data,
            password_hash=users.hash_password(data.get("password") or ""),
            photo=local_photo_url or None,  # путь к копии в static/img
        )
        users.create_user(conn, user_obj)

    return RedirectResponse(url="/add_user", status_code=303)

async def process_add_product(request: Request):
    form = await request.form()
    data = {k: v for k, v in form.items() if not hasattr(v, "filename")}

    local_image_url = None

    image_file = form.get("image_file")
    if image_file and getattr(image_file, "filename", ""):
        content = await image_file.read()
        ctype = (image_file.content_type or "").split(";")[0].strip().lower()
        if content and len(content) <= MAX_IMAGE_SIZE and ctype in ALLOWED_MIME:
            local_image_url = await save_image_bytes(content, ctype)
        await image_file.close()
    elif data.get("image"):
        local_image_url = await download_image_to_static(data["image"])

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None
    try:
        price = float(data.get("price") or 0)
    except ValueError:
        price = 0.0
    try:
        stock = int(data.get("stock") or 0)
    except ValueError:
        stock = 0
    try:
        weight = float(data.get("weight") or 0)    # граммы
    except ValueError:
        weight = 0.0
    category = (data.get("category") or "").strip() or None

    if not name:
        raise HTTPException(status_code=400, detail="Название товара обязательно")
    if price < 0 or stock < 0 or weight < 0:
        raise HTTPException(status_code=400, detail="Цена, остаток и вес не могут быть отрицательными")

    with sqlite3.connect(DB_PATH) as conn:
        product = pd.Product(
            id=pd.get_next_product_id(conn),
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=local_image_url or None,
            category=category,
            weight=weight,
        )
        pd.create_product(conn, product)

    url = request.url_for("admin").include_query_params(tab="products")
    return RedirectResponse(url=str(url), status_code=303)


@app.get("/add_product", response_class=HTMLResponse, name="add_product_form")
async def add_product_form(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        # поля для формы (исключает image)
        fields = pd.products_table_info(conn)
    if not fields:
        raise HTTPException(status_code=404, detail="Структура таблицы products не найдена")
    return templates.TemplateResponse("add_product.html", {"request": request, "fields": fields})

@app.post("/add_product", name="add_product_submit")
async def add_product_submit(request: Request):
    return await process_add_product(request)

async def process_edit_product(request: Request, product_id: str):
    form = await request.form()
    data = {k: v for k, v in form.items() if not hasattr(v, "filename")}
    clear_image = bool(form.get("clear_image"))

    with sqlite3.connect(DB_PATH) as conn:
        product = pd.get_product(conn, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        # Текстовые поля
        name = (data.get("name") or product.name).strip()
        description = (data.get("description") or "") or None
        category = (data.get("category") or "") or None

        # Числовые поля
        def to_float(v, default):
            try:
                return float(v)
            except (TypeError, ValueError):
                return default
        def to_int(v, default):
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        price = to_float(data.get("price"), product.price)
        stock = to_int(data.get("stock"), product.stock)
        weight = to_float(data.get("weight"), product.weight)

        if not name:
            raise HTTPException(status_code=400, detail="Название обязательно")
        if price < 0 or stock < 0 or weight < 0:
            raise HTTPException(status_code=400, detail="Цена, остаток и вес не могут быть отрицательными")

        # Обработка изображения: clear -> None; иначе файл > URL > оставить как было
        new_image = product.image
        if clear_image:
            new_image = None
        else:
            image_file = form.get("image_file")
            if image_file and getattr(image_file, "filename", ""):
                content = await image_file.read()
                ctype = (image_file.content_type or "").split(";")[0].strip().lower()
                if content and len(content) <= MAX_IMAGE_SIZE and ctype in ALLOWED_MIME:
                    new_image = await save_image_bytes(content, ctype)
                await image_file.close()
            elif data.get("image"):
                downloaded = await download_image_to_static(data["image"])
                if downloaded:
                    new_image = downloaded

        # Применяем изменения и сохраняем
        product.name = name
        product.description = description
        product.category = category
        product.price = price
        product.stock = stock
        product.weight = weight
        product.image = new_image

        ok = pd.update_product(conn, product)
        if not ok:
            raise HTTPException(status_code=500, detail="Не удалось сохранить изменения")

    return RedirectResponse(
        url=str(request.url_for("product_detail", product_id=product_id)),
        status_code=303
    )

@app.get("/products/{product_id}/edit", response_class=HTMLResponse, name="product_edit_form")
async def product_edit_form(request: Request, product_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        product = pd.get_product(conn, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return templates.TemplateResponse("product_edit.html", {"request": request, "product": product})

@app.post("/products/{product_id}/edit", name="product_edit_submit")
async def product_edit_submit(request: Request, product_id: str):
    return await process_edit_product(request, product_id)

@app.get("/products/{product_id}/delete", response_class=HTMLResponse, name="product_delete_confirm")
async def product_delete_confirm(request: Request, product_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        product = pd.get_product(conn, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return templates.TemplateResponse("product_delete_confirm.html",
                                      {"request": request, "product": product})

@app.post("/products/{product_id}/delete", name="product_delete")
async def product_delete(request: Request, product_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        deleted = pd.delete_product(conn, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Товар не найден")
    # Правильное формирование адреса с query-параметром
    url = request.url_for("admin").include_query_params(tab="products")
    return RedirectResponse(url=url, status_code=303)


# Добавьте эти импорты в начало файла, если их еще нет
from typing import List
import sqlite3


# CRUD операции для адресов

# Создание адреса
@app.get("/admin/address/add", response_class=HTMLResponse, name="add_address_form")
async def add_address_form(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        # Получаем список пользователей для выпадающего списка
        all_users = users.list_users(conn)
        fields = addres.address_table_info(conn)
    return templates.TemplateResponse(
        "add_address.html",
        {
            "request": request,
            "fields": fields,
            "users": all_users
        }
    )


@app.post("/admin/address/add", name="add_address_submit")
async def add_address_submit(request: Request):
    return await process_add_address(request)


async def process_add_address(request: Request):
    form = await request.form()
    data = {k: v for k, v in form.items()}

    # Валидация обязательных полей
    required_fields = ['country', 'city_type', 'city', 'street_type', 'street', 'house_number', 'user_id']
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Поле {field} обязательно")

    with sqlite3.connect(DB_PATH) as conn:
        # Создаем объект адреса
        address_data = {
            'id': addres.get_next_address_id(conn),
            'country': data['country'].strip(),
            'city_type': data['city_type'].strip(),
            'city': data['city'].strip(),
            'street_type': data['street_type'].strip(),
            'street': data['street'].strip(),
            'house_number': data['house_number'].strip(),
            'apartment': data.get('apartment', '').strip() or None,
            'user_id': data['user_id'].strip()
        }

        address = addres.Address(**address_data)
        addres.create_address(conn, address)

    url = request.url_for("admin").include_query_params(tab="addresses")
    return RedirectResponse(url=str(url), status_code=303)


# Просмотр деталей адреса
@app.get("/admin/address/{address_id}", response_class=HTMLResponse, name="address_detail")
async def address_detail(request: Request, address_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        address = addres.get_address(conn, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Адрес не найден")

        # Получаем информацию о пользователе
        user = users.get_user(conn, address.user_id) if address.user_id else None

    return templates.TemplateResponse(
        "address_detail.html",
        {
            "request": request,
            "address": address,
            "user": user
        }
    )


@app.get("/admin/address/{address_id}/edit", response_class=HTMLResponse, name="address_edit_form")
async def address_edit_form(request: Request, address_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        address = addres.get_address(conn, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Адрес не найден")

        all_users = users.list_users(conn)
        addresses_header = addres.address_table_info(conn)  # Получаем заголовки

    return templates.TemplateResponse(
        "address_edit.html",
        {
            "request": request,
            "address": address,
            "users": all_users,
            "addresses_header": addresses_header  # Передаем в шаблон
        }
    )

@app.post("/admin/address/{address_id}/edit", name="address_edit_submit")
async def address_edit_submit(request: Request, address_id: str):
    return await process_edit_address(request, address_id)


async def process_edit_address(request: Request, address_id: str):
    form = await request.form()
    data = {k: v for k, v in form.items()}

    with sqlite3.connect(DB_PATH) as conn:
        address = addres.get_address(conn, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Адрес не найден")

        # Валидация обязательных полей
        required_fields = ['country', 'city_type', 'city', 'street_type', 'street', 'house_number', 'user_id']
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=400, detail=f"Поле {field} обязательно")

        # Обновляем поля
        address.country = data['country'].strip()
        address.city_type = data['city_type'].strip()
        address.city = data['city'].strip()
        address.street_type = data['street_type'].strip()
        address.street = data['street'].strip()
        address.house_number = data['house_number'].strip()
        address.apartment = data.get('apartment', '').strip() or None
        address.user_id = data['user_id'].strip()

        ok = addres.update_address(conn, address)
        if not ok:
            raise HTTPException(status_code=500, detail="Не удалось обновить адрес")

    url = request.url_for("admin").include_query_params(tab="addresses")
    return RedirectResponse(url=str(url), status_code=303)


# Удаление адреса (подтверждение)
@app.get("/admin/address/{address_id}/delete", response_class=HTMLResponse, name="address_delete_confirm")
async def address_delete_confirm(request: Request, address_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        address = addres.get_address(conn, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Адрес не найден")

        user = users.get_user(conn, address.user_id) if address.user_id else None

    return templates.TemplateResponse(
        "address_delete_confirm.html",
        {
            "request": request,
            "address": address,
            "user": user
        }
    )


@app.post("/admin/address/{address_id}/delete", name="address_delete")
async def address_delete(request: Request, address_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        deleted = addres.delete_address(conn, address_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Адрес не найден")

    url = request.url_for("admin").include_query_params(tab="addresses")
    return RedirectResponse(url=url, status_code=303)


# CRUD операции для заказов

# Создание заказа
@app.get("/admin/order/add", response_class=HTMLResponse, name="add_order_form")
async def add_order_form(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        products = pd.list_products(conn)
        addresses = addres.list_addresses(conn)

        # Получаем детальную информацию для отображения
        addresses_details = []
        for addr in addresses:
            user = users.get_user(conn, addr.user_id) if addr.user_id else None
            addresses_details.append({
                'address': addr,
                'user': user
            })

    return templates.TemplateResponse(
        "add_order.html",
        {
            "request": request,
            "products": products,
            "addresses_details": addresses_details
        }
    )


@app.post("/admin/order/add", name="add_order_submit")
async def add_order_submit(request: Request):
    return await process_add_order(request)


async def process_add_order(request: Request):
    form = await request.form()
    data = {k: v for k, v in form.items()}

    # Валидация обязательных полей
    required_fields = ['product_id', 'quantity', 'address_id']
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Поле {field} обязательно")

    try:
        quantity = int(data['quantity'])
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректное количество")

    with sqlite3.connect(DB_PATH) as conn:
        # Рассчитываем общую стоимость
        total_price = ords.calculate_total_price(conn, data['product_id'], quantity)

        # Создаем объект заказа
        order_data = {
            'id': ords.get_next_order_id(conn),
            'product_id': data['product_id'].strip(),
            'quantity': quantity,
            'address_id': data['address_id'].strip(),
            'order_date': datetime.now().isoformat(),
            'total_price': total_price,
            'status': data.get('status', 'pending')
        }

        order = ords.Order(**order_data)
        ords.create_order(conn, order)

    url = request.url_for("admin").include_query_params(tab="orders")
    return RedirectResponse(url=str(url), status_code=303)


# Просмотр деталей заказа
@app.get("/admin/order/{order_id}", response_class=HTMLResponse, name="order_detail")
async def order_detail(request: Request, order_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        order_details = ords.orders_with_details(conn)
        order = next((o for o in order_details if o['id'] == order_id), None)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "order": order
        }
    )


# Редактирование заказа
@app.get("/admin/order/{order_id}/edit", response_class=HTMLResponse, name="order_edit_form")
async def order_edit_form(request: Request, order_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        order = ords.get_order(conn, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        products = pd.list_products(conn)
        addresses = addres.list_addresses(conn)

        # Получаем детальную информацию для отображения
        addresses_details = []
        for addr in addresses:
            user = users.get_user(conn, addr.user_id) if addr.user_id else None
            addresses_details.append({
                'address': addr,
                'user': user
            })

    return templates.TemplateResponse(
        "order_edit.html",
        {
            "request": request,
            "order": order,
            "products": products,
            "addresses_details": addresses_details
        }
    )


@app.post("/admin/order/{order_id}/edit", name="order_edit_submit")
async def order_edit_submit(request: Request, order_id: str):
    return await process_edit_order(request, order_id)


async def process_edit_order(request: Request, order_id: str):
    form = await request.form()
    data = {k: v for k, v in form.items()}

    with sqlite3.connect(DB_PATH) as conn:
        order = ords.get_order(conn, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        # Валидация обязательных полей
        required_fields = ['product_id', 'quantity', 'address_id']
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=400, detail=f"Поле {field} обязательно")

        try:
            quantity = int(data['quantity'])
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным")
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректное количество")

        # Пересчитываем стоимость если изменился товар или количество
        if order.product_id != data['product_id'] or order.quantity != quantity:
            total_price = ords.calculate_total_price(conn, data['product_id'], quantity)
        else:
            total_price = order.total_price

        # Обновляем поля
        order.product_id = data['product_id'].strip()
        order.quantity = quantity
        order.address_id = data['address_id'].strip()
        order.total_price = total_price
        order.status = data.get('status', order.status)

        ok = ords.update_order(conn, order)
        if not ok:
            raise HTTPException(status_code=500, detail="Не удалось обновить заказ")

    url = request.url_for("admin").include_query_params(tab="orders")
    return RedirectResponse(url=str(url), status_code=303)


# Удаление заказа
@app.get("/admin/order/{order_id}/delete", response_class=HTMLResponse, name="order_delete_confirm")
async def order_delete_confirm(request: Request, order_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        order = ords.get_order(conn, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        # Получаем детальную информацию
        order_details = ords.orders_with_details(conn)
        order_detail = next((o for o in order_details if o['id'] == order_id), None)

    return templates.TemplateResponse(
        "order_delete_confirm.html",
        {
            "request": request,
            "order": order_detail if order_detail else order
        }
    )


@app.post("/admin/order/{order_id}/delete", name="order_delete")
async def order_delete(request: Request, order_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        deleted = ords.delete_order(conn, order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    url = request.url_for("admin").include_query_params(tab="orders")
    return RedirectResponse(url=url, status_code=303)

# Также обновите функцию on_startup чтобы инициализировать таблицу адресов
@app.on_event("startup")
async def on_startup():
    with sqlite3.connect(DB_PATH) as conn:
        users.init_db_schema(conn)
        pd.init_products_table(conn)
        pd.upgrade_products_add_category(conn)
        pd.upgrade_products_add_weight(conn)
        addres.init_addresses_table(conn)  # Добавьте эту строку
        ords.init_orders_table(conn)  # Добавьте эту строку
