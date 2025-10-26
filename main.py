import ipaddress
import mimetypes
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status
from starlette.middleware.sessions import SessionMiddleware
import secrets
import sqlite3
import setting
from DataBase.products import Product
from setting import *
from DataBase import users, addres
from DataBase import products as pd
from DataBase import orders as ords
from DataBase import authorization as au
from DataBase import user_order_address as uoa
from fastapi import Query
from contextlib import contextmanager
from typing import List
from DataBase import faq as fq

app = FastAPI()

# Добавляем middleware для сессий
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-here-change-in-production")

# монтируем /static → папка static/ в корне проекта
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# указываем Jinja2Templates, папка templates/ в корне проекта
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# Зависимость для получения текущего пользователя с ролью
async def get_current_user(request: Request):
    """
    Возвращает объединенные данные пользователя с ролью из user_credentials
    """
    session_id = request.session.get("session_id")
    if not session_id:
        return None

    with sqlite3.connect(DB_PATH) as conn:
        # Получаем сессию
        session = au.get_user_session(conn, session_id)
        if not session or session.is_expired():
            return None

        # Получаем основную информацию о пользователе
        user = users.get_user(conn, session.user_id)
        if not user:
            return None

        # Получаем учетные данные с ролью
        credential = au.get_user_credential(conn, session.user_id)

        if not credential:
            return None

        # Создаем объединенный объект с ролью
        user_with_role = type('UserWithRole', (object,), {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "middle_name": user.middle_name,
            "birthdate": user.birthdate,
            "phone": user.phone,
            "email": user.email,
            "vip": user.vip,
            "photo": user.photo,
            "login": user.login,
            # Добавляем роль из учетных данных
            "role": credential.role
        })()

        return user_with_role


# Зависимость для проверки аутентификации
async def require_auth(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return current_user


# Зависимость для проверки администратора
async def require_admin(current_user=Depends(require_auth)):
    """
    Проверяет, является ли пользователь администратором
    Использует поле role из user_credentials вместо vip
    """
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return current_user


@app.on_event("startup")
async def on_startup():
    with sqlite3.connect(DB_PATH) as conn:
        pd.init_products_table(conn)
        pd.upgrade_products_add_category(conn)
        pd.upgrade_products_add_weight(conn)
        users.init_db_schema(conn)
        addres.init_addresses_table(conn)
        ords.init_orders_table(conn)
        uoa.init_user_order_address_table(conn)
        au.init_user_credentials_table(conn)
        au.init_user_sessions_table(conn)


@contextmanager
def get_db():
    conn = sqlite3.connect(setting.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Middleware для обновления активности сессии
@app.middleware("http")
async def update_session_activity(request: Request, call_next):
    response = await call_next(request)

    session_id = request.session.get("session_id")
    if session_id:
        with sqlite3.connect(DB_PATH) as conn:
            au.update_session_activity(conn, session_id)

    return response


# Маршруты аутентификации
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """
    Форма входа
    """
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.post("/login")
async def login_submit(
        request: Request,
        response: Response,
        login: str = Form(...),
        password: str = Form(...)
):
    """
    Обработка входа
    """
    with sqlite3.connect(DB_PATH) as conn:
        credential = au.authenticate_user(conn, login, password)

        if not credential:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Неверный логин или пароль"}
            )

        # Создаем сессию
        session = au.create_user_session(conn, credential.user_id)

        # Сохраняем в сессии
        request.session["user_id"] = credential.user_id
        request.session["session_id"] = session.session_id

        return RedirectResponse(url="/profile", status_code=303)


@app.post("/logout")
async def logout(request: Request, response: Response):
    """
    Выход из системы
    """
    session_id = request.session.get("session_id")
    user_id = request.session.get("user_id")

    if session_id and user_id:
        with sqlite3.connect(DB_PATH) as conn:
            au.delete_user_session(conn, session_id)

    # Очищаем сессию
    request.session.clear()

    return RedirectResponse(url="/", status_code=303)


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    """
    Форма регистрации
    """
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@app.post("/register")
async def register_submit(
        request: Request,
        login: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: str = Form(None),
        phone: str = Form(None),
        birthdate: str = Form(None)
):
    """
    Обработка регистрации
    """
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароли не совпадают"}
        )

    with sqlite3.connect(DB_PATH) as conn:
        # Проверяем, не занят ли логин
        if au.user_exists_by_login(conn, login):
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Пользователь с таким логином уже существует"}
            )

        # Создаем пользователя
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'birthdate': birthdate,
            'vip': False  # Обычный пользователь
        }

        success = au.create_complete_user(conn, user_data, login, password)

        if success:
            # Автоматически входим после регистрации
            credential = au.authenticate_user(conn, login, password)
            if credential:
                session = au.create_user_session(conn, credential.user_id)
                request.session["user_id"] = credential.user_id
                request.session["session_id"] = session.session_id
                return RedirectResponse(url="/profile", status_code=303)

        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Ошибка при создании пользователя"}
        )


# Основные маршруты
@app.get("/home", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user=Depends(get_current_user)):
    """
    Главная страница
    """
    return templates.TemplateResponse(
        "home1.html",
        {
            "request": request,
            "user": current_user
        }
    )


