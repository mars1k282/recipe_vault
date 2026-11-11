from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from paths import get_base_path
import sys

base_path = get_base_path()
font_path = base_path / "assets" / "arial.ttf"


def export_recipe_to_pdf(recipe: dict, output_path: str) -> bool:
    """Генерирует PDF-файл с рецептом и сохраняет его по указанному пути."""

    try:
        pdfmetrics.registerFont(TTFont('CustomFont', font_path))

        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        y = height - 50

        def draw_wrapped_text(text: str, x: int, y_pos: int, max_width: int, font_size: int = 12) -> int:
            """Рисует текст с автоматическим переносом строк, возвращает новую координату Y."""

            c.setFont('CustomFont', font_size)
            words = text.split(' ')
            line = ""

            for word in words:
                if c.stringWidth(line + word + " ", 'CustomFont', font_size) < max_width:
                    line += word + " "
                else:
                    c.drawString(x, y_pos, line)
                    y_pos -= 20
                    line = word + " "

            if line:
                c.drawString(x, y_pos, line)
                y_pos -= 20

            return y_pos

        c.setFont('CustomFont', 22)
        c.drawString(50, y, recipe['recipe_name'])
        y -= 40

        if recipe.get('path_to_image'):
            if getattr(sys, 'frozen', False):
                img_path = Path(sys.executable).parent / recipe['path_to_image']
            else:
                img_path = Path(__file__).parent.parent / recipe['path_to_image']

            if img_path.exists():
                img = ImageReader(str(img_path))
                c.drawImage(img, 350, y - 250, width=200, height=250, preserveAspectRatio=True)

        c.setFont('CustomFont', 12)
        c.drawString(50, y, "Описание:")
        y -= 20

        description = recipe['description'] if recipe['description'] else "Без описания"
        y = draw_wrapped_text(description, 60, y, 280)
        y -= 20

        c.setFont('CustomFont', 14)
        c.drawString(50, y, "Ингредиенты:")
        y -= 20

        for ing_name, ing_amount in recipe['ingredients']:
            text = f"• {ing_name} — {ing_amount}" if ing_amount else f"• {ing_name}"
            y = draw_wrapped_text(text, 60, y, 280)

        y -= 20

        c.setFont('CustomFont', 14)
        c.drawString(50, y, "Шаги приготовления:")
        y -= 20

        for i, step in enumerate(recipe['steps'], start=1):
            text = f"{i}. {step}"
            y = draw_wrapped_text(text, 60, y, 280)

            if y < 50:
                c.showPage()
                y = height - 50

        c.save()
        return True

    except Exception as e:
        print(e)
        return False
