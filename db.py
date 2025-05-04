import sqlite3

def create_database(db_path='books.db'):
    """Create the SQLite database and books table with expanded fields."""
    conn = sqlite3.connect(db_path)
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
                    category TEXT,
                    last_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()

def insert_books(books_list, db_path='books.db'):
    """Insert a list of books into the database, ignoring duplicates based on UPC."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Upsert: insert new records or update existing ones, updating last_scraped_at
    c.executemany('''
        INSERT INTO books
            (upc, title, price_excl_tax, price_incl_tax, tax, availability, num_reviews, rating, description, product_type, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(upc) DO UPDATE SET
            title=excluded.title,
            price_excl_tax=excluded.price_excl_tax,
            price_incl_tax=excluded.price_incl_tax,
            tax=excluded.tax,
            availability=excluded.availability,
            num_reviews=excluded.num_reviews,
            rating=excluded.rating,
            description=excluded.description,
            product_type=excluded.product_type,
            category=excluded.category,
            last_scraped_at=CURRENT_TIMESTAMP
    ''',
    [
        (
            book['upc'], book['title'], book['price_excl_tax'], book['price_incl_tax'], book['tax'],
            book['availability'], book['num_reviews'], book['rating'], book['description'],
            book['product_type'], book['category']
        )
        for book in books_list
    ])
    conn.commit()
    conn.close()

def get_all_books(db_path='books.db'):
    """Fetch all books from the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return books