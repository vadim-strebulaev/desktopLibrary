import hashlib
import sqlite3

DB_PATH = "library.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), b"library_app_salt", 10000).hex()


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT NOT NULL,
            login       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            reader_card TEXT UNIQUE NOT NULL,
            is_admin    INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS books (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            author       TEXT NOT NULL,
            year         INTEGER,
            genre        TEXT,
            is_available INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS requests (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id    INTEGER,
            user_id    INTEGER,
            status     TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS queue (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id    INTEGER,
            user_id    INTEGER,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id    INTEGER,
            user_id    INTEGER,
            rating     INTEGER,
            comment    TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE(book_id, user_id)
        );
    """)

    # Создаём аккаунт администратора
    try:
        conn.execute(
            "INSERT INTO users (full_name, login, password, reader_card, is_admin) VALUES (?, ?, ?, ?, ?)",
            ("Администратор", "admin", hash_password("admin"), "ADMIN-0001", 1),
        )
    except sqlite3.IntegrityError:
        pass

    # Добавляем тестовые книги
    books = [
        ("Мастер и Маргарита", "Михаил Булгаков", 1967, "Роман"),
        ("Преступление и наказание", "Фёдор Достоевский", 1866, "Роман"),
        ("Война и мир", "Лев Толстой", 1869, "Роман"),
        ("1984", "Джордж Оруэлл", 1949, "Антиутопия"),
        ("Гарри Поттер и философский камень", "Дж. К. Роулинг", 1997, "Фэнтези"),
        ("Идиот", "Фёдор Достоевский", 1869, "Роман"),
        ("Анна Каренина", "Лев Толстой", 1878, "Роман"),
        ("Маленький принц", "Антуан де Сент-Экзюпери", 1943, "Сказка"),
    ]
    for b in books:
        try:
            conn.execute("INSERT INTO books (title, author, year, genre) VALUES (?, ?, ?, ?)", b)
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


# --- пользователи ---

def login(username, password):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE login = ?", (username,)).fetchone()
    conn.close()
    if user and user["password"] == hash_password(password):
        return dict(user)
    return None


def register(full_name, login_name, password, reader_card):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (full_name, login, password, reader_card) VALUES (?, ?, ?, ?)",
            (full_name, login_name, hash_password(password), reader_card),
        )
        conn.commit()
        return True, "Регистрация прошла успешно!"
    except sqlite3.IntegrityError as e:
        if "login" in str(e):
            return False, "Такой логин уже существует."
        if "reader_card" in str(e):
            return False, "Такой номер билета уже используется."
        return False, "Ошибка регистрации."
    finally:
        conn.close()


def get_all_users():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, full_name, login, reader_card, is_admin FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- книги ---

def get_books(genre=None, author=None, year=None, available=None, sort_by=None):
    query = """
        SELECT b.id, b.title, b.author, b.year, b.genre, b.is_available,
               ROUND(COALESCE(AVG(rv.rating), 0), 1) AS avg_rating,
               COUNT(DISTINCT req.id) AS borrow_count
        FROM books b
        LEFT JOIN reviews rv ON b.id = rv.book_id
        LEFT JOIN requests req ON b.id = req.book_id
        WHERE 1=1
    """
    params = []

    if genre:
        query += " AND b.genre = ?"
        params.append(genre)
    if author:
        query += " AND LOWER(b.author) LIKE LOWER(?)"
        params.append(f"%{author}%")
    if year:
        query += " AND b.year = ?"
        params.append(year)
    if available is not None:
        query += " AND b.is_available = ?"
        params.append(1 if available else 0)

    query += " GROUP BY b.id"

    sorts = {
        "rating": " ORDER BY avg_rating DESC",
        "title":  " ORDER BY b.title ASC",
        "year":   " ORDER BY b.year DESC",
        "author": " ORDER BY b.author ASC",
    }
    query += sorts.get(sort_by, " ORDER BY b.id ASC")

    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_book(book_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_book(title, author, year, genre):
    conn = get_conn()
    conn.execute(
        "INSERT INTO books (title, author, year, genre) VALUES (?, ?, ?, ?)",
        (title, author, year, genre),
    )
    conn.commit()
    conn.close()


def edit_book(book_id, title, author, year, genre):
    conn = get_conn()
    conn.execute(
        "UPDATE books SET title=?, author=?, year=?, genre=? WHERE id=?",
        (title, author, year, genre, book_id),
    )
    conn.commit()
    conn.close()


def delete_book(book_id):
    conn = get_conn()
    conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()


def get_genres():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL ORDER BY genre"
    ).fetchall()
    conn.close()
    return [r["genre"] for r in rows]


# --- выдача и возврат ---

def borrow_book(book_id, user_id):
    conn = get_conn()
    c = conn.cursor()

    book = c.execute("SELECT is_available FROM books WHERE id=?", (book_id,)).fetchone()
    if not book:
        conn.close()
        return "error", "Книга не найдена."

    if c.execute(
        "SELECT id FROM requests WHERE book_id=? AND user_id=? AND status='active'",
        (book_id, user_id),
    ).fetchone():
        conn.close()
        return "error", "Вы уже взяли эту книгу."

    if c.execute(
        "SELECT id FROM queue WHERE book_id=? AND user_id=?", (book_id, user_id)
    ).fetchone():
        conn.close()
        return "error", "Вы уже стоите в очереди на эту книгу."

    if book["is_available"]:
        c.execute("INSERT INTO requests (book_id, user_id) VALUES (?, ?)", (book_id, user_id))
        c.execute("UPDATE books SET is_available=0 WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
        return "ok", "Книга успешно взята!"

    conn.close()
    return "busy", "Книга занята. Встать в очередь?"


def join_queue(book_id, user_id):
    conn = get_conn()
    conn.execute("INSERT INTO queue (book_id, user_id) VALUES (?, ?)", (book_id, user_id))
    conn.commit()
    conn.close()


def return_book(book_id, user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE requests SET status='returned' WHERE book_id=? AND user_id=? AND status='active'",
        (book_id, user_id),
    )

    next_user = c.execute(
        "SELECT q.id, q.user_id, u.full_name FROM queue q JOIN users u ON q.user_id=u.id "
        "WHERE q.book_id=? ORDER BY q.created_at LIMIT 1",
        (book_id,),
    ).fetchone()

    notification = None
    if next_user:
        c.execute("INSERT INTO requests (book_id, user_id) VALUES (?, ?)", (book_id, next_user["user_id"]))
        c.execute("DELETE FROM queue WHERE id=?", (next_user["id"],))
        notification = f"Книга передана следующему в очереди: {next_user['full_name']}."
    else:
        c.execute("UPDATE books SET is_available=1 WHERE id=?", (book_id,))

    conn.commit()
    conn.close()
    return notification


def get_user_books(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT b.id, b.title, b.author, b.year, b.genre, r.created_at AS taken_at "
        "FROM requests r JOIN books b ON r.book_id=b.id "
        "WHERE r.user_id=? AND r.status='active'",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- рекомендации ---

def get_recommendations():
    conn = get_conn()
    rows = conn.execute(
        "SELECT b.id, b.title, b.author, b.year, b.genre, "
        "COUNT(DISTINCT req.id) AS borrow_count, "
        "ROUND(COALESCE(AVG(rv.rating), 0), 1) AS avg_rating "
        "FROM books b "
        "LEFT JOIN requests req ON b.id=req.book_id "
        "LEFT JOIN reviews rv ON b.id=rv.book_id "
        "GROUP BY b.id ORDER BY borrow_count DESC, avg_rating DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- отзывы ---

def add_review(book_id, user_id, rating, comment):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO reviews (book_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
            (book_id, user_id, rating, comment),
        )
        conn.commit()
        return True, "Отзыв сохранён!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_reviews(book_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT rv.rating, rv.comment, rv.created_at, u.full_name "
        "FROM reviews rv JOIN users u ON rv.user_id=u.id "
        "WHERE rv.book_id=? ORDER BY rv.created_at DESC",
        (book_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- заявки для администратора ---

def get_all_requests():
    conn = get_conn()
    rows = conn.execute(
        "SELECT r.id, b.title, u.full_name, r.status, r.created_at "
        "FROM requests r "
        "JOIN books b ON r.book_id=b.id "
        "JOIN users u ON r.user_id=u.id "
        "ORDER BY r.created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
