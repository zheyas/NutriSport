# database/faq.py
import sqlite3
from typing import Optional, Dict, Any, List
import setting

def get_category_lovers(conn: sqlite3.Connection, category: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Топ любителей категории (топ пользователей по сумме потраченных денег в определенной категории)
    Сортировка по total_spent DESC (по убыванию суммы потраченных денег)
    """
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.id as user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                COUNT(DISTINCT o.id) as orders_count,
                SUM(o.quantity) as total_quantity,
                SUM(o.total_price) as total_spent,
                GROUP_CONCAT(DISTINCT p.name) as purchased_products
            FROM users u
            JOIN user_order_address uoa ON u.id = uoa.user_id
            JOIN orders o ON uoa.order_id = o.id
            JOIN products p ON o.product_id = p.id
            WHERE p.category = ?
            GROUP BY u.id, u.first_name, u.last_name, u.email, u.phone
            ORDER BY total_spent DESC  -- Сортировка по сумме потраченных денег (по убыванию)
            LIMIT ?
        """, (category, limit))

        results = []
        for row in cur.fetchall():
            purchased_products = row['purchased_products'].split(',')[:3] if row['purchased_products'] else []

            results.append({
                'user_id': row['user_id'],
                'name': f"{row['first_name']} {row['last_name']}",
                'email': row['email'],
                'phone': row['phone'],
                'orders_count': row['orders_count'],
                'total_quantity': row['total_quantity'],
                'total_spent': row['total_spent'],
                'purchased_products': purchased_products
            })
        return results

    except Exception as e:
        print(f"Error in get_category_lovers: {e}")
        return []

