import sqlite3

def create_database():
    """Create the SQLite database and books table."""
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (title TEXT, price REAL, rating INTEGER)''')
    conn.commit()
    conn.close()

def insert_books(books_list):
    """Insert a list of books into the database."""
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.executemany("INSERT INTO books (title, price, rating) VALUES (?, ?, ?)",
                  [(book['title'], book['price'], book['rating']) for book in books_list])
    conn.commit()
    conn.close()

def get_all_books():
    """Fetch all books from the database."""
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return books