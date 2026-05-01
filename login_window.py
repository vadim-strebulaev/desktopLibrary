from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database as db


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Цифровая Библиотека — Вход")
        self.setFixedSize(420, 360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(14)

        title = QLabel("📚 Цифровая Библиотека")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Вход в систему")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray; font-size: 13px;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        self.login_edit.setMinimumHeight(36)
        layout.addWidget(self.login_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumHeight(36)
        self.password_edit.returnPressed.connect(self._on_login)
        layout.addWidget(self.password_edit)

        btn_login = QPushButton("Войти")
        btn_login.setMinimumHeight(40)
        btn_login.setStyleSheet(
            "background-color: #4CAF50; color: white; "
            "font-size: 14px; border-radius: 5px;"
        )
        btn_login.clicked.connect(self._on_login)
        layout.addWidget(btn_login)

        sep = QLabel("— или —")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep.setStyleSheet("color: gray;")
        layout.addWidget(sep)

        btn_register = QPushButton("Зарегистрироваться")
        btn_register.setMinimumHeight(36)
        btn_register.setStyleSheet(
            "background-color: #2196F3; color: white; "
            "font-size: 13px; border-radius: 5px;"
        )
        btn_register.clicked.connect(self._open_register)
        layout.addWidget(btn_register)

        self.setLayout(layout)

    def _on_login(self):
        username = self.login_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль.")
            return

        user = db.login(username, password)
        if not user:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")
            return

        if user["is_admin"]:
            from admin_window import AdminWindow
            self._next = AdminWindow(user)
        else:
            from main_window import MainWindow
            self._next = MainWindow(user)

        self._next.show()
        self.close()

    def _open_register(self):
        self._reg = RegisterWindow()
        self._reg.show()


class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация читателя")
        self.setFixedSize(420, 420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(12)

        title = QLabel("Регистрация читателя")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(6)

        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("ФИО")
        self.fullname_edit.setMinimumHeight(36)
        layout.addWidget(self.fullname_edit)

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        self.login_edit.setMinimumHeight(36)
        layout.addWidget(self.login_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль (минимум 4 символа)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumHeight(36)
        layout.addWidget(self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText("Подтвердите пароль")
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setMinimumHeight(36)
        layout.addWidget(self.confirm_edit)

        self.card_edit = QLineEdit()
        self.card_edit.setPlaceholderText("Номер читательского билета")
        self.card_edit.setMinimumHeight(36)
        layout.addWidget(self.card_edit)

        btn = QPushButton("Зарегистрироваться")
        btn.setMinimumHeight(40)
        btn.setStyleSheet(
            "background-color: #4CAF50; color: white; "
            "font-size: 14px; border-radius: 5px;"
        )
        btn.clicked.connect(self._on_register)
        layout.addWidget(btn)

        self.setLayout(layout)

    def _on_register(self):
        full_name   = self.fullname_edit.text().strip()
        login_name  = self.login_edit.text().strip()
        password    = self.password_edit.text()
        confirm     = self.confirm_edit.text()
        reader_card = self.card_edit.text().strip()

        if not all([full_name, login_name, password, reader_card]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return

        if len(password) < 4:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 4 символа.")
            return

        ok, msg = db.register(full_name, login_name, password, reader_card)
        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", msg)