def get_all_categories(conn: sqlite3.Connection) -> List[str]:
    """
    Получить все категории товаров
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category")
        rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error in get_all_categories: {e}")
        return [
            "ПРОТЕИНЫ", "ВИТАМИНЫ И МИНЕРАЛЫ", "ПРЕДТРЕНИРОВОЧНЫЕ КОМПЛЕКСЫ",
            "ЖИРОСЖИГАТЕЛИ", "КРЕАТИН И АМИНОКИСЛОТЫ", "ГЕЙНЕРЫ",
            "ЭНЕРГЕТИЧЕСКИЕ БАТОНЧИКИ", "СПЕЦИАЛЬНЫЕ ДОБАВКИ", "ИЗОТОНИКИ И НАПИТКИ"
        ]

# Остальные функции остаются без изменений
def get_largest_order_info(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """
    Найти адрес доставки самого большого заказа и его владельца
    Работает только с заказами, которые есть в таблице user_order_address
    """
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                o.id as order_id,
                o.total_price,
                o.quantity,
                o.order_date,
                o.status,
                p.name as product_name,
                p.price as unit_price,
                p.category as product_category,
                p.weight as product_weight,  
                u.id as user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                uc.login as user_login,
                a.country,
                a.city,
                a.city_type,
                a.street_type,
                a.street,
                a.house_number,
                a.apartment
            FROM orders o
            JOIN user_order_address uoa ON o.id = uoa.order_id
            JOIN products p ON o.product_id = p.id
            JOIN users u ON uoa.user_id = u.id
            LEFT JOIN user_credentials uc ON u.id = uc.user_id
            LEFT JOIN addresses a ON uoa.address_id = a.id
            ORDER BY o.total_price DESC
            LIMIT 1
        """)

        result = cur.fetchone()
        if result:
            # Формируем полный адрес
            address_parts = []

            # Безопасное получение значений из результата
            country = result['country'] if 'country' in result.keys() and result['country'] else None
            city = result['city'] if 'city' in result.keys() and result['city'] else None
            city_type = result['city_type'] if 'city_type' in result.keys() and result['city_type'] else None
            street_type = result['street_type'] if 'street_type' in result.keys() and result['street_type'] else None
            street = result['street'] if 'street' in result.keys() and result['street'] else None
            house_number = result['house_number'] if 'house_number' in result.keys() and result['house_number'] else None
            apartment = result['apartment'] if 'apartment' in result.keys() and result['apartment'] else None

            if country:
                address_parts.append(country)
            if city:
                if city_type:
                    address_parts.append(f"{city_type} {city}")
                else:
                    address_parts.append(city)
            if street:
                if street_type:
                    address_parts.append(f"{street_type} {street}")
                else:
                    address_parts.append(street)
            if house_number:
                if apartment:
                    address_parts.append(f"д. {house_number}, кв. {apartment}")
                else:
                    address_parts.append(f"д. {house_number}")

            full_address = ", ".join(address_parts) if address_parts else "Адрес не указан"

            # Формируем информацию о клиенте
            first_name = result['first_name'] if 'first_name' in result.keys() and result['first_name'] else ""
            last_name = result['last_name'] if 'last_name' in result.keys() and result['last_name'] else ""
            customer_name = f"{first_name} {last_name}".strip()

            # Если имя пустое, пытаемся получить логин
            if not customer_name:
                login = result['user_login'] if 'user_login' in result.keys() and result['user_login'] else None
                if login:
                    customer_name = f"Пользователь ({login})"
                else:
                    customer_name = "Неизвестный клиент"

            # Рассчитываем общий вес заказа
            product_weight = result['product_weight'] if 'product_weight' in result.keys() else 0
            quantity = result['quantity']
            total_weight = product_weight * quantity

            # Полная информация о клиенте
            customer_info = {
                'user_id': result['user_id'] if 'user_id' in result.keys() and result['user_id'] else None,
                'name': customer_name,
                'email': result['email'] if 'email' in result.keys() and result['email'] else None,
                'phone': result['phone'] if 'phone' in result.keys() and result['phone'] else None,
                'login': result['user_login'] if 'user_login' in result.keys() and result['user_login'] else None
            }

            # Информация о товаре
            product_info = {
                'name': result['product_name'] if 'product_name' in result.keys() and result['product_name'] else 'Неизвестный товар',
                'category': result['product_category'] if 'product_category' in result.keys() and result['product_category'] else 'Неизвестная категория',
                'unit_price': result['unit_price'] if 'unit_price' in result.keys() else 0,
                'quantity': quantity,
                'weight': product_weight,
                'total_weight': total_weight
            }

            # Информация о заказе
            order_info = {
                'id': result['order_id'],
                'total_price': result['total_price'],
                'order_date': result['order_date'],
                'status': result['status'] if 'status' in result.keys() and result['status'] else 'Неизвестен'
            }

            return {
                'order': order_info,
                'product': product_info,
                'customer': customer_info,
                'delivery_address': full_address,
                'address_details': {
                    'country': country,
                    'city': city,
                    'city_type': city_type,
                    'street_type': street_type,
                    'street': street,
                    'house_number': house_number,
                    'apartment': apartment
                }
            }
        return None

    except Exception as e:
        print(f"Error in get_largest_order_info: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def user_exists(conn: sqlite3.Connection, user_id: str) -> bool:
    """
    Проверить существование пользователя
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        return cur.fetchone() is not None
    except Exception as e:
        print(f"Error in user_exists: {e}")
        return False

def get_user_favorite_product(conn: sqlite3.Connection, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Любимый товар пользователя (самый часто покупаемый товар)
    """
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                p.id,
                p.name,
                p.category,
                p.price,
                p.image,
                p.description,
                COUNT(o.id) as purchase_count,
                SUM(o.quantity) as total_quantity,
                SUM(o.total_price) as total_spent,
                MAX(o.order_date) as last_purchase_date
            FROM products p
            JOIN orders o ON p.id = o.product_id
            JOIN user_order_address uoa ON o.id = uoa.order_id
            WHERE uoa.user_id = ?
            GROUP BY p.id, p.name, p.category, p.price, p.image, p.description
            ORDER BY purchase_count DESC, total_spent DESC
            LIMIT 1
        """, (user_id,))

        result = cur.fetchone()
        if result:
            # Рассчитываем рейтинг популярности
            purchase_count = result['purchase_count']
            if purchase_count >= 10:
                popularity_rating = 5
            elif purchase_count >= 5:
                popularity_rating = 4
            elif purchase_count >= 3:
                popularity_rating = 3
            elif purchase_count >= 2:
                popularity_rating = 2
            else:
                popularity_rating = 1

            return {
                'product_id': result['id'],
                'name': result['name'],
                'category': result['category'],
                'price': result['price'],
                'image_url': result['image'] or '/static/images/placeholder-product.jpg',
                'description': result['description'],
                'purchase_count': purchase_count,
                'total_quantity': result['total_quantity'],
                'total_spent': result['total_spent'],
                'last_purchase_date': result['last_purchase_date'],
                'popularity_rating': popularity_rating
            }
        return None

    except Exception as e:
        print(f"Error in get_user_favorite_product: {e}")
        return None
