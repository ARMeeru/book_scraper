# Books to Scrape - Python Scraper

This project is a Python-based web scraper that extracts book information from the "Books to Scrape" demo website (http://books.toscrape.com) using Playwright and stores the data in a local SQLite database.

## Features
- Scrape all books across multiple pages
- Extract detailed information for each book:
  - UPC
  - Title
  - Price (excl. tax and incl. tax)
  - Tax
  - Availability
  - Number of reviews
  - Rating (1 to 5 stars)
  - Description
  - Product type
  - Category (breadcrumb path)
- Store scraped data in an `SQLite` database (`books.db`)
- Idempotent inserts (duplicate UPCs are ignored)

## Prerequisites
- Python 3.7 or higher
- `pip` package manager

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/books-scraper.git
   cd books-scraper
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```
3. Install required Python packages:
   ```bash
   pip install playwright
   ```
4. Install Playwright browser binaries:
   ```bash
   playwright install
   ```

## Usage
Run the scraper to fetch all books and populate the database:
```bash
python scraper.py
```
This will:
- Create `books.db` (if it doesn't exist)
- Scrape all book pages and extract details
- Insert records into the `books` table (ignoring duplicates)
- Print log information about scraping progress

## Accessing the Data
You can query the collected data using the provided `db.py` functions, for example:
```python
from db import get_all_books
books = get_all_books()
for book in books[:5]:
    print(book)
```

## Project Structure
```
├── scraper.py      # Main scraper using Playwright
├── db.py           # SQLite database functions
├── books.db        # SQLite database (generated after first run)
└── README.md       # This documentation file
```

## License
This project is released under the MIT License. See [LICENSE](https://github.com/ARMeeru/book_scraper/blob/main/LICENSE) for details.