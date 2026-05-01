from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QMessageBox,
    QDialogButtonBox, QHeaderView,
)
from PyQt6.QtGui import QFont

import database as db


class AdminWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("Администратор — Цифровая Библиотека")
        self.setMinimumSize(960, 620)

        self.books_tab    = AdminBooksTab()
        self.users_tab    = AdminUsersTab()
        self.requests_tab = AdminRequestsTab()

        tabs = QTabWidget()
        tabs.addTab(self.books_tab,    "📚 Книги")
        tabs.addTab(self.users_tab,    "👥 Пользователи")
        tabs.addTab(self.requests_tab, "📋 Заявки")
        tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(tabs)
        self._tabs = tabs

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.books_tab.refresh()
        elif index == 1:
            self.users_tab.refresh()
        elif index == 2:
            self.requests_tab.refresh()


# ─────────────────────────────────────────────────────────────────────────────
#  Вкладка «Книги» (управление каталогом)
# ─────────────────────────────────────────────────────────────────────────────

class AdminBooksTab(QWidget):
    def __init__(self):
        super().__init__()
        self._book_ids: list[int] = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout()

        lbl = QLabel("Управление каталогом книг")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Название", "Автор", "Год", "Жанр", "Статус"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()

        btn_add = QPushButton("➕ Добавить")
        btn_add.setStyleSheet(
            "background-color: #4CAF50; color: white; border-radius: 4px; padding: 6px 12px;"
        )
        btn_add.clicked.connect(self._add_book)
        btn_row.addWidget(btn_add)

        btn_edit = QPushButton("✏ Редактировать")
        btn_edit.setStyleSheet(
            "background-color: #2196F3; color: white; border-radius: 4px; padding: 6px 12px;"
        )
        btn_edit.clicked.connect(self._edit_book)
        btn_row.addWidget(btn_edit)

        btn_del = QPushButton("🗑 Удалить")
        btn_del.setStyleSheet(
            "background-color: #f44336; color: white; border-radius: 4px; padding: 6px 12px;"
        )
        btn_del.clicked.connect(self._delete_book)
        btn_row.addWidget(btn_del)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def refresh(self):
        books = db.get_books()
        self._book_ids = []
        self.table.setRowCount(len(books))
        for i, book in enumerate(books):
            self._book_ids.append(book["id"])
            self.table.setItem(i, 0, QTableWidgetItem(str(book["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(book["title"]))
            self.table.setItem(i, 2, QTableWidgetItem(book["author"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(book["year"] or "")))
            self.table.setItem(i, 4, QTableWidgetItem(book["genre"] or ""))
            self.table.setItem(
                i, 5,
                QTableWidgetItem("Доступна" if book["is_available"] else "Занята"),
            )

    def _selected(self) -> tuple[int | None, int | None]:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите книгу в таблице.")
            return None, None
        return row, self._book_ids[row]

    def _add_book(self):
        dlg = BookFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.add_book(d["title"], d["author"], d["year"], d["genre"])
            self.refresh()

    def _edit_book(self):
        _, book_id = self._selected()
        if book_id is None:
            return
        book = db.get_book(book_id)
        dlg = BookFormDialog(self, book)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.edit_book(book_id, d["title"], d["author"], d["year"], d["genre"])
            self.refresh()

    def _delete_book(self):
        _, book_id = self._selected()
        if book_id is None:
            return
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранную книгу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_book(book_id)
            self.refresh()


# ─────────────────────────────────────────────────────────────────────────────
#  Вкладка «Пользователи»
# ─────────────────────────────────────────────────────────────────────────────

class AdminUsersTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout()

        lbl = QLabel("Список пользователей")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "ФИО", "Логин", "Читательский билет", "Роль"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh(self):
        users = db.get_all_users()
        self.table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.table.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(u["full_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(u["login"]))
            self.table.setItem(i, 3, QTableWidgetItem(u["reader_card"]))
            self.table.setItem(
                i, 4,
                QTableWidgetItem("Администратор" if u["is_admin"] else "Читатель"),
            )


# ─────────────────────────────────────────────────────────────────────────────
#  Вкладка «Заявки»
# ─────────────────────────────────────────────────────────────────────────────

class AdminRequestsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout()

        lbl = QLabel("Все заявки на книги")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Книга", "Пользователь", "Статус", "Дата"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(btn_refresh)

        self.setLayout(layout)

    def refresh(self):
        requests = db.get_all_requests()
        self.table.setRowCount(len(requests))
        for i, req in enumerate(requests):
            status_ru = "Активна" if req["status"] == "active" else "Возвращена"
            self.table.setItem(i, 0, QTableWidgetItem(str(req["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(req["title"]))
            self.table.setItem(i, 2, QTableWidgetItem(req["full_name"]))
            self.table.setItem(i, 3, QTableWidgetItem(status_ru))
            self.table.setItem(i, 4, QTableWidgetItem(req["created_at"] or ""))


# ─────────────────────────────────────────────────────────────────────────────
#  Диалог: добавление / редактирование книги
# ─────────────────────────────────────────────────────────────────────────────

class BookFormDialog(QDialog):
    def __init__(self, parent=None, book: dict | None = None):
        super().__init__(parent)
        self.book = book
        self.setWindowTitle("Добавить книгу" if book is None else "Редактировать книгу")
        self.setFixedSize(420, 260)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        self.title_edit = QLineEdit(self.book["title"] if self.book else "")
        layout.addRow("Название:", self.title_edit)

        self.author_edit = QLineEdit(self.book["author"] if self.book else "")
        layout.addRow("Автор:", self.author_edit)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(0, 2100)
        self.year_spin.setValue(
            self.book["year"] if (self.book and self.book["year"]) else 2024
        )
        layout.addRow("Год:", self.year_spin)

        self.genre_edit = QLineEdit(
            (self.book["genre"] or "") if self.book else ""
        )
        layout.addRow("Жанр:", self.genre_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

        self.setLayout(layout)

    def _validate_and_accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название книги.")
            return
        if not self.author_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите имя автора.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "title":  self.title_edit.text().strip(),
            "author": self.author_edit.text().strip(),
            "year":   self.year_spin.value(),
            "genre":  self.genre_edit.text().strip() or None,
        }
