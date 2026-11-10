import sys
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMessageBox, QMenu, QFileDialog
from PyQt6.QtCore import Qt
from db.database import get_all_user_recipes, get_user_categories, search_user_recipes, create_category, \
    get_recipes_by_category, delete_category, delete_recipe, toggle_favorite, get_favorite_recipes
from ui.add_recipe import AddRecipeWindow
from ui.view_recipe import ViewRecipeWindow
from paths import get_base_path

base_path = get_base_path()
ui_path = base_path / "ui" / "main_window.ui"


class MainWindow(QMainWindow):
    def __init__(self, user_id: int):
        super().__init__()
        self.view_window = None
        self.add_window = None
        uic.loadUi(ui_path, self)
        self.user_id = user_id

        self.add_recipe_button.clicked.connect(self.handle_add_recipe)
        self.recipes_list.itemClicked.connect(self.handle_recipe_click)
        self.search_input.textChanged.connect(self.handle_search)
        self.add_category_button.clicked.connect(self.handle_add_category)
        self.categories_list.itemClicked.connect(self.handle_category_click)
        self.action_exit.triggered.connect(self.close)
        self.action_about.triggered.connect(self.show_about_dialog)
        self.categories_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.categories_list.customContextMenuRequested.connect(self.show_category_context_menu)
        self.recipes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recipes_list.customContextMenuRequested.connect(self.show_recipe_context_menu)
        self.txt_import_button.clicked.connect(self.handle_import_from_txt)

        self.load_categories()
        self.load_recipes()

    def load_categories(self) -> None:
        """Заполняет левый список категориями из БД"""

        self.categories_list.clear()

        all_item = QListWidgetItem("Все рецепты")
        self.categories_list.addItem(all_item)

        fav_item = QListWidgetItem("Избранное")
        fav_item.setData(Qt.ItemDataRole.UserRole, "favorites")
        self.categories_list.addItem(fav_item)

        categories = get_user_categories(self.user_id)
        for row in categories:
            item = QListWidgetItem(row['name'])
            item.setData(Qt.ItemDataRole.UserRole, row['id'])
            self.categories_list.addItem(item)

    def load_recipes(self) -> None:
        """Заполняет правый список рецептами из БД"""

        self.recipes_list.clear()

        recipes = get_all_user_recipes(self.user_id)

        if not recipes:
            self.recipes_list.addItem("У вас пока нет рецептов...")
            return None

        for row in recipes:
            item = QListWidgetItem(row['recipe_name'])
            item.setData(Qt.ItemDataRole.UserRole, row['id'])
            self.recipes_list.addItem(item)

    def handle_add_recipe(self) -> None:
        self.add_window = AddRecipeWindow(self.user_id, self)
        self.add_window.show()

    def handle_recipe_click(self, item) -> None:
        """Открывает окно просмотра выбранного рецепта"""

        recipe_id = item.data(Qt.ItemDataRole.UserRole)

        if recipe_id is not None:
            self.view_window = ViewRecipeWindow(recipe_id)
            self.view_window.show()

    def handle_search(self, text: str) -> None:
        """Фильтрует список рецептов при вводе текста"""

        self.recipes_list.clear()

        if text.strip():
            recipes = search_user_recipes(self.user_id, text)
        else:
            recipes = get_all_user_recipes(self.user_id)

        for row in recipes:
            item = QListWidgetItem(row['recipe_name'])
            item.setData(Qt.ItemDataRole.UserRole, row['id'])
            self.recipes_list.addItem(item)

    def handle_add_category(self) -> None:
        """Создает новую категорию и обновляет список слева"""

        name = self.new_category_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название категории")
            return

        success = create_category(self.user_id, name)

        if success:
            self.new_category_input.clear()
            self.load_categories()
        else:
            QMessageBox.warning(self, "Ошибка", "Такая категория уже существует")

    def handle_category_click(self, item) -> None:
        """Фильтрует рецепты при клике на категорию слева"""

        category_id = item.data(Qt.ItemDataRole.UserRole)
        self.recipes_list.clear()

        if category_id is None:
            recipes = get_all_user_recipes(self.user_id)
        elif category_id == "favorites":
            recipes = get_favorite_recipes(self.user_id)
        else:
            recipes = get_recipes_by_category(self.user_id, category_id)

        for row in recipes:
            recipe_item = QListWidgetItem(row['recipe_name'])
            recipe_item.setData(Qt.ItemDataRole.UserRole, row['id'])
            self.recipes_list.addItem(recipe_item)

    def show_about_dialog(self) -> None:
        """Показывает окно 'О программе'"""

        about_text = (
            "<h3>Recipe Vault</h3>"
            "<p>Десктопное приложение для хранения, систематизации и экспорта рецептов.</p>"
            "<p><b>Автор:</b> Максим Дука</p>"
        )
        QMessageBox.about(self, "О программе", about_text)

    def show_category_context_menu(self, pos) -> None:
        """Показывает меню при клике правой кнопкой мыши на категорию"""

        item = self.categories_list.itemAt(pos)

        if item is None or item.data(Qt.ItemDataRole.UserRole) is None or item.data(
                Qt.ItemDataRole.UserRole) == 'favorite':
            return

        menu = QMenu(self)
        delete_action = menu.addAction("Удалить категорию")

        action = menu.exec(self.categories_list.mapToGlobal(pos))

        if action == delete_action:
            self.handle_delete_category(item)

    def handle_delete_category(self, item) -> None:
        """Удаляет выбранную категорию"""

        category_id = item.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить категорию '{item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            delete_category(self.user_id, category_id)
            self.load_categories()
            self.load_recipes()

    def handle_import_from_txt(self) -> None:
        """Выбирает TXT файл и открывает окно добавления с уже заполненными данными"""

        from services.txt_import import parse_txt_recipe

        file_path, _ = QFileDialog.getOpenFileName(self, "Импорт рецепта", "", "Text Files (*.txt)")
        if not file_path:
            return

        data = parse_txt_recipe(file_path)
        if not data:
            QMessageBox.warning(self, "Ошибка", "Неверный формат файла.")
            return

        self.add_window = AddRecipeWindow(self.user_id, self, import_data=data)
        self.add_window.show()

    def show_recipe_context_menu(self, pos) -> None:
        """Показывает меню при клике правой кнопкой мыши на рецепт"""

        item = self.recipes_list.itemAt(pos)

        if item is None or item.data(Qt.ItemDataRole.UserRole) is None:
            return

        menu = QMenu(self)
        favorite_action = menu.addAction("В избранное / Убрать")
        delete_action = menu.addAction("Удалить рецепт")

        action = menu.exec(self.recipes_list.mapToGlobal(pos))

        if action == favorite_action:
            self.handle_toggle_favorite(item)
        elif action == delete_action:
            self.handle_delete_recipe(item)

    def handle_delete_recipe(self, item) -> None:
        """Удаляет рецепт через контекстное меню"""

        recipe_id = item.data(Qt.ItemDataRole.UserRole)
        recipe_name = item.text()

        reply = QMessageBox.question(
            self, "Удаление рецепта",
            f"Вы уверены, что хотите удалить рецепт '{recipe_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            delete_recipe(recipe_id)
            self.load_recipes()

    def handle_toggle_favorite(self, item) -> None:
        """Добавляет или удаляет рецепт из избранного через ПКМ"""
        recipe_id = item.data(Qt.ItemDataRole.UserRole)

        toggle_favorite(self.user_id, recipe_id)

        current_category = self.categories_list.currentItem()
        if current_category:
            self.handle_category_click(current_category)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow(user_id=1)
    ex.show()
    sys.exit(app.exec())