@app.get("/products", response_class=HTMLResponse)
async def products(
        request: Request,
        current_user=Depends(get_current_user),
        q: str = Query(None, description="Поисковый запрос"),
        categories: str = Query(None, description="Категории через запятую"),
        min_price: float = Query(None, description="Минимальная цена"),
        max_price: float = Query(None, description="Максимальная цена"),
        in_stock: bool = Query(False, description="Только в наличии"),
        low_stock: bool = Query(False, description="Мало в наличии"),
        with_photo: bool = Query(False, description="Только с фото"),
        sort: str = Query("name_asc", description="Сортировка"),
        page: int = Query(1, description="Номер страницы")
):
    """
    Каталог товаров с поиском и фильтрами
    """
    # Параметры пагинации
    per_page = 12
    offset = (page - 1) * per_page

    # Базовый SQL запрос
    base_query = "SELECT * FROM products WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM products WHERE 1=1"
    params = []

    # Применение фильтров
    if q:
        base_query += " AND (name LIKE ? OR description LIKE ?)"
        count_query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f'%{q}%', f'%{q}%'])

    if categories:
        category_list = [cat.strip() for cat in categories.split(',')]
        placeholders = ','.join(['?'] * len(category_list))
        base_query += f" AND category IN ({placeholders})"
        count_query += f" AND category IN ({placeholders})"
        params.extend(category_list)

    if min_price is not None:
        base_query += " AND price >= ?"
        count_query += " AND price >= ?"
        params.append(min_price)

    if max_price is not None:
        base_query += " AND price <= ?"
        count_query += " AND price <= ?"
        params.append(max_price)

    if in_stock:
        base_query += " AND stock > 10"
        count_query += " AND stock > 10"

    if low_stock:
        base_query += " AND stock > 0 AND stock <= 10"
        count_query += " AND stock > 0 AND stock <= 10"

    if with_photo:
        base_query += " AND image IS NOT NULL AND image != ''"
        count_query += " AND image IS NOT NULL AND image != ''"

    # Применение сортировки
    sort_mapping = {
        "name_asc": "name ASC",
        "name_desc": "name DESC",
        "price_asc": "price ASC",
        "price_desc": "price DESC",
        "stock_desc": "stock DESC"
    }
    sort_clause = sort_mapping.get(sort, "name ASC")
    base_query += f" ORDER BY {sort_clause}"

    # Получение общего количества товаров
    conn = sqlite3.connect(setting.DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Подсчет общего количества
    count_params = params.copy()
    cur.execute(count_query, count_params)
    total_count = cur.fetchone()[0]
    total_pages = (total_count + per_page - 1) // per_page

    # Применение пагинации
    base_query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    # Получение товаров
    cur.execute(base_query, params)
    products_rows = cur.fetchall()

    # Преобразование в объекты Product
    products = []
    for row in products_rows:
        weight = 0.0
        if "weight" in row.keys():
            weight = row["weight"]

        product = Product(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            stock=row["stock"],
            image=row["image"],
            category=row["category"],
            weight=weight
        )
        products.append(product)

    # Получение всех категорий для фильтра
    cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category")
    categories_rows = cur.fetchall()
    all_categories = [row["category"] for row in categories_rows]

    conn.close()

    # Подготовка данных для шаблона
    selected_categories = categories.split(',') if categories else []

    return templates.TemplateResponse(
        "all_products.html",
        {
            "request": request,
            "user": current_user,
            "products": products,
            "categories": all_categories,
            "search_query": q or "",
            "selected_categories": selected_categories,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock,
            "low_stock": low_stock,
            "with_photo": with_photo,
            "sort_by": sort,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count
        }
    )


@app.get("/faq", response_class=HTMLResponse)
async def faq_page(
        request: Request,
        current_user=Depends(get_current_user),
        category: str = Query("ПРОТЕИНЫ", description="Категория для анализа"),
        user_pk: str = Query(None, description="ID пользователя для анализа")
):
    """
    Страница FAQ с тремя независимыми отчетами
    """
    # Инициализируем переменные для каждого раздела
    largest_order_info = None
    category_lovers = []
    user_favorite = None
    user_exists_flag = False

    with sqlite3.connect(DB_PATH) as conn:
        # 1. Адрес доставки самого большого заказа и его владелец
        try:
            largest_order_info = fq.get_largest_order_info(conn)
        except Exception as e:
            print(f"Error processing largest order: {e}")

        # 2. Топ любителей категории (работает независимо от других параметров)
        try:
            category_lovers = fq.get_category_lovers(conn, category)
        except Exception as e:
            print(f"Error processing category lovers: {e}")

        # 3. Любимый товар пользователя (работает только если указан user_pk)
        if user_pk:
            try:
                # Сначала проверяем существование пользователя
                user_exists_flag = fq.user_exists(conn, user_pk)
                if user_exists_flag:
                    user_favorite = fq.get_user_favorite_product(conn, user_pk)
            except Exception as e:
                print(f"Error processing user favorite: {e}")

        # Получаем все категории для выпадающего списка
        all_categories = fq.get_all_categories(conn)

    return templates.TemplateResponse(
        "faq.html",
        {
            "request": request,
            "user": current_user,
            "largest_order_info": largest_order_info,
            "category_lovers": category_lovers,
            "user_favorite": user_favorite,
            "user_exists": user_exists_flag,
            "all_categories": all_categories,
            "selected_category": category,
            "user_pk": user_pk or ""
        }
    )


# Эндпоинт для умных подсказок поиска
@app.get("/api/search-suggestions")
async def search_suggestions(
        q: str = Query(..., min_length=2, description="Поисковый запрос для подсказок")
):
    """
    API для получения умных подсказок при поиске товаров
    """
    try:
        conn = sqlite3.connect(setting.DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        search_pattern = f"%{q}%"
        starts_with_pattern = f"{q}%"

        # 1. Ищем товары, которые начинаются с запроса (высший приоритет)
        product_query = """
            SELECT name, category, price, image,
                   CASE 
                       WHEN name LIKE ? THEN 1  
                       WHEN name LIKE ? THEN 2  
                       ELSE 3
                   END as relevance
            FROM products 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY relevance, name
            LIMIT 5
        """

        cur.execute(product_query, [starts_with_pattern, search_pattern, search_pattern, search_pattern])
        product_suggestions = []
        for row in cur.fetchall():
            product_suggestions.append({
                "type": "product",
                "name": row["name"],
                "category": row["category"],
                "price": row["price"],
                "image": row["image"],
                "relevance": row["relevance"]
            })

        # 2. Ищем категории
        category_query = """
            SELECT DISTINCT category as name
            FROM products 
            WHERE category LIKE ? AND category IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN category LIKE ? THEN 1
                    ELSE 2
                END
            LIMIT 3
        """

        cur.execute(category_query, [search_pattern, starts_with_pattern])
        category_suggestions = []
        for row in cur.fetchall():
            category_suggestions.append({
                "type": "category",
                "name": row["name"]
            })

        # 3. Ищем популярные поисковые фразы (на основе названий товаров)
        phrase_query = """
            SELECT DISTINCT name as phrase
            FROM products 
            WHERE (name LIKE ? OR description LIKE ?)
            AND name NOT IN (SELECT name FROM products WHERE name LIKE ? LIMIT 5)
            ORDER BY 
                CASE 
                    WHEN name LIKE ? THEN 1
                    ELSE 2
                END,
                name
            LIMIT 3
        """

        cur.execute(phrase_query, [search_pattern, search_pattern, starts_with_pattern, starts_with_pattern])
        phrase_suggestions = []
        for row in cur.fetchall():
            phrase_suggestions.append({
                "type": "suggestion",
                "text": row["phrase"]
            })

        conn.close()

        # Комбинируем все подсказки с приоритетами
        all_suggestions = []

        # Сначала товары, которые точно совпадают
        all_suggestions.extend(product_suggestions)

        # Затем категории
        all_suggestions.extend(category_suggestions)

        # Затем поисковые фразы
        all_suggestions.extend(phrase_suggestions)

        return all_suggestions

    except Exception as e:
        print(f"Error in search suggestions: {e}")
        return []


# Эндпоинт для популярных поисковых запросов
@app.get("/api/popular-searches")
async def popular_searches():
    """
    API для получения популярных поисковых запросов
    """
    try:
        conn = sqlite3.connect(setting.DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Возвращаем товары с наибольшим количеством
        query = """
            SELECT name, COUNT(*) as search_count
            FROM products 
            WHERE stock > 0
            GROUP BY name 
            ORDER BY search_count DESC, name
            LIMIT 8
        """

        cur.execute(query)
        popular_searches = []
        for row in cur.fetchall():
            popular_searches.append({
                "text": row["name"],
                "count": row["search_count"]
            })

        conn.close()
        return popular_searches

    except Exception as e:
        print(f"Error in popular searches: {e}")
        return []


@app.get("/categories", response_class=HTMLResponse)
async def categories(request: Request, current_user=Depends(get_current_user)):
    """
    Категории
    """
    return templates.TemplateResponse(
        "categories.html",
        {
            "request": request,
            "user": current_user
        }
    )


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, current_user=Depends(require_auth)):
    """
    Личный кабинет - требует аутентификации
    """
    with sqlite3.connect(DB_PATH) as conn:
        # Получаем заказы пользователя
        user_orders = uoa.get_user_order_addresses_by_user(conn, current_user.id)
        orders_details = []

        for uo in user_orders:
            order = ords.get_order(conn, uo.order_id)
            if order:
                product = pd.get_product(conn, order.product_id)
                address = addres.get_address(conn, uo.address_id)
                orders_details.append({
                    'order': order,
                    'product': product,
                    'address': address
                })

    return templates.TemplateResponse(
        "profile_view.html",
        {
            "request": request,
            "user": current_user,
            "orders": orders_details
        }
    )


@app.get("/admin", response_class=HTMLResponse, name="admin")
async def admin(
        request: Request,
        current_user=Depends(require_admin),  # Используем исправленную зависимость
        tab: str = "users",
        login_search: str = Query("", alias="login_search"),
        address_search: str = Query("", alias="address_search"),
        order_search: str = Query("", alias="order_search"),
        credential_search: str = Query("", alias="credential_search"),
        user_order_search: str = Query("", alias="user_order_search"),
        page: int = Query(1, ge=1),
        show_all: bool = Query(False),
        sort_field: str = Query("", description="Поле для сортировки"),
        sort_order: str = Query("asc", description="Порядок сортировки (asc/desc)")
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
            login_search=login_search,
            show_all=show_all,
            sort_field=sort_field,
            sort_order=sort_order
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
            address_search=address_search,
            show_all=show_all,
            sort_field=sort_field,
            sort_order=sort_order
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
            page=page,
            show_all=show_all,
            sort_field=sort_field,
            sort_order=sort_order
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
            order_search=order_search,
            show_all=show_all,
            sort_field=sort_field,
            sort_order=sort_order
        )
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # Обработка удаления учетных данных
    elif tab == "credentials" and action == "delete_credential" and delete_id:
        with sqlite3.connect(DB_PATH) as conn:
            ok = au.delete_user_credential(conn, delete_id)
        url = request.url_for("admin").include_query_params(
            tab="credentials",
            page=page,
            credential_search=credential_search,
            show_all=show_all,
            sort_field=sort_field,
            sort_order=sort_order
        )
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # Обработка удаления связи
    elif tab == "user_orders" and action == "delete_user_order" and delete_id:
        with sqlite3.connect(DB_PATH) as conn:
            ok = uoa.delete_user_order_address(conn, int(delete_id))
        url = request.url_for("admin").include_query_params(
            tab="user_orders",
            page=page,
            user_order_search=user_order_search,
            show_all=show_all,
            sort_field=sort_field,
            sort_order=sort_order
        )
        if not ok:
            url = url.include_query_params(error="not_found")
        return RedirectResponse(url=str(url), status_code=303)

    # Получаем данные для отображения с учетом сортировки
    per_page = 50 if show_all else 10
    paged_users = []
    list_product_page = []
    paged_addresses = []
    paged_orders = []
    paged_credentials = []
    paged_user_orders = []

    if tab == "users":
        with sqlite3.connect(DB_PATH) as conn:
            all_users = users.list_users(conn)
            users_header = users.users_table_info(conn)

        # Применяем поиск
        filtered_users = all_users
        if login_search:
            filtered_users = [
                u for u in all_users
                if login_search.lower() in u.login.lower()
                   or login_search.lower() in u.last_name.lower()
                   or login_search.lower() in u.first_name.lower()
                   or login_search.lower() in u.id.lower()
            ]

        # Применяем сортировку
        if sort_field:
            def get_sort_key(user):
                value = getattr(user, sort_field, '')
                value_str = str(value)

                # Специальная обработка для ID
                if sort_field == 'id':
                    # Отсекаем буквенную часть и оставляем цифры
                    import re
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        return int(numbers[0])  # Берем первую найденную цифру
                    return 0

                # Для VIP преобразуем в булево
                elif sort_field == 'vip':
                    return bool(value)
                # Для дат пытаемся преобразовать
                elif sort_field == 'birthdate' and value_str:
                    try:
                        return datetime.strptime(value_str, '%Y-%m-%d')
                    except:
                        return value_str
                else:
                    return value_str.lower()

            reverse = sort_order == 'desc'
            filtered_users.sort(key=get_sort_key, reverse=reverse)

        total_count = len(filtered_users)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1

        if show_all:
            paged_users = filtered_users
            total_pages = 1
            page = 1
        else:
            start = (page - 1) * per_page
            end = start + per_page
            paged_users = filtered_users[start:end]

    elif tab == "products":
        with sqlite3.connect(DB_PATH) as conn:
            all_products = pd.list_products(conn)
            product_header = pd.products_table_info(conn)

        # Применяем сортировку
        filtered_products = all_products
        if sort_field:
            def get_sort_key(product):
                value = getattr(product, sort_field, '')
                value_str = str(value)

                # Специальная обработка для ID
                if sort_field == 'id':
                    # Отсекаем буквенную часть и оставляем цифры
                    import re
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        return int(numbers[0])  # Берем первую найденную цифру
                    return 0

                # Для числовых полей
                elif sort_field in ['price', 'stock', 'weight']:
                    return float(value) if value else 0.0
                else:
                    return value_str.lower()

            reverse = sort_order == 'desc'
            filtered_products.sort(key=get_sort_key, reverse=reverse)

        total_count = len(filtered_products)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1

        if show_all:
            list_product_page = filtered_products
            total_pages = 1
            page = 1
        else:
            start = (page - 1) * per_page
            end = start + per_page
            list_product_page = filtered_products[start:end]

    elif tab == "addresses":
        with sqlite3.connect(DB_PATH) as conn:
            all_addresses = addres.list_addresses(conn)
            addresses_header = addres.address_table_info(conn)

        # Применяем поиск
        filtered_addresses = all_addresses
        if address_search:
            filtered_addresses = [
                a for a in all_addresses
                if address_search.lower() in a.country.lower()
                   or address_search.lower() in a.city.lower()
                   or address_search.lower() in a.street.lower()
                   or address_search.lower() in str(a.user_id).lower()
                   or address_search.lower() in str(a.id).lower()
            ]

        # Применяем сортировку
        if sort_field:
            def get_sort_key(address):
                value = getattr(address, sort_field, '')
                value_str = str(value)

                # Специальная обработка для ID
                if sort_field == 'id':
                    # Отсекаем буквенную часть и оставляем цифры
                    import re
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        return int(numbers[0])  # Берем первую найденную цифру
                    return 0
                else:
                    return value_str.lower()

            reverse = sort_order == 'desc'
            filtered_addresses.sort(key=get_sort_key, reverse=reverse)

        total_count = len(filtered_addresses)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1

        if show_all:
            paged_addresses = filtered_addresses
            total_pages = 1
            page = 1
        else:
            start = (page - 1) * per_page
            end = start + per_page
            paged_addresses = filtered_addresses[start:end]

    elif tab == "orders":
        with sqlite3.connect(DB_PATH) as conn:
            # Получаем заказы с деталями через новую структуру
            all_orders = ords.orders_with_details(conn)
            orders_header = ords.orders_table_info(conn)

        # Применяем поиск
        filtered_orders = all_orders
        if order_search:
            filtered_orders = [
                o for o in all_orders
                if order_search.lower() in o['id'].lower()
                   or order_search.lower() in o.get('product_name', '').lower()
                   or order_search.lower() in o['product_id'].lower()
                   or (o.get('first_name') and order_search.lower() in o['first_name'].lower())
                   or (o.get('last_name') and order_search.lower() in o['last_name'].lower())
                   or (o.get('user_id') and order_search.lower() in str(o['user_id']).lower())
                   or (o.get('country') and order_search.lower() in o['country'].lower())
                   or (o.get('city') and order_search.lower() in o['city'].lower())
                   or (o.get('street') and order_search.lower() in o['street'].lower())
            ]

        # Применяем сортировку
        if sort_field:
            def get_sort_key(order):
                value = order.get(sort_field, '')
                value_str = str(value)

                # Специальная обработка для ID
                if sort_field == 'id':
                    # Отсекаем буквенную часть и оставляем цифры
                    import re
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        return int(numbers[0])  # Берем первую найденную цифру
                    return 0

                # Для числовых полей
                elif sort_field in ['quantity', 'total_price', 'product_price']:
                    return float(value) if value else 0.0
                # Для дат
                elif sort_field == 'order_date' and value_str:
                    try:
                        return datetime.fromisoformat(value_str.replace('Z', '+00:00'))
                    except:
                        return value_str
                else:
                    return value_str.lower()

            reverse = sort_order == 'desc'
            filtered_orders.sort(key=get_sort_key, reverse=reverse)

        total_count = len(filtered_orders)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1

        if show_all:
            paged_orders = filtered_orders
            total_pages = 1
            page = 1
        else:
            start = (page - 1) * per_page
            end = start + per_page
            paged_orders = filtered_orders[start:end]

    elif tab == "credentials":
        with sqlite3.connect(DB_PATH) as conn:
            all_credentials = au.list_user_credentials(conn)
            credentials_header = au.credentials_table_info(conn)

        # Применяем поиск
        filtered_credentials = all_credentials
        if credential_search:
            filtered_credentials = [
                c for c in all_credentials
                if credential_search.lower() in str(c.user_id).lower()
                   or credential_search.lower() in c.login.lower()
            ]

        # Применяем сортировку
        if sort_field:
            def get_sort_key(credential):
                value = getattr(credential, sort_field, '')
                value_str = str(value)

                # Специальная обработка для ID
                if sort_field == 'user_id':
                    # Отсекаем буквенную часть и оставляем цифры
                    import re
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        return int(numbers[0])  # Берем первую найденную цифру
                    return 0

                return value_str.lower()

            reverse = sort_order == 'desc'
            filtered_credentials.sort(key=get_sort_key, reverse=reverse)

        total_count = len(filtered_credentials)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1

        if show_all:
            paged_credentials = filtered_credentials
            total_pages = 1
            page = 1
        else:
            start = (page - 1) * per_page
            end = start + per_page
            paged_credentials = filtered_credentials[start:end]

    elif tab == "user_orders":
        with sqlite3.connect(DB_PATH) as conn:
            all_user_orders = uoa.list_user_order_addresses(conn)
            user_orders_header = uoa.user_order_address_table_info(conn)

        # Применяем поиск
        filtered_user_orders = all_user_orders
        if user_order_search:
            filtered_user_orders = [
                uo for uo in all_user_orders
                if user_order_search.lower() in str(uo.user_id).lower()
                   or user_order_search.lower() in str(uo.order_id).lower()
                   or user_order_search.lower() in str(uo.address_id).lower()
                   or user_order_search.lower() in str(uo.id).lower()
            ]

        # Применяем сортировку
        if sort_field:
            def get_sort_key(user_order):
                value = getattr(user_order, sort_field, '')
                value_str = str(value)

                # Специальная обработка для ID
                if sort_field in ['id', 'user_id', 'order_id', 'address_id']:
                    # Отсекаем буквенную часть и оставляем цифры
                    import re
                    numbers = re.findall(r'\d+', value_str)
                    if numbers:
                        return int(numbers[0])  # Берем первую найденную цифру
                    return 0

                # Для дат
                elif sort_field == 'created_at' and value_str:
                    try:
                        return datetime.fromisoformat(value_str.replace('Z', '+00:00'))
                    except:
                        return value_str
                else:
                    return value_str.lower()

            reverse = sort_order == 'desc'
            filtered_user_orders.sort(key=get_sort_key, reverse=reverse)

        total_count = len(filtered_user_orders)
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1

        if show_all:
            paged_user_orders = filtered_user_orders
            total_pages = 1
            page = 1
        else:
            start = (page - 1) * per_page
            end = start + per_page
            paged_user_orders = filtered_user_orders[start:end]

    else:
        total_pages = 1
        total_count = 0

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
            "credentials_header": credentials_header if tab == "credentials" else [],
            "list_credentials": paged_credentials if tab == "credentials" else [],
            "user_orders_header": user_orders_header if tab == "user_orders" else [],
            "list_user_orders": paged_user_orders if tab == "user_orders" else [],
            "login_search": login_search,
            "address_search": address_search,
            "order_search": order_search,
            "credential_search": credential_search,
            "user_order_search": user_order_search,
            "page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "error": request.query_params.get("error", ""),
            "user": current_user,
            "show_all": show_all,
            "total_count": total_count,
            "sort_field": sort_field,
            "sort_order": sort_order
        }
    )


