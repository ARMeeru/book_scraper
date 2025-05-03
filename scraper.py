import logging
from playwright.sync_api import sync_playwright
from db import create_database, insert_books, get_all_books

# Set up basic logging
logging.basicConfig(level=logging.INFO)

def scrape_page(url):
    """Scrape book data from a single page."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        books = []
        book_elements = page.query_selector_all('.product_pod')
        for book_el in book_elements:
            title = book_el.query_selector('h3 a').get_attribute('title')
            price_str = book_el.query_selector('.price_color').inner_text()
            price = float(price_str.replace('£', ''))
            rating_class = book_el.query_selector('.star-rating').get_attribute('class').split()[-1]
            rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
            rating = rating_map.get(rating_class, 0)  # Default to 0 if not found
            books.append({'title': title, 'price': price, 'rating': rating})
        browser.close()
    return books

if __name__ == '__main__':
    # Create the database and table
    create_database()
    
    # Scrape the first page
    url = 'http://books.toscrape.com/catalogue/page-1.html'
    books = scrape_page(url)
    
    # Insert scraped books into the database
    insert_books(books)
    
    # Verify insertion by fetching and logging the data
    all_books = get_all_books()
    logging.info(f'Scraped and inserted {len(books)} books.')
    logging.info(f'Total books in database: {len(all_books)}')
    
    # Print sample data for verification
    for book in all_books[:5]:
        logging.info(book)