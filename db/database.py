import sqlite3
from pathlib import Path
from config import DEFAULT_CATEGORIES
import sys


if getattr(sys, 'frozen', False):
    db_path = Path(sys.executable).parent / 'recipe_vault.db'
else:
    db_path = Path(__file__).parent / 'recipe_vault.db'


def get_connection() -> sqlite3.Connection:
    """Открывает/создает файл базы данных и возвращает объект подключения"""

    connect = sqlite3.connect(db_path)
    connect.row_factory = sqlite3.Row
    connect.execute("PRAGMA foreign_keys = ON")
    return connect


def init_db() -> None:
    """Создает таблицы в базе данных"""

    connect = get_connection()
    try:
        cursor = connect.cursor()
        cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        date_time TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipe_name TEXT NOT NULL,
        description TEXT,
        path_to_image TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        ingredient_name TEXT NOT NULL,
        amount TEXT,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        order_num INTEGER NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        UNIQUE (recipe_id, order_num)
        );

        CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE (user_id, name)
        );

        CREATE TABLE IF NOT EXISTS recipes_categories(
        category_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
        PRIMARY KEY (category_id, recipe_id)
        );

        CREATE TABLE IF NOT EXISTS favorites(
        user_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
        PRIMARY KEY (user_id, recipe_id)
        );
        ''')

    finally:
        connect.close()


def create_user(login: str, password_hash: str, salt: str) -> int:
    """Добавляет пользователя и его зашифрованный пароль с солью в базу данных. Возвращает id добавленного
    пользователя"""

    connect = get_connection()
    try:
        cursor = connect.cursor()
        cursor.execute(
            'INSERT INTO users (login, password_hash, salt) VALUES (?, ?, ?)',
            (login, password_hash, salt)
        )
        last_id = cursor.lastrowid
        connect.commit()
        return last_id

    finally:
        connect.close()


def delete_user(user_id: int) -> None:
    """Удаляет пользователя из базы данных"""

    connect = get_connection()
    try:
        connect.execute('DELETE FROM users WHERE id = ?', (user_id,))
        connect.commit()
    finally:
        connect.close()


def delete_recipe(recipe_id: int) -> None:
    """Удаляет рецепт"""

    connect = get_connection()
    try:
        connect.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        connect.commit()
    finally:
        connect.close()


def create_default_categories(user_id: int) -> None:
    """Добавляет начальные категории пользователю по id"""

    connect = get_connection()
    try:
        data = [(user_id, category) for category in DEFAULT_CATEGORIES]
        connect.executemany('INSERT INTO categories (user_id, name) VALUES (?, ?)', data)
        connect.commit()
    finally:
        connect.close()


def create_category(user_id: int, name: str) -> bool:
    """Создает новую категорию. Возвращает True при успехе, False если такая уже есть."""

    connect = get_connection()
    try:
        connect.execute(
            'INSERT INTO categories (user_id, name) VALUES (?, ?)',
            (user_id, name)
        )
        connect.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        connect.close()


def get_user_by_login(login: str) -> sqlite3.Row | None:
    """Возвразает информацию о пользователе из таблицы users"""

    connect = get_connection()
    try:
        user = connect.execute('SELECT * FROM users WHERE login = ?', (login,)).fetchone()
        return user
    finally:
        connect.close()


def create_recipe(user_id: int, recipe_name: str, description: str, path_to_image: str) -> int | None:
    """Добавляет рецепт в базу данных и возвращает его id"""

    connect = get_connection()
    try:
        cursor = connect.cursor()
        cursor.execute('INSERT INTO recipes (user_id, recipe_name, description, path_to_image) VALUES (?, ?, ?, ?)',
                       (user_id, recipe_name, description, path_to_image)
                       )
        last_id = cursor.lastrowid
        connect.commit()
        return last_id
    finally:
        connect.close()


def add_ingredients(recipe_id: int, ingredients: list[tuple[str, str]]) -> None:
    """Добавляет ингредиенты в таблицу ingredients и прикрепляет внешним ключом к таблице recipes"""

    connect = get_connection()
    try:
        data = [(recipe_id, ingredient, amount) for ingredient, amount in ingredients]
        connect.executemany('INSERT INTO ingredients (recipe_id, ingredient_name, amount) VALUES (?, ?, ?)', data)
        connect.commit()
    finally:
        connect.close()


def add_steps(recipe_id: int, steps: list[str]) -> None:
    """Добавляет шаги приготовления в таблицу steps и прикрепляет внешним ключом к таблице recipes"""

    connect = get_connection()
    try:
        data = [(recipe_id, order_num + 1, step) for order_num, step in enumerate(steps)]
        connect.executemany('INSERT INTO steps (recipe_id, order_num, text) VALUES (?, ?, ?)', data)
        connect.commit()
    finally:
        connect.close()


def get_recipe_by_id(recipe_id: int) -> dict | None:
    """Возвращает словарь рецепта"""

    connect = get_connection()
    try:
        recipe_row = connect.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
        if recipe_row is None:
            return None
        recipe = dict(recipe_row)

        ingredients_rows = connect.execute(
            'SELECT ingredient_name, amount FROM ingredients WHERE recipe_id = ? ORDER BY id', (recipe_id,)).fetchall()
        recipe['ingredients'] = [(row['ingredient_name'], row['amount']) for row in ingredients_rows]

        steps_rows = connect.execute(
            'SELECT text FROM steps WHERE recipe_id = ? ORDER BY order_num', (recipe_id,)).fetchall()
        recipe['steps'] = [row['text'] for row in steps_rows]

        return recipe
    finally:
        connect.close()


def get_all_user_recipes(user_id: int) -> list[sqlite3.Row]:
    """Возвращает список всех рецептов пользователя"""

    connect = get_connection()
    try:
        recipes = connect.execute(
            'SELECT id, recipe_name FROM recipes WHERE user_id = ? ORDER BY id DESC',
            (user_id,)
        ).fetchall()
        return recipes
    finally:
        connect.close()


def get_user_categories(user_id: int) -> list[sqlite3.Row]:
    """Возвращает список категорий пользователя"""

    connect = get_connection()
    try:
        categories = connect.execute(
            'SELECT id, name FROM categories WHERE user_id = ? ORDER BY name',
            (user_id,)
        ).fetchall()
        return categories
    finally:
        connect.close()


def update_recipe(recipe_id: int, recipe_name: str, description: str, path_to_image: str) -> None:
    """Обновляет основную информацию о рецепте"""

    connect = get_connection()
    try:
        connect.execute(
            'UPDATE recipes SET recipe_name = ?, description = ?, path_to_image = ? WHERE id = ?',
            (recipe_name, description, path_to_image, recipe_id)
        )
        connect.commit()
    finally:
        connect.close()


def clear_recipe_details(recipe_id: int) -> None:
    """Удаляет старые ингредиенты и шаги перед их повторной записью"""

    connect = get_connection()
    try:
        connect.execute('DELETE FROM ingredients WHERE recipe_id = ?', (recipe_id,))
        connect.execute('DELETE FROM steps WHERE recipe_id = ?', (recipe_id,))
        connect.commit()
    finally:
        connect.close()


def search_user_recipes(user_id: int, query: str) -> list[sqlite3.Row]:
    """Ищет рецепты пользователя по названию"""

    connect = get_connection()
    try:
        recipes = connect.execute(
            'SELECT id, recipe_name FROM recipes WHERE user_id = ? AND recipe_name LIKE ? ORDER BY id DESC',
            (user_id, f"%{query}%")
        ).fetchall()
        return recipes
    finally:
        connect.close()


def get_recipes_by_category(user_id: int, category_id: int) -> list[sqlite3.Row]:
    """Возвращает рецепты конкретной категории"""

    connect = get_connection()
    try:
        recipes = connect.execute('''
            SELECT recipes.id, recipes.recipe_name 
            FROM recipes 
            JOIN recipes_categories ON recipes.id = recipes_categories.recipe_id
            WHERE recipes.user_id = ? AND recipes_categories.category_id = ?
            ORDER BY recipes.id DESC
        ''', (user_id, category_id)).fetchall()
        return recipes
    finally:
        connect.close()


def get_recipe_categories(recipe_id: int) -> list[sqlite3.Row]:
    """Возвращает категории рецепта"""

    connect = get_connection()
    try:
        categories = connect.execute('''
            SELECT categories.id, categories.name 
            FROM categories 
            JOIN recipes_categories ON categories.id = recipes_categories.category_id
            WHERE recipes_categories.recipe_id = ?
        ''', (recipe_id,)).fetchall()
        return categories
    finally:
        connect.close()


def add_category_to_recipe(recipe_id: int, category_id: int) -> None:
    """Привязывает категорию к рецепту. Если связь уже есть ничего не делает."""

    connect = get_connection()
    try:
        connect.execute(
            'INSERT OR IGNORE INTO recipes_categories (recipe_id, category_id) VALUES (?, ?)',
            (recipe_id, category_id)
        )
        connect.commit()
    finally:
        connect.close()


def delete_category(user_id: int, category_id: int) -> None:
    """Удаляет категорию пользователя"""

    connect = get_connection()
    try:
        connect.execute(
            'DELETE FROM categories WHERE id = ? AND user_id = ?',
            (category_id, user_id)
        )
        connect.commit()
    finally:
        connect.close()


def toggle_favorite(user_id: int, recipe_id: int) -> bool:
    """Добавляет или удаляет рецепт из избранного. Возвращает True, если рецепт добавлен."""
    connect = get_connection()
    try:
        exists = connect.execute(
            'SELECT 1 FROM favorites WHERE user_id = ? AND recipe_id = ?',
            (user_id, recipe_id)
        ).fetchone()

        if exists:
            connect.execute('DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?', (user_id, recipe_id))
            connect.commit()
            return False
        else:
            connect.execute('INSERT INTO favorites (user_id, recipe_id) VALUES (?, ?)', (user_id, recipe_id))
            connect.commit()
            return True
    finally:
        connect.close()


def get_favorite_recipes(user_id: int) -> list[sqlite3.Row]:
    """Возвращает список избранных рецептов пользователя"""
    connect = get_connection()
    try:
        recipes = connect.execute('''
            SELECT recipes.id, recipes.recipe_name 
            FROM recipes 
            JOIN favorites ON recipes.id = favorites.recipe_id
            WHERE favorites.user_id = ? 
            ORDER BY recipes.id DESC
        ''', (user_id,)).fetchall()
        return recipes
    finally:
        connect.close()
