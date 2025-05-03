import logging
from playwright.sync_api import sync_playwright
from db import create_database, insert_books, get_all_books

# Set up basic logging
logging.basicConfig(level=logging.INFO)


def get_book_urls(page, base_url):
    """Extract book detail URLs from the current page."""
    book_elements = page.query_selector_all(".product_pod")
    urls = []
    for book_el in book_elements:
        link = book_el.query_selector("h3 a").get_attribute("href")
        full_url = f"{base_url}/catalogue/{link}"
        urls.append(full_url)
    return urls


def scrape_book_details(page):
    """Scrape detailed book information from the detail page."""
    # Scrape title
    title = page.query_selector("h1").inner_text()

    # Scrape product information table
    product_info = {}
    table_rows = page.query_selector_all(".table.table-striped tr")
    for row in table_rows:
        key = row.query_selector("th").inner_text().strip()
        value = row.query_selector("td").inner_text().strip()
        product_info[key] = value

    # Extract specific fields from product info
    upc = product_info.get("UPC", "")
    product_type = product_info.get("Product Type", "")
    price_excl_tax = float(
        product_info.get("Price (excl. tax)", "£0.00").replace("£", "")
    )
    price_incl_tax = float(
        product_info.get("Price (incl. tax)", "£0.00").replace("£", "")
    )
    tax = float(product_info.get("Tax", "£0.00").replace("£", ""))
    availability = product_info.get("Availability", "")
    num_reviews = int(product_info.get("Number of reviews", "0"))

    # Scrape description
    description_element = page.query_selector("article.product_page > p")
    description = description_element.inner_text() if description_element else ""

    # Scrape category from breadcrumb
    breadcrumb = page.query_selector(".breadcrumb")
    categories = breadcrumb.query_selector_all("li a")
    category_path = " > ".join([cat.inner_text().strip() for cat in categories])

    # Scrape rating
    rating_element = page.query_selector(".star-rating")
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    rating = (
        rating_map.get(rating_element.get_attribute("class").split()[-1], 0)
        if rating_element
        else 0
    )

    # Return book data as a dictionary
    return {
        "upc": upc,
        "title": title,
        "price_excl_tax": price_excl_tax,
        "price_incl_tax": price_incl_tax,
        "tax": tax,
        "availability": availability,
        "num_reviews": num_reviews,
        "rating": rating,
        "description": description,
        "product_type": product_type,
        "category": category_path,
    }


def scrape_all_books():
    """Scrape all books from all pages by following 'next' links and return a list of book data."""
    base_url = "http://books.toscrape.com"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Start at the first page
        current_url = f"{base_url}/catalogue/page-1.html"
        book_urls = []
        page_number = 1
        while current_url:
            page.goto(current_url)
            urls = get_book_urls(page, base_url)
            book_urls.extend(urls)
            logging.info(f"Scraped URLs from page {page_number}")
            next_link = page.query_selector("li.next a")
            if next_link:
                next_href = next_link.get_attribute("href")
                current_url = f"{base_url}/catalogue/{next_href}"
                page_number += 1
            else:
                current_url = None

        # Scrape details for each book
        books = []
        for idx, url in enumerate(book_urls, 1):
            page.goto(url)
            book_data = scrape_book_details(page)
            books.append(book_data)
            if idx % 100 == 0:
                logging.info(f"Scraped details for {idx} of {len(book_urls)} books")

        browser.close()
    return books


if __name__ == "__main__":
    # Create the database and table
    create_database()

    # Scrape all books from all pages
    logging.info("Starting to scrape all books...")
    books = scrape_all_books()

    # Insert scraped books into the database
    insert_books(books)

    # Verify insertion
    all_books = get_all_books()
    logging.info(f"Scraped and inserted {len(books)} books.")
    logging.info(f"Total books in database: {len(all_books)}")

    # Print sample data for verification (first 5 books)
    """logging.info("Sample of first 5 books:")
    for book in all_books[:5]:
        logging.info(book)"""
