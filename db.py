import sqlite3

def create_database():
    """Create the SQLite database and books table with expanded fields."""
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books (
                    upc TEXT PRIMARY KEY,
                    title TEXT,
                    price_excl_tax REAL,
                    price_incl_tax REAL,
                    tax REAL,
                    availability TEXT,
                    num_reviews INTEGER,
                    rating INTEGER,
                    description TEXT,
                    product_type TEXT,
                    category TEXT
                 )''')
    conn.commit()
    conn.close()

def insert_books(books_list):
    """Insert a list of books into the database, ignoring duplicates based on UPC."""
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.executemany('''INSERT OR IGNORE INTO books 
                     (upc, title, price_excl_tax, price_incl_tax, tax, availability, num_reviews, rating, description, product_type, category) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  [(book['upc'], book['title'], book['price_excl_tax'], book['price_incl_tax'], book['tax'], 
                    book['availability'], book['num_reviews'], book['rating'], book['description'], 
                    book['product_type'], book['category']) for book in books_list])
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