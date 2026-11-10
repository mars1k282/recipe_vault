import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from db.database import init_db
from ui.login_window import MyWidget


def main() -> None:
    init_db()
    app = QApplication(sys.argv)

    style_path = Path(__file__).parent / "ui" / "style.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = MyWidget()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
