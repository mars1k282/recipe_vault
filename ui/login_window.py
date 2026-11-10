import sys
from pathlib import Path
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox
from services.auth import authenticate_user, register_user
from ui.main_window import MainWindow
from paths import get_base_path

base_path = get_base_path()
ui_path = base_path / "ui" / "auth_register.ui"


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.main_window = None
        uic.loadUi(ui_path, self)

        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.handle_register)

    def handle_login(self) -> None:
        """То что происходит при нажатии кнопки 'Войти'"""

        login = self.login_input.text()
        password = self.password_input.text()
        user_id, error = authenticate_user(login, password)

        if error:
            QMessageBox.warning(self, "Ошибка входа", error)
        else:
            self.main_window = MainWindow(user_id)
            self.main_window.show()
            self.close()

    def handle_register(self) -> None:
        """То что происходит при нажатии кнопки 'Зарегестрироваться'"""

        login = self.login_input.text()
        password = self.password_input.text()
        user_id, error = register_user(login, password)

        if error:
            QMessageBox.warning(self, "Ошибка регистрации", error)
        else:
            self.main_window = MainWindow(user_id)
            self.main_window.show()
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec())
