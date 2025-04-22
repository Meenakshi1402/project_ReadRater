from flask import (
    Flask, render_template, request, redirect, url_for,
    abort, session, g, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # load from env in prod


def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Twisted@love25',   # your MySQL password
        database='readraterdb'
    )


def fetch_all_books(q=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if q:
        sql = """
          SELECT id, title, author, cover_url
            FROM books
           WHERE title LIKE %s
              OR author LIKE %s;
        """
        like_q = f"%{q}%"
        cursor.execute(sql, (like_q, like_q))
    else:
        cursor.execute("SELECT id, title, author, cover_url FROM books;")
    cols = [c[0] for c in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]


def fetch_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, author, cover_url FROM books WHERE id = %s;",
        (book_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return None
    cols = [c[0] for c in cursor.description]
    return dict(zip(cols, row))


def fetch_reviews(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
          r.id           AS review_id,
          r.user_id      AS reviewer_id,
          r.rating,
          r.comment,
          r.created_at,
          u.username
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.book_id = %s
        ORDER BY r.created_at DESC;
        """,
        (book_id,)
    )
    cols = [c[0] for c in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = {'id': user_id, 'username': session.get('username')} if user_id else None


@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    books = fetch_all_books(q or None)
    return render_template('index.html', books=books, q=q)


@app.route('/books/<int:book_id>')
def book_detail(book_id):
    book = fetch_book(book_id)
    if not book:
        abort(404)
    reviews = fetch_reviews(book_id)
    return render_template('book_detail.html', book=book, reviews=reviews)


@app.route('/books/<int:book_id>/review', methods=['POST'])
def add_review(book_id):
    if not g.user:
        flash("You must be logged in to post a review.")
        return redirect(url_for('login'))
    try:
        rating = int(request.form.get('rating'))
        if rating < 1 or rating > 5:
            raise ValueError()
    except (TypeError, ValueError):
        abort(400, "Invalid rating")
    comment = request.form.get('comment', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (user_id, book_id, rating, comment) VALUES (%s, %s, %s, %s);",
        (g.user['id'], book_id, rating, comment)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/reviews/<int:review_id>/delete', methods=['POST'])
def delete_review(review_id):
    if not g.user:
        flash("You must be logged in to delete reviews.")
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM reviews WHERE id = %s AND user_id = %s;",
        (review_id, g.user['id'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash("Review deleted.")
    return redirect(request.referrer or url_for('index'))


@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if not g.user:
        flash("You must be logged in to add books.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()
        cover_url = request.form.get('cover_url', '').strip() or None
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, cover_url) VALUES (%s, %s, %s);",
            (title, author, cover_url)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Book added successfully!")
        return redirect(url_for('index'))
    return render_template('add_book.html')


@app.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    if not g.user:
        flash("You must be logged in to edit books.")
        return redirect(url_for('login'))
    book = fetch_book(book_id)
    if not book:
        abort(404)
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()
        cover_url = request.form.get('cover_url', '').strip() or None
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET title=%s, author=%s, cover_url=%s WHERE id=%s;",
            (title, author, cover_url, book_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Book updated.")
        return redirect(url_for('book_detail', book_id=book_id))
    return render_template('edit_book.html', book=book)


@app.route('/books/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    if not g.user:
        flash("You must be logged in to delete books.")
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE book_id=%s;", (book_id,))
    cursor.execute("DELETE FROM books WHERE id=%s;", (book_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Book and its reviews deleted.")
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash("Username and password required.")
            return redirect(url_for('register'))
        pwd_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s);",
                (username, pwd_hash)
            )
            conn.commit()
        except mysql.connector.IntegrityError:
            flash("Username already taken.")
            cursor.close()
            conn.close()
            return redirect(url_for('register'))
        cursor.close()
        conn.close()
        flash("Account created! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username=%s;",
            (username,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and check_password_hash(row[1], password):
            session.clear()
            session['user_id'] = row[0]
            session['username'] = username
            flash(f"Welcome, {username}!")
            return redirect(url_for('index'))
        flash("Invalid username or password.")
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
