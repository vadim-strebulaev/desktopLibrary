from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QLineEdit, QCheckBox, QMessageBox, QDialog,
    QSpinBox, QTextEdit, QDialogButtonBox, QFrame, QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import database as db


class MainWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"Цифровая Библиотека — {user['full_name']}")
        self.setMinimumSize(960, 620)

        self.catalog_tab       = CatalogTab(user, self)
        self.my_books_tab      = MyBooksTab(user, self)
        self.recommendations_tab = RecommendationsTab()

        tabs = QTabWidget()
        tabs.addTab(self.catalog_tab,         "📖 Каталог")
        tabs.addTab(self.my_books_tab,        "📚 Мои книги")
        tabs.addTab(self.recommendations_tab, "⭐ Рекомендации")
        tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(tabs)
        self._tabs = tabs

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.catalog_tab.refresh()
        elif index == 1:
            self.my_books_tab.refresh()
        elif index == 2:
            self.recommendations_tab.refresh()


# ─────────────────────────────────────────────────────────────────────────────
#  Вкладка «Каталог»
# ─────────────────────────────────────────────────────────────────────────────

class CatalogTab(QWidget):
    def __init__(self, user: dict, parent: MainWindow):
        super().__init__()
        self.user   = user
        self._parent = parent
        self._book_ids: list[int] = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # ── Панель фильтров ──────────────────────────────────────────────────
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Жанр:"))
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("Все")
        for g in db.get_genres():
            self.genre_combo.addItem(g)
        self.genre_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.genre_combo)

        filter_row.addWidget(QLabel("Автор:"))
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Поиск по автору")
        self.author_edit.textChanged.connect(self.refresh)
        filter_row.addWidget(self.author_edit)

        filter_row.addWidget(QLabel("Сортировка:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            ["По умолчанию", "По рейтингу", "По названию", "По году", "По автору"]
        )
        self.sort_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.sort_combo)

        self.available_check = QCheckBox("Только доступные")
        self.available_check.stateChanged.connect(self.refresh)
        filter_row.addWidget(self.available_check)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # ── Таблица ──────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Название", "Автор", "Год", "Жанр", "Рейтинг", "Статус"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # ── Кнопки ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()

        btn_take = QPushButton("📥 Взять книгу")
        btn_take.setMinimumHeight(34)
        btn_take.setStyleSheet(
            "background-color: #4CAF50; color: white; border-radius: 4px;"
        )
        btn_take.clicked.connect(self._take_book)
        btn_row.addWidget(btn_take)

        btn_review = QPushButton("✍ Оставить отзыв")
        btn_review.setMinimumHeight(34)
        btn_review.setStyleSheet(
            "background-color: #2196F3; color: white; border-radius: 4px;"
        )
        btn_review.clicked.connect(self._leave_review)
        btn_row.addWidget(btn_review)

        btn_view_reviews = QPushButton("👁 Просмотр отзывов")
        btn_view_reviews.setMinimumHeight(34)
        btn_view_reviews.clicked.connect(self._view_reviews)
        btn_row.addWidget(btn_view_reviews)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def refresh(self):
        genre = self.genre_combo.currentText()
        if genre == "Все":
            genre = None

        author  = self.author_edit.text().strip() or None
        sort_by = [None, "rating", "title", "year", "author"][self.sort_combo.currentIndex()]
        available = True if self.available_check.isChecked() else None

        books = db.get_books(genre=genre, author=author, available=available, sort_by=sort_by)

        self._book_ids = []
        self.table.setRowCount(len(books))
        for i, book in enumerate(books):
            self._book_ids.append(book["id"])
            self.table.setItem(i, 0, QTableWidgetItem(str(book["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(book["title"]))
            self.table.setItem(i, 2, QTableWidgetItem(book["author"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(book["year"] or "")))
            self.table.setItem(i, 4, QTableWidgetItem(book["genre"] or ""))

            r = book["avg_rating"]
            if r > 0:
                stars = "★" * round(r) + "☆" * (5 - round(r))
                rating_str = f"{stars} ({r:.1f})"
            else:
                rating_str = "Нет оценок"
            self.table.setItem(i, 5, QTableWidgetItem(rating_str))

            status_item = QTableWidgetItem(
                "✅ Доступна" if book["is_available"] else "❌ Занята"
            )
            status_item.setForeground(
                QColor("#2e7d32") if book["is_available"] else QColor("#c62828")
            )
            self.table.setItem(i, 6, status_item)

    def _selected_book_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите книгу в таблице.")
            return None
        return self._book_ids[row]

    def _take_book(self):
        book_id = self._selected_book_id()
        if book_id is None:
            return

        status, msg = db.borrow_book(book_id, self.user["id"])

        if status == "ok":
            QMessageBox.information(self, "Успех", msg)
            self.refresh()
            self._parent.my_books_tab.refresh()
        elif status == "busy":
            reply = QMessageBox.question(
                self, "Книга занята", f"{msg}\n\nВстать в очередь?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                db.join_queue(book_id, self.user["id"])
                QMessageBox.information(self, "Очередь", "Вы добавлены в очередь на эту книгу.")
        else:
            QMessageBox.warning(self, "Ошибка", msg)

    def _leave_review(self):
        book_id = self._selected_book_id()
        if book_id is None:
            return
        book = db.get_book(book_id)
        dlg = ReviewDialog(book, self.user["id"], self)
        dlg.exec()
        self.refresh()

    def _view_reviews(self):
        book_id = self._selected_book_id()
        if book_id is None:
            return
        book = db.get_book(book_id)
        ReviewsViewDialog(book, self).exec()


# ─────────────────────────────────────────────────────────────────────────────
#  Вкладка «Мои книги»
# ─────────────────────────────────────────────────────────────────────────────

class MyBooksTab(QWidget):
    def __init__(self, user: dict, parent: MainWindow):
        super().__init__()
        self.user   = user
        self._parent = parent
        self._book_ids: list[int] = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout()

        lbl = QLabel("Мои книги")
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Название", "Автор", "Год", "Жанр", "Дата взятия"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_return = QPushButton("📤 Вернуть выбранную книгу")
        btn_return.setMinimumHeight(36)
        btn_return.setStyleSheet(
            "background-color: #FF9800; color: white; border-radius: 4px;"
        )
        btn_return.clicked.connect(self._return_book)
        layout.addWidget(btn_return)

        self.setLayout(layout)

    def refresh(self):
        books = db.get_user_books(self.user["id"])
        self._book_ids = []
        self.table.setRowCount(len(books))
        for i, book in enumerate(books):
            self._book_ids.append(book["id"])
            self.table.setItem(i, 0, QTableWidgetItem(book["title"]))
            self.table.setItem(i, 1, QTableWidgetItem(book["author"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(book["year"] or "")))
            self.table.setItem(i, 3, QTableWidgetItem(book["genre"] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(book.get("taken_at") or ""))

    def _return_book(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите книгу для возврата.")
            return

        book_id = self._book_ids[row]
        notification = db.return_book(book_id, self.user["id"])

        text = "Книга успешно возвращена!"
        if notification:
            text += f"\n\n📢 {notification}"
        QMessageBox.information(self, "Возврат", text)

        self.refresh()
        self._parent.catalog_tab.refresh()


# ─────────────────────────────────────────────────────────────────────────────
#  Вкладка «Рекомендации»
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        outer = QVBoxLayout()

        lbl = QLabel("⭐ Топ-5 самых читаемых книг")
        lbl.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(lbl)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        outer.addWidget(self._cards_widget)
        outer.addStretch()

        self.setLayout(outer)

    def refresh(self):
        # Очищаем предыдущие карточки
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        books = db.get_recommendations()
        if not books:
            self._cards_layout.addWidget(
                QLabel("Нет данных для отображения.")
            )
            return

        medals = ["🥇", "🥈", "🥉", "4.", "5."]
        for i, book in enumerate(books):
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame.setStyleSheet(
                "QFrame { background: #f5f5f5; border-radius: 8px; margin: 4px; padding: 4px; }"
            )

            row = QHBoxLayout(frame)

            rank_lbl = QLabel(medals[i])
            rank_lbl.setFont(QFont("Arial", 22))
            rank_lbl.setFixedWidth(50)
            rank_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(rank_lbl)

            info = QVBoxLayout()
            title_lbl = QLabel(book["title"])
            title_lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            info.addWidget(title_lbl)
            author_lbl = QLabel(f"{book['author']}, {book.get('year') or '—'}")
            author_lbl.setStyleSheet("color: gray;")
            info.addWidget(author_lbl)
            row.addLayout(info)

            row.addStretch()

            stats = QVBoxLayout()
            stats.addWidget(QLabel(f"📖 Взята: {book['borrow_count']} раз"))
            r = book["avg_rating"]
            stats.addWidget(
                QLabel(f"⭐ Рейтинг: {r:.1f}" if r > 0 else "⭐ Нет оценок")
            )
            row.addLayout(stats)

            self._cards_layout.addWidget(frame)

        self._cards_layout.addStretch()


# ─────────────────────────────────────────────────────────────────────────────
#  Диалог: оставить отзыв
# ─────────────────────────────────────────────────────────────────────────────

class ReviewDialog(QDialog):
    def __init__(self, book: dict, user_id: int, parent=None):
        super().__init__(parent)
        self.book    = book
        self.user_id = user_id
        self.setWindowTitle("Оставить отзыв")
        self.setFixedSize(420, 310)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(QLabel(f"<b>Книга:</b> {self.book['title']}"))
        layout.addWidget(QLabel(f"<b>Автор:</b> {self.book['author']}"))
        layout.addSpacing(6)

        rating_row = QHBoxLayout()
        rating_row.addWidget(QLabel("Оценка (1–5):"))
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(1, 5)
        self.rating_spin.setValue(5)
        rating_row.addWidget(self.rating_spin)
        rating_row.addStretch()
        layout.addLayout(rating_row)

        layout.addWidget(QLabel("Комментарий (необязательно):"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(100)
        layout.addWidget(self.comment_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setLayout(layout)

    def _save(self):
        rating  = self.rating_spin.value()
        comment = self.comment_edit.toPlainText().strip()
        ok, msg = db.add_review(self.book["id"], self.user_id, rating, comment)
        if ok:
            QMessageBox.information(self, "Успех", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", msg)


# ─────────────────────────────────────────────────────────────────────────────
#  Диалог: просмотр отзывов
# ─────────────────────────────────────────────────────────────────────────────

class ReviewsViewDialog(QDialog):
    def __init__(self, book: dict, parent=None):
        super().__init__(parent)
        self.book = book
        self.setWindowTitle(f"Отзывы: {book['title']}")
        self.setMinimumSize(520, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"<b>Книга:</b> {self.book['title']}"))
        layout.addWidget(QLabel(f"<b>Автор:</b> {self.book['author']}"))
        layout.addSpacing(8)

        reviews = db.get_reviews(self.book["id"])

        if not reviews:
            layout.addWidget(QLabel("Отзывов пока нет."))
        else:
            for rv in reviews:
                frame = QFrame()
                frame.setFrameShape(QFrame.Shape.StyledPanel)
                frame.setStyleSheet(
                    "QFrame { background: #f9f9f9; border-radius: 5px; margin: 3px; }"
                )

                fl = QVBoxLayout(frame)
                stars = "★" * rv["rating"] + "☆" * (5 - rv["rating"])
                header_lbl = QLabel(
                    f"<b>{rv['full_name']}</b> — {stars} ({rv['rating']}/5)"
                    f"  <span style='color:gray;font-size:11px;'>{rv['created_at']}</span>"
                )
                fl.addWidget(header_lbl)

                if rv["comment"]:
                    txt = QLabel(rv["comment"])
                    txt.setWordWrap(True)
                    fl.addWidget(txt)

                layout.addWidget(frame)

        layout.addStretch()

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)
