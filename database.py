import hashlib, sqlite3

DB = "library.db"

def cn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def hp(p):
    return hashlib.pbkdf2_hmac("sha256", p.encode(), b"lib_salt", 10000).hex()

def init_db():
    c = cn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,login TEXT UNIQUE,password TEXT,reader_card TEXT UNIQUE,is_admin INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS books(id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,author TEXT,year INTEGER,genre TEXT,is_available INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,user_id INTEGER,status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT(datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,user_id INTEGER,created_at TEXT DEFAULT(datetime('now','localtime')));
        CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,user_id INTEGER,rating INTEGER,comment TEXT,
            created_at TEXT DEFAULT(datetime('now','localtime')),UNIQUE(book_id,user_id));
    """)
    try: c.execute("INSERT INTO users(full_name,login,password,reader_card,is_admin)VALUES(?,?,?,?,?)",
                   ("Администратор","admin",hp("admin"),"ADMIN-0001",1))
    except: pass
    for b in [("Мастер и Маргарита","Михаил Булгаков",1967,"Роман"),
              ("Преступление и наказание","Фёдор Достоевский",1866,"Роман"),
              ("Война и мир","Лев Толстой",1869,"Роман"),
              ("1984","Джордж Оруэлл",1949,"Антиутопия"),
              ("Гарри Поттер","Дж. К. Роулинг",1997,"Фэнтези"),
              ("Анна Каренина","Лев Толстой",1878,"Роман"),
              ("Маленький принц","Антуан де Сент-Экзюпери",1943,"Сказка")]:
        try: c.execute("INSERT INTO books(title,author,year,genre)VALUES(?,?,?,?)",b)
        except: pass
    c.commit(); c.close()

def login(u, p):
    c = cn(); r = c.execute("SELECT * FROM users WHERE login=?",(u,)).fetchone(); c.close()
    return dict(r) if r and r["password"]==hp(p) else None

def register(fn, ln, pw, rc):
    c = cn()
    try:
        c.execute("INSERT INTO users(full_name,login,password,reader_card)VALUES(?,?,?,?)",(fn,ln,hp(pw),rc))
        c.commit(); return True,"Готово!"
    except sqlite3.IntegrityError as e:
        return False,"Логин занят." if "login" in str(e) else "Билет занят."
    finally: c.close()

def get_users():
    c = cn(); r = c.execute("SELECT id,full_name,login,reader_card,is_admin FROM users ORDER BY id").fetchall(); c.close()
    return [dict(x) for x in r]

def get_books(genre=None, author=None, available=None, sort_by=None):
    q = ("SELECT b.id,b.title,b.author,b.year,b.genre,b.is_available,"
         "ROUND(COALESCE(AVG(rv.rating),0),1) AS avg_rating "
         "FROM books b LEFT JOIN reviews rv ON b.id=rv.book_id "
         "LEFT JOIN requests req ON b.id=req.book_id WHERE 1=1")
    p = []
    if genre: q+=" AND b.genre=?"; p.append(genre)
    if author: q+=" AND LOWER(b.author) LIKE LOWER(?)"; p.append(f"%{author}%")
    if available is not None: q+=" AND b.is_available=?"; p.append(1 if available else 0)
    q+=" GROUP BY b.id"
    q+={"rating":" ORDER BY avg_rating DESC","title":" ORDER BY b.title",
        "year":" ORDER BY b.year DESC","author":" ORDER BY b.author"}.get(sort_by," ORDER BY b.id")
    c = cn(); r = c.execute(q,p).fetchall(); c.close(); return [dict(x) for x in r]

def get_book(bid):
    c = cn(); r = c.execute("SELECT * FROM books WHERE id=?",(bid,)).fetchone(); c.close()
    return dict(r) if r else None

def add_book(t,a,y,g): c=cn(); c.execute("INSERT INTO books(title,author,year,genre)VALUES(?,?,?,?)",(t,a,y,g)); c.commit(); c.close()
def edit_book(bid,t,a,y,g): c=cn(); c.execute("UPDATE books SET title=?,author=?,year=?,genre=? WHERE id=?",(t,a,y,g,bid)); c.commit(); c.close()
def delete_book(bid): c=cn(); c.execute("DELETE FROM books WHERE id=?",(bid,)); c.commit(); c.close()

def get_genres():
    c=cn(); r=c.execute("SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL ORDER BY genre").fetchall(); c.close()
    return [x["genre"] for x in r]

def borrow_book(bid, uid):
    c=cn(); cur=c.cursor()
    bk=cur.execute("SELECT is_available FROM books WHERE id=?",(bid,)).fetchone()
    if not bk: c.close(); return "error","Не найдена."
    if cur.execute("SELECT id FROM requests WHERE book_id=? AND user_id=? AND status='active'",(bid,uid)).fetchone():
        c.close(); return "error","Уже взяли."
    if cur.execute("SELECT id FROM queue WHERE book_id=? AND user_id=?",(bid,uid)).fetchone():
        c.close(); return "error","Уже в очереди."
    if bk["is_available"]:
        cur.execute("INSERT INTO requests(book_id,user_id)VALUES(?,?)",(bid,uid))
        cur.execute("UPDATE books SET is_available=0 WHERE id=?",(bid,)); c.commit(); c.close(); return "ok","Взяли!"
    c.close(); return "busy","Занята. Встать в очередь?"

def join_queue(bid,uid): c=cn(); c.execute("INSERT INTO queue(book_id,user_id)VALUES(?,?)",(bid,uid)); c.commit(); c.close()

def return_book(bid,uid):
    c=cn(); cur=c.cursor()
    cur.execute("UPDATE requests SET status='returned' WHERE book_id=? AND user_id=? AND status='active'",(bid,uid))
    nx=cur.execute("SELECT q.id,q.user_id,u.full_name FROM queue q JOIN users u ON q.user_id=u.id WHERE q.book_id=? ORDER BY q.created_at LIMIT 1",(bid,)).fetchone()
    msg=None
    if nx:
        cur.execute("INSERT INTO requests(book_id,user_id)VALUES(?,?)",(bid,nx["user_id"]))
        cur.execute("DELETE FROM queue WHERE id=?",(nx["id"],)); msg=f"Передана: {nx['full_name']}"
    else: cur.execute("UPDATE books SET is_available=1 WHERE id=?",(bid,))
    c.commit(); c.close(); return msg

def get_user_books(uid):
    c=cn(); r=c.execute("SELECT b.id,b.title,b.author,b.year,b.genre,r.created_at AS taken_at FROM requests r JOIN books b ON r.book_id=b.id WHERE r.user_id=? AND r.status='active'",(uid,)).fetchall(); c.close()
    return [dict(x) for x in r]

def get_recommendations():
    c=cn(); r=c.execute("SELECT b.title,b.author,COUNT(DISTINCT req.id) AS bc,ROUND(COALESCE(AVG(rv.rating),0),1) AS ar FROM books b LEFT JOIN requests req ON b.id=req.book_id LEFT JOIN reviews rv ON b.id=rv.book_id GROUP BY b.id ORDER BY bc DESC,ar DESC LIMIT 5").fetchall(); c.close()
    return [dict(x) for x in r]

def add_review(bid,uid,rating,comment):
    c=cn()
    try: c.execute("INSERT OR REPLACE INTO reviews(book_id,user_id,rating,comment)VALUES(?,?,?,?)",(bid,uid,rating,comment)); c.commit(); return True,"Сохранено!"
    except Exception as e: return False,str(e)
    finally: c.close()

def get_reviews(bid):
    c=cn(); r=c.execute("SELECT rv.rating,rv.comment,rv.created_at,u.full_name FROM reviews rv JOIN users u ON rv.user_id=u.id WHERE rv.book_id=? ORDER BY rv.created_at DESC",(bid,)).fetchall(); c.close()
    return [dict(x) for x in r]

def get_all_requests():
    c=cn(); r=c.execute("SELECT r.id,b.title,u.full_name,r.status,r.created_at FROM requests r JOIN books b ON r.book_id=b.id JOIN users u ON r.user_id=u.id ORDER BY r.created_at DESC").fetchall(); c.close()
    return [dict(x) for x in r]
