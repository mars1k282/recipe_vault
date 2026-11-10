import hashlib
import hmac
import secrets
from db.database import get_user_by_login, create_user, create_default_categories

from config import PBKDF2_ITERATIONS


def hash_password(password: str) -> tuple[str, str]:
    """Генерирует соль и хэширует пароль. Возвращает соль и хэшированный пароль"""

    salt_bytes = secrets.token_bytes(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, PBKDF2_ITERATIONS)

    return salt_bytes.hex(), hash_bytes.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Проверяет пароль. Возвращает True если пароль верный в и False если нет"""

    salt_bytes = bytes.fromhex(salt_hex)
    hash_bytes_to_compare = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, PBKDF2_ITERATIONS)

    hash_hex_to_compare = hash_bytes_to_compare.hex()
    return hmac.compare_digest(hash_hex_to_compare, hash_hex)


def authenticate_user(login: str, password: str) -> tuple[int | None, str | None]:
    """Проверяет логин и пароль. Возвращает (user_id, None) при успехе, или (None, 'текст ошибки') при неудаче."""

    if not login or not password:
        return None, 'Логин и пароль не могут быть пустыми'

    try:
        user = get_user_by_login(login)
        if user is None:
            return None, 'Неверный логин или пароль'

        if verify_password(password, user['salt'], user['password_hash']):
            return user['id'], None

        return None, 'Неверный логин или пароль'

    except Exception as e:
        return None, f'Ошибка кода: {e}'


def register_user(login: str, password: str) -> tuple[int | None, str | None]:
    """Проверяет нет ли логина в users, если нет - возвращает (user_id, None) и
    заполняет таблицы, если есть - возвращает (None, 'текст ошибки')"""

    if not login or not password:
        return None, 'Логин и пароль не могут быть пустыми'

    try:
        user = get_user_by_login(login)
        if user is None:
            salt, hash_pass = hash_password(password)
            user_id = create_user(login, hash_pass, salt)
            create_default_categories(user_id)
            return user_id, None

        else:
            return None, "Пользователь с таким логином уже существует"

    except Exception as e:
        return None, f'Ошибка кода: {e}'
