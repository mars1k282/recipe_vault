import sys
import shutil
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog
from db.database import (create_recipe, add_ingredients, add_steps, get_recipe_by_id,
                         update_recipe, clear_recipe_details, get_user_categories, add_category_to_recipe,
                         get_connection)
from paths import get_base_path

base_path = get_base_path()
ui_path = base_path / "ui" / "add_recipe.ui"


class AddRecipeWindow(QWidget):
    def __init__(self, user_id: int, main_window, recipe_id: int = None, import_data: dict = None):
        super().__init__()
        uic.loadUi(ui_path, self)

        self.user_id = user_id
        self.main_window = main_window
        self.recipe_id = recipe_id
        self.image_path = ""
        self.temp_ingredients = []
        self.temp_steps = []

        self.add_ingredient_button.clicked.connect(self.handle_add_ingredient)
        self.remove_ingredient_button.clicked.connect(self.handle_remove_ingredient)
        self.add_step_button.clicked.connect(self.handle_add_step)
        self.remove_step_button.clicked.connect(self.handle_remove_step)
        self.save_recipe_button.clicked.connect(self.handle_save)
        self.select_image_button.clicked.connect(self.handle_select_image)

        self.category_combo.clear()
        self.category_combo.addItem("Без категории", None)
        for cat in get_user_categories(self.user_id):
            self.category_combo.addItem(cat['name'], cat['id'])

        if self.recipe_id is not None:
            self.load_recipe_for_edit()
        elif import_data is not None:
            self.fill_from_import(import_data)

    def handle_add_ingredient(self) -> None:
        text = self.ingredient_input.text().strip()
        if text:
            self.temp_ingredients.append(text)
            self.ingredients_list.addItem(text)
            self.ingredient_input.clear()

    def handle_remove_ingredient(self) -> None:
        current_row = self.ingredients_list.currentRow()
        if current_row >= 0:
            self.ingredients_list.takeItem(current_row)
            self.temp_ingredients.pop(current_row)

    def handle_add_step(self) -> None:
        text = self.step_input.text().strip()
        if text:
            self.temp_steps.append(text)
            step_num = len(self.temp_steps)
            self.steps_list.addItem(f"{step_num}. {text}")
            self.step_input.clear()

    def handle_remove_step(self) -> None:
        current_row = self.steps_list.currentRow()
        if current_row >= 0:
            self.steps_list.takeItem(current_row)
            self.temp_steps.pop(current_row)

            self.steps_list.clear()
            for i, step in enumerate(self.temp_steps, start=1):
                self.steps_list.addItem(f"{i}. {step}")

    def handle_save(self) -> None:
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название рецепта")
            return

        if not self.temp_ingredients or not self.temp_steps:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один ингредиент и один шаг")
            return

        formatted_ing = [(item, "") for item in self.temp_ingredients]
        cat_id = self.category_combo.currentData()

        if self.recipe_id is None:
            new_id = create_recipe(self.user_id, name, description, self.image_path)
            if new_id:
                add_ingredients(new_id, formatted_ing)
                add_steps(new_id, self.temp_steps)

                if cat_id is not None:
                    add_category_to_recipe(new_id, cat_id)

                if self.main_window:
                    self.main_window.load_recipes()
                self.close()
        else:
            update_recipe(self.recipe_id, name, description, self.image_path)
            clear_recipe_details(self.recipe_id)
            add_ingredients(self.recipe_id, formatted_ing)
            add_steps(self.recipe_id, self.temp_steps)

            connect = get_connection()
            try:
                connect.execute('DELETE FROM recipes_categories WHERE recipe_id = ?', (self.recipe_id,))
                connect.commit()
            finally:
                connect.close()

            if cat_id is not None:
                add_category_to_recipe(self.recipe_id, cat_id)

            self.close()

    def handle_select_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать фото", "", "Images (*.png *.jpg *.jpeg)")

        if file_path:
            assets_dir = Path(__file__).parent.parent / "assets" / "images"
            assets_dir.mkdir(parents=True, exist_ok=True)
            filename = Path(file_path).name
            new_path = assets_dir / filename

            shutil.copy(file_path, new_path)

            self.image_path = f"assets/images/{filename}"

            pixmap = QPixmap(str(new_path))
            self.image_preview.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))

    def load_recipe_for_edit(self) -> None:
        recipe = get_recipe_by_id(self.recipe_id)
        if not recipe:
            return

        self.name_input.setText(recipe['recipe_name'])
        self.description_input.setText(recipe['description'] or "")
        self.image_path = recipe['path_to_image'] or ""

        if self.image_path:
            img_path = Path(__file__).parent.parent / self.image_path
            if img_path.exists():
                pixmap = QPixmap(str(img_path))
                self.image_preview.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))

        self.ingredients_list.clear()
        for ing_name, ing_amount in recipe['ingredients']:
            text = f"{ing_name} {ing_amount}".strip()
            self.temp_ingredients.append(text)
            self.ingredients_list.addItem(text)

        self.steps_list.clear()
        for i, step in enumerate(recipe['steps'], start=1):
            self.temp_steps.append(step)
            self.steps_list.addItem(f"{i}. {step}")

        from db.database import get_recipe_categories
        recipe_cats = get_recipe_categories(self.recipe_id)
        if recipe_cats:
            cat_id = recipe_cats[0]['id']
            index = self.category_combo.findData(cat_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def fill_from_import(self, data: dict) -> None:
        """Заполняет поля данными, полученными из txt парсера"""

        self.name_input.setText(data['name'])
        self.description_input.setText(data['description'])

        self.ingredients_list.clear()
        self.temp_ingredients.clear()
        for ing in data['ingredients']:
            self.temp_ingredients.append(ing)
            self.ingredients_list.addItem(ing)

        self.steps_list.clear()
        self.temp_steps.clear()
        for i, step in enumerate(data['steps'], start=1):
            self.temp_steps.append(step)
            self.steps_list.addItem(f"{i}. {step}")

        if data['category']:
            index = self.category_combo.findText(data['category'], Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AddRecipeWindow(1, None)
    ex.show()
    sys.exit(app.exec())