# Остальные маршруты остаются без изменений...

@app.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: str, current_user=Depends(require_auth)):
    with sqlite3.connect(DB_PATH) as conn:
        prod = pd.get_product(conn, product_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Товар не найден")
    return templates.TemplateResponse("product_detail.html", {
        "request": request,
        "product": prod,
        "user": current_user
    })


@app.get("/admin/users/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: int, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        user = users.get_user(conn, str(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
    return templates.TemplateResponse("profile_edit.html", {
        "request": request,
        "user": user,
        "current_user": current_user
    })


@app.get(
    "/profile/edit/{user_id}",
    response_class=HTMLResponse,
    name="profile_edit_form"
)
async def profile_edit_form(request: Request, user_id: str, current_user=Depends(require_auth)):
    """
    Показать форму редактирования профиля пользователя.
    user_id — строка, например 'us0', 'abc123' и т.п.
    """
    # Проверяем, что пользователь редактирует свой профиль
    if current_user.id != user_id and not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Недостаточно прав")

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
            "current_user": current_user
        },
    )


@app.post("/profile/edit/{user_id}", name="profile_edit_save")
async def profile_edit_save(request: Request, user_id: str, current_user=Depends(require_auth)):
    # Проверяем, что пользователь редактирует свой профиль
    if current_user.id != user_id and not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Недостаточно прав")

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
async def profile_view(request: Request, user_id: str, current_user=Depends(require_auth)):
    # Проверяем, что пользователь просматривает свой профиль или является администратором
    if current_user.id != user_id and not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    with sqlite3.connect(DB_PATH) as conn:
        u = users.get_user(conn, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user_dict = {}
    for key, value in vars(u).items():
        user_dict[key] = value

    return templates.TemplateResponse("profile_view.html", {
        "request": request,
        "user": user_dict,
        "current_user": current_user
    })


@app.get("/add_user", response_class=HTMLResponse, name="add_user_form")
async def add_user_form(request: Request, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        fields = users.users_table_info(conn)
    if not fields:
        raise HTTPException(status_code=404, detail="Структура таблицы не найдена")
    return templates.TemplateResponse("add_user.html", {
        "request": request,
        "fields": fields,
        "user": current_user
    })


@app.post("/add_user", name="add_user_submit")
async def add_user_submit(request: Request, current_user=Depends(require_admin)):
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

    # Валидация обязательных полей
    required_fields = ['login', 'password', 'role', 'first_name', 'last_name', 'phone', 'email']
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Поле {field} обязательно")

    # Проверка длины пароля
    if len(data['password']) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 6 символов")

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

    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Проверяем, не существует ли уже пользователь с таким логином
            existing_user = au.get_user_credential_by_login(conn, data['login'])
            if existing_user:
                raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

            # Создаем полного пользователя
            user_data = {
                'first_name': data['first_name'].strip(),
                'last_name': data['last_name'].strip(),
                'middle_name': data.get('middle_name', '').strip(),
                'birthdate': data.get('birthdate'),
                'phone': data['phone'].strip(),
                'email': data['email'].strip(),
                'vip': 'vip' in data and data['vip'] == 'true',
                'photo': local_photo_url
            }

            success = au.create_complete_user(
                conn=conn,
                user_data=user_data,
                login=data['login'].strip(),
                password=data['password'],
                role=data.get('role', 'user')  # ПЕРЕДАЕМ РОЛЬ
            )

            if not success:
                raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

    return RedirectResponse(url="/admin?tab=users", status_code=303)

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
        weight = float(data.get("weight") or 0)  # граммы
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
async def add_product_form(request: Request, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        # поля для формы (исключает image)
        fields = pd.products_table_info(conn)
    if not fields:
        raise HTTPException(status_code=404, detail="Структура таблицы products не найдена")
    return templates.TemplateResponse("add_product.html", {
        "request": request,
        "fields": fields,
        "user": current_user
    })


@app.post("/add_product", name="add_product_submit")
async def add_product_submit(request: Request, current_user=Depends(require_admin)):
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
async def product_edit_form(request: Request, product_id: str, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        product = pd.get_product(conn, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return templates.TemplateResponse("product_edit.html", {
        "request": request,
        "product": product,
        "user": current_user
    })


@app.post("/products/{product_id}/edit", name="product_edit_submit")
async def product_edit_submit(request: Request, product_id: str, current_user=Depends(require_admin)):
    return await process_edit_product(request, product_id)


@app.get("/products/{product_id}/delete", response_class=HTMLResponse, name="product_delete_confirm")
async def product_delete_confirm(request: Request, product_id: str, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        product = pd.get_product(conn, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return templates.TemplateResponse("product_delete_confirm.html", {
        "request": request,
        "product": product,
        "user": current_user
    })


@app.post("/products/{product_id}/delete", name="product_delete")
async def product_delete(request: Request, product_id: str, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        deleted = pd.delete_product(conn, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Товар не найден")
    # Правильное формирование адреса с query-параметром
    url = request.url_for("admin").include_query_params(tab="products")
    return RedirectResponse(url=url, status_code=303)


# CRUD операции для адресов

# Создание адреса
@app.get("/admin/address/add", response_class=HTMLResponse, name="add_address_form")
async def add_address_form(request: Request, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        # Получаем список пользователей для выпадающего списка
        all_users = users.list_users(conn)
        fields = addres.address_table_info(conn)
    return templates.TemplateResponse(
        "add_address.html",
        {
            "request": request,
            "fields": fields,
            "users": all_users,
            "user": current_user
        }
    )


@app.post("/admin/address/add", name="add_address_submit")
async def add_address_submit(request: Request, current_user=Depends(require_admin)):
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
async def address_detail(request: Request, address_id: str, current_user=Depends(require_admin)):
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
            "user": user,
            "current_user": current_user
        }
    )


@app.get("/admin/address/{address_id}/edit", response_class=HTMLResponse, name="address_edit_form")
async def address_edit_form(request: Request, address_id: str, current_user=Depends(require_admin)):
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
            "addresses_header": addresses_header,
            "user": current_user
        }
    )


@app.post("/admin/address/{address_id}/edit", name="address_edit_submit")
async def address_edit_submit(request: Request, address_id: str, current_user=Depends(require_admin)):
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
async def address_delete_confirm(request: Request, address_id: str, current_user=Depends(require_admin)):
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
            "user": user,
            "current_user": current_user
        }
    )


@app.post("/admin/address/{address_id}/delete", name="address_delete")
async def address_delete(request: Request, address_id: str, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        deleted = addres.delete_address(conn, address_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Адрес не найден")

    url = request.url_for("admin").include_query_params(tab="addresses")
    return RedirectResponse(url=url, status_code=303)


# CRUD операции для заказов

# Создание заказа
@app.get("/admin/orders/add", response_class=HTMLResponse, name="order_create")
async def add_order_form(request: Request, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        products = pd.list_products(conn)
        addresses = addres.list_addresses(conn)

        # Группируем адреса по пользователям для более удобного отображения
        users_addresses = {}
        for addr in addresses:
            if addr.user_id not in users_addresses:
                user = users.get_user(conn, addr.user_id) if addr.user_id else None
                users_addresses[addr.user_id] = {
                    'user': user,
                    'addresses': []
                }
            users_addresses[addr.user_id]['addresses'].append(addr)

    return templates.TemplateResponse(
        "add_order.html",
        {
            "request": request,
            "products": products,
            "users_addresses": users_addresses,
            "user": current_user
        }
    )


@app.post("/admin/orders/add", name="add_order_submit")
async def add_order_submit(
        request: Request,
        current_user=Depends(require_admin)
):
    return await process_add_order(request)


async def process_add_order(request: Request):
    form = await request.form()
    data = {k: v for k, v in form.items()}

    # Валидация обязательных полей (убираем address_id)
    required_fields = ['product_id', 'quantity']  # Убрали address_id
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

        # Создаем объект заказа (убираем address_id)
        order_data = {
            'id': ords.get_next_order_id(conn),
            'product_id': data['product_id'].strip(),
            'quantity': quantity,
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
async def order_detail(request: Request, order_id: str, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        order_details = ords.orders_with_details(conn)
        order = next((o for o in order_details if o['id'] == order_id), None)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "order": order,
            "user": current_user
        }
    )


# Редактирование заказа
@app.get("/admin/order/{order_id}/edit", response_class=HTMLResponse, name="order_edit_form")
async def order_edit_form(request: Request, order_id: str, current_user=Depends(require_admin)):
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
            "addresses_details": addresses_details,
            "user": current_user
        }
    )


@app.post("/admin/order/{order_id}/edit", name="order_edit_submit")
async def order_edit_submit(request: Request, order_id: str, current_user=Depends(require_admin)):
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
async def order_delete_confirm(request: Request, order_id: str, current_user=Depends(require_admin)):
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
            "order": order_detail if order_detail else order,
            "user": current_user
        }
    )


@app.post("/admin/order/{order_id}/delete", name="order_delete")
async def order_delete(request: Request, order_id: str, current_user=Depends(require_admin)):
    with sqlite3.connect(DB_PATH) as conn:
        deleted = ords.delete_order(conn, order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    url = request.url_for("admin").include_query_params(tab="orders")
    return RedirectResponse(url=url, status_code=303)


# Простые маршруты для управления учетными данными
@app.get("/admin/credentials/{user_id}/edit", response_class=HTMLResponse, name="credential_edit_form")
async def credential_edit_form(request: Request, user_id: str, current_user=Depends(require_admin)):
    """
    Форма изменения пароля пользователя
    """
    with sqlite3.connect(DB_PATH) as conn:
        user = users.get_user(conn, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        credential = au.get_user_credential(conn, user_id)

    return templates.TemplateResponse(
        "credential_edit.html",
        {
            "request": request,
            "user": user,
            "credential": credential,
            "current_user": current_user
        }
    )


@app.post("/admin/credentials/{user_id}/edit", name="credential_edit_submit")
async def credential_edit_submit(request: Request, user_id: str, current_user=Depends(require_admin)):
    """
    Обработка изменения пароля
    """
    form = await request.form()
    new_password = form.get("new_password")
    confirm_password = form.get("confirm_password")

    if not new_password or not confirm_password:
        raise HTTPException(status_code=400, detail="Все поля обязательны")

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    with sqlite3.connect(DB_PATH) as conn:
        password_hash = users.hash_password(new_password)
        success = au.update_user_password(conn, user_id, password_hash)

    if success:
        url = request.url_for("admin").include_query_params(tab="credentials")
        return RedirectResponse(url=str(url), status_code=303)
    else:
        raise HTTPException(status_code=404, detail="Учетные данные не найдены")


@app.get("/admin/credentials/{user_id}/delete", response_class=HTMLResponse, name="credential_delete_confirm")
async def credential_delete_confirm(request: Request, user_id: str, current_user=Depends(require_admin)):
    """
    Подтверждение удаления учетных данных
    """
    with sqlite3.connect(DB_PATH) as conn:
        user = users.get_user(conn, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        credential = au.get_user_credential(conn, user_id)

    return templates.TemplateResponse(
        "credential_delete_confirm.html",
        {
            "request": request,
            "user": user,
            "credential": credential,
            "current_user": current_user
        }
    )


@app.post("/admin/credentials/{user_id}/delete", name="credential_delete")
async def credential_delete(request: Request, user_id: str, current_user=Depends(require_admin)):
    """
    Удаление учетных данных
    """
    with sqlite3.connect(DB_PATH) as conn:
        deleted = au.delete_user_credential(conn, user_id)

    if deleted:
        url = request.url_for("admin").include_query_params(tab="credentials")
        return RedirectResponse(url=str(url), status_code=303)
    else:
        raise HTTPException(status_code=404, detail="Учетные данные не найдены")


@app.get("/admin/user-order/add", response_class=HTMLResponse, name="user_order_add_form")
async def user_order_add_form(request: Request, current_user=Depends(require_admin)):
    """
    Форма создания новой связи пользователя и заказа
    """
    with sqlite3.connect(DB_PATH) as conn:
        # Получаем все данные для выпадающих списков
        all_users = users.list_users(conn)
        all_orders = ords.list_orders(conn)
        all_addresses = addres.list_addresses(conn)

    return templates.TemplateResponse(
        "user_order_add.html",
        {
            "request": request,
            "all_users": all_users,
            "all_orders": all_orders,
            "all_addresses": all_addresses,
            "current_user": current_user
        }
    )


@app.post("/admin/user-order/add", name="user_order_add_submit")
async def user_order_add_submit(request: Request, current_user=Depends(require_admin)):
    """
    Обработка создания новой связи
    """
    form = await request.form()
    user_id = form.get("user_id")
    order_id = form.get("order_id")
    address_id = form.get("address_id")

    if not user_id or not order_id or not address_id:
        # Если не все поля заполнены, показываем форму с ошибкой
        with sqlite3.connect(DB_PATH) as conn:
            all_users = users.list_users(conn)
            all_orders = ords.list_orders(conn)
            all_addresses = addres.list_addresses(conn)

        return templates.TemplateResponse(
            "user_order_add.html",
            {
                "request": request,
                "all_users": all_users,
                "all_orders": all_orders,
                "all_addresses": all_addresses,
                "error": "Все поля обязательны для заполнения",
                "current_user": current_user
            }
        )

    with sqlite3.connect(DB_PATH) as conn:
        # Создаем объект связи (id будет автоматически сгенерирован)
        new_relation = uoa.UserOrderAddress(
            id=None,  # AUTOINCREMENT сам создаст ID
            user_id=user_id,
            order_id=order_id,
            address_id=address_id,
            created_at=datetime.now().isoformat()
        )

        # Создаем новую связь
        try:
            new_id = uoa.create_user_order_address(conn, new_relation)
            success = new_id is not None
        except Exception as e:
            print(f"Error creating relation: {e}")
            success = False

    if success:
        url = request.url_for("admin").include_query_params(tab="user_orders")
        return RedirectResponse(url=str(url), status_code=303)
    else:
        with sqlite3.connect(DB_PATH) as conn:
            all_users = users.list_users(conn)
            all_orders = ords.list_orders(conn)
            all_addresses = addres.list_addresses(conn)

        return templates.TemplateResponse(
            "user_order_add.html",
            {
                "request": request,
                "all_users": all_users,
                "all_orders": all_orders,
                "all_addresses": all_addresses,
                "error": "Не удалось создать связь. Возможно, такая связь уже существует.",
                "current_user": current_user
            }
        )


# Маршруты для управления связями пользователей и заказов
@app.get("/admin/user-order/{relation_id}/edit", response_class=HTMLResponse, name="user_order_edit_form")
async def user_order_edit_form(request: Request, relation_id: int, current_user=Depends(require_admin)):
    """
    Форма редактирования связи пользователя и заказа
    """
    with sqlite3.connect(DB_PATH) as conn:
        relation = uoa.get_user_order_address(conn, relation_id)
        if not relation:
            raise HTTPException(status_code=404, detail="Связь не найдена")

        # Получаем дополнительные данные для отображения
        user = users.get_user(conn, relation.user_id) if relation.user_id else None
        order = ords.get_order(conn, relation.order_id) if relation.order_id else None
        address = addres.get_address(conn, relation.address_id) if relation.address_id else None

        # Получаем все данные для выпадающих списков
        all_users = users.list_users(conn)
        all_orders = ords.orders_with_details(conn)
        all_addresses = addres.list_addresses(conn)

    return templates.TemplateResponse(
        "user_order_edit.html",
        {
            "request": request,
            "relation": relation,
            "user": user,
            "order": order,
            "address": address,
            "all_users": all_users,
            "all_orders": all_orders,
            "all_addresses": all_addresses,
            "current_user": current_user
        }
    )


@app.post("/admin/user-order/{relation_id}/edit", name="user_order_edit_submit")
async def user_order_edit_submit(request: Request, relation_id: int, current_user=Depends(require_admin)):
    """
    Обработка редактирования связи
    """
    form = await request.form()
    user_id = form.get("user_id")
    order_id = form.get("order_id")
    address_id = form.get("address_id")

    if not user_id or not order_id or not address_id:
        raise HTTPException(status_code=400, detail="Все поля обязательны")

    with sqlite3.connect(DB_PATH) as conn:
        relation = uoa.get_user_order_address(conn, relation_id)
        if not relation:
            raise HTTPException(status_code=404, detail="Связь не найдена")

        # Обновляем связь
        relation.user_id = user_id
        relation.order_id = order_id
        relation.address_id = address_id

        success = uoa.update_user_order_address(conn, relation)

    if success:
        url = request.url_for("admin").include_query_params(tab="user_orders")
        return RedirectResponse(url=str(url), status_code=303)
    else:
        raise HTTPException(status_code=500, detail="Не удалось обновить связь")


@app.get("/admin/user-order/{relation_id}/delete", response_class=HTMLResponse, name="user_order_delete_confirm")
async def user_order_delete_confirm(request: Request, relation_id: int, current_user=Depends(require_admin)):
    """
    Подтверждение удаления связи
    """
    with sqlite3.connect(DB_PATH) as conn:
        relation = uoa.get_user_order_address(conn, relation_id)
        if not relation:
            raise HTTPException(status_code=404, detail="Связь не найдена")

        # Получаем дополнительные данные для отображения
        user = users.get_user(conn, relation.user_id)
        order = ords.get_order(conn, relation.order_id)
        address = addres.get_address(conn, relation.address_id)

    return templates.TemplateResponse(
        "user_order_delete_confirm.html",
        {
            "request": request,
            "relation": relation,
            "user": user,
            "order": order,
            "address": address,
            "current_user": current_user
        }
    )


@app.post("/admin/user-order/{relation_id}/delete", name="user_order_delete")
async def user_order_delete(request: Request, relation_id: int, current_user=Depends(require_admin)):
    """
    Удаление связи
    """
    with sqlite3.connect(DB_PATH) as conn:
        deleted = uoa.delete_user_order_address(conn, relation_id)

    if deleted:
        url = request.url_for("admin").include_query_params(tab="user_orders")
        return RedirectResponse(url=str(url), status_code=303)
    else:
        raise HTTPException(status_code=404, detail="Связь не найдена")


@app.get("/admin/user-order/{relation_id}", response_class=HTMLResponse)
async def user_order_detail(request: Request, relation_id: int, current_user=Depends(require_admin)):
    """
    Детальная страница связи пользователя и заказа
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Получаем связь
            relation = uoa.get_user_order_address(conn, relation_id)
            if not relation:
                raise HTTPException(status_code=404, detail="Связь не найдена")

            # Преобразуем relation в словарь для удобства
            relation_dict = {
                'id': relation.id,
                'user_id': relation.user_id,
                'order_id': relation.order_id,
                'address_id': relation.address_id,
                'created_at': relation.created_at
            }

            # Получаем детальную информацию
            user = None
            if relation.user_id:
                user_obj = users.get_user(conn, relation.user_id)
                user = {
                    'id': user_obj.id,
                    'first_name': user_obj.first_name,
                    'last_name': user_obj.last_name,
                    'email': user_obj.email,
                    'phone': user_obj.phone,
                    'login': user_obj.login
                } if user_obj else None

            order = None
            if relation.order_id:
                order_obj = ords.get_order(conn, relation.order_id)
                order = {
                    'id': order_obj.id,
                    'product_id': order_obj.product_id,
                    'quantity': order_obj.quantity,
                    'total_price': order_obj.total_price,
                    'status': order_obj.status,
                    'order_date': order_obj.order_date
                } if order_obj else None

            address = None
            if relation.address_id:
                address_obj = addres.get_address(conn, relation.address_id)
                address = {
                    'id': address_obj.id,
                    'country': address_obj.country,
                    'city_type': address_obj.city_type,
                    'city': address_obj.city,
                    'street_type': address_obj.street_type,
                    'street': address_obj.street,
                    'house_number': address_obj.house_number,
                    'apartment': address_obj.apartment,
                    'user_id': address_obj.user_id
                } if address_obj else None

            # Получаем дополнительную информацию о заказе
            order_details = ords.orders_with_details(conn)
            order_detail = None
            for o in order_details:
                if o['id'] == relation.order_id:
                    order_detail = o
                    break

        return templates.TemplateResponse(
            "user_order_detail.html",
            {
                "request": request,
                "relation": relation_dict,
                "user": user,
                "order": order,
                "order_detail": order_detail,
                "address": address,
                "current_user": current_user
            }
        )
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке данных связи: {str(e)}")


@app.get("/api/category-lovers")
async def get_category_lovers_api(
        category: str = Query(..., description="Категория для анализа"),
        current_user=Depends(get_current_user)
):
    """
    API endpoint для получения топа покупателей категории
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            category_lovers = fq.get_category_lovers(conn, category)
            all_categories = fq.get_all_categories(conn)

        return {
            "success": True,
            "category_lovers": category_lovers,
            "selected_category": category,
            "all_categories": all_categories
        }

    except Exception as e:
        print(f"Error in category lovers API: {e}")
        return {
            "success": False,
            "error": str(e),
            "category_lovers": [],
            "selected_category": category
        }


@app.get("/contact", response_class=HTMLResponse)
async def contacts(request: Request, current_user=Depends(get_current_user)):
    """
    Страница контактов
    """
    return templates.TemplateResponse(
        "contacts.html",
        {
            "request": request,
            "user": current_user
        }
    )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, current_user=Depends(get_current_user)):
    """
    Страница о нас
    """
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "user": current_user
        }
    )
