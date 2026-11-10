import sys
from pathlib import Path
from PyQt6 import uic
from ui.add_recipe import AddRecipeWindow
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from db.database import get_recipe_by_id, toggle_favorite
from services.pdf_export import export_recipe_to_pdf
from paths import get_base_path

base_path = get_base_path()
ui_path = base_path / "ui" / "view_recipe.ui"


class ViewRecipeWindow(QWidget):
    def __init__(self, recipe_id: int):
        super().__init__()
        uic.loadUi(ui_path, self)

        self.recipe_id = recipe_id
        self.recipe_data = None
        self.edit_window = None

        self.edit_button.clicked.connect(self.handle_edit)
        self.export_button.clicked.connect(self.handle_export)

        self.load_recipe_data()

    def load_recipe_data(self) -> None:
        """Загружает полный рецепт из базы данных и заполняет интерфейс"""

        recipe = get_recipe_by_id(self.recipe_id)

        if recipe is None:
            QMessageBox.warning(self, "Ошибка", "Рецепт не найден")
            self.close()
            return

        self.recipe_data = recipe

        self.title_label.setText(recipe['recipe_name'])

        description = recipe['description'] if recipe['description'] else "Без описания"
        self.description_label.setText(description)

        if recipe['path_to_image']:
            img_path = Path(__file__).parent.parent / recipe['path_to_image']
            if img_path.exists():
                pixmap = QPixmap(str(img_path))
                self.image_label.setPixmap(pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio,
                                                         Qt.TransformationMode.SmoothTransformation))
            else:
                self.image_label.setText("Фото не найдено")
        else:
            self.image_label.setText("Нет фото")

        self.ingredients_list.clear()
        for ing_name, ing_amount in recipe['ingredients']:
            if ing_amount:
                self.ingredients_list.addItem(f"{ing_name} — {ing_amount}")
            else:
                self.ingredients_list.addItem(ing_name)

        self.steps_list.clear()
        for i, step_text in enumerate(recipe['steps'], start=1):
            self.steps_list.addItem(f"{i}. {step_text}")

    def handle_edit(self) -> None:
        """Открывает окно редактирования"""

        self.edit_window = AddRecipeWindow(self.recipe_data['user_id'], None, self.recipe_id)
        self.edit_window.show()
        self.close()

    def handle_export(self) -> None:
        """Экспортирует в pdf рецепт"""

        if not self.recipe_data:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить PDF", f"{self.recipe_data['recipe_name']}.pdf", "PDF Files (*.pdf)"
        )

        if file_path:
            export_recipe_to_pdf(self.recipe_data, file_path)

    def handle_favorite(self) -> None:
        """Добавляет или удаляет рецепт из избранного"""

        toggle_favorite(self.recipe_data['user_id'], self.recipe_id)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ViewRecipeWindow(recipe_id=1)
    ex.show()
    sys.exit(app.exec())
