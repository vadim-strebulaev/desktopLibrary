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
        self.setFixedSize(400, 340)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(12)

        title = QLabel("Цифровая Библиотека")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        layout.addWidget(self.login_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self.on_login)
        layout.addWidget(self.password_edit)

        btn_login = QPushButton("Войти")
        btn_login.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        btn_login.clicked.connect(self.on_login)
        layout.addWidget(btn_login)

        layout.addWidget(QLabel(""))

        btn_register = QPushButton("Зарегистрироваться")
        btn_register.setStyleSheet("background-color: #2196F3; color: white;")
        btn_register.clicked.connect(self.open_register)
        layout.addWidget(btn_register)

        self.setLayout(layout)

    def on_login(self):
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
            self.next_window = AdminWindow(user)
        else:
            from main_window import MainWindow
            self.next_window = MainWindow(user)

        self.next_window.show()
        self.close()

    def open_register(self):
        self.reg_window = RegisterWindow()
        self.reg_window.show()


class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация читателя")
        self.setFixedSize(400, 380)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(10)

        title = QLabel("Регистрация читателя")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("ФИО")
        layout.addWidget(self.fullname_edit)

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Логин")
        layout.addWidget(self.login_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль (минимум 4 символа)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setPlaceholderText("Подтвердите пароль")
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_edit)

        self.card_edit = QLineEdit()
        self.card_edit.setPlaceholderText("Номер читательского билета")
        layout.addWidget(self.card_edit)

        btn = QPushButton("Зарегистрироваться")
        btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        btn.clicked.connect(self.on_register)
        layout.addWidget(btn)

        self.setLayout(layout)

    def on_register(self):
        full_name   = self.fullname_edit.text().strip()
        login_name  = self.login_edit.text().strip()
        password    = self.password_edit.text()
        confirm     = self.confirm_edit.text()
        reader_card = self.card_edit.text().strip()

        if not full_name or not login_name or not password or not reader_card:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return

        if len(password) < 4:
            QMessageBox.warning(self, "Ошибка", "Пароль слишком короткий (минимум 4 символа).")
            return

        ok, msg = db.register(full_name, login_name, password, reader_card)
        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", msg)
