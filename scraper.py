import argparse
import logging
import time
import random
from playwright.sync_api import sync_playwright
from db import create_database, insert_books, get_all_books

# Module-level constants and logger
from urllib.parse import urljoin
logger = logging.getLogger(__name__)
BASE_URL = "http://books.toscrape.com"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
GOTO_TIMEOUT_MS = 10000  # ms for page.goto timeout
SELECTOR_TIMEOUT_MS = 5000  # ms for waiting selectors


def get_book_urls(page):
    """Extract absolute book detail URLs from the current listing page."""
    # Links are relative to the listing page URL
    anchors = page.query_selector_all(".product_pod h3 a")
    urls = []
    for a in anchors:
        href = a.get_attribute("href") or ""
        # Resolve relative URL against the current page URL
        full_url = urljoin(page.url, href)
        urls.append(full_url)
    return urls


def scrape_book_details(page):
    """Scrape detailed book information from the detail page."""
    # Scrape title
    title = page.locator("h1").text_content() or ""

    # Scrape product information table
    product_info = {}
    table_rows = page.query_selector_all(".table.table-striped tr")
    for row in table_rows:
        key_el = row.query_selector("th")
        val_el = row.query_selector("td")
        key = key_el.inner_text().strip() if key_el else ""
        value = val_el.inner_text().strip() if val_el else ""
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
    desc_el = page.query_selector("article.product_page > p")
    description = desc_el.inner_text().strip() if desc_el else ""

    # Scrape category from breadcrumb
    crumbs = page.query_selector_all(".breadcrumb li a")
    category_path = " > ".join([c.inner_text().strip() for c in crumbs if c])

    # Scrape rating
    rating = 0
    rating_el = page.query_selector(".star-rating")
    if rating_el:
        class_attr = rating_el.get_attribute("class") or ""
        style = class_attr.split()[-1] if class_attr else ""
        rating = RATING_MAP.get(style, 0)

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


def scrape_all_books(start_page=1, limit=None, min_delay=0.1, max_delay=0.5, retries=3):
    """
    Scrape all books from pages starting at `start_page`, optionally limiting total books,
    with delays between detail requests and retry logic.
    """
    # Use module-level BASE_URL
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Paginate through listing pages
        book_urls = []
        page_number = start_page
        while True:
            list_url = f"{BASE_URL}/catalogue/page-{page_number}.html"
            try:
                page.goto(list_url)
                page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.warning("Failed to load listing page %d: %s", page_number, e, exc_info=True)
                break
            urls = get_book_urls(page)
            if not urls:
                break
            # Optionally limit number of URLs collected
            if limit:
                remaining = limit - len(book_urls)
                if remaining <= 0:
                    break
                urls = urls[:remaining]
            book_urls.extend(urls)
            logger.info("Found %d book URLs on page %d", len(urls), page_number)
            next_link = page.query_selector("li.next a")
            if next_link:
                page_number += 1
            else:
                break


        # Scrape details for each book with retries and delays
        books = []
        for idx, url in enumerate(book_urls, 1):
            book_data = None
            for attempt in range(1, retries + 1):
                try:
                    # Navigate with shorter timeout and wait until DOM is loaded
                    page.goto(url, timeout=GOTO_TIMEOUT_MS, wait_until="domcontentloaded")
                    # Ensure title is present before scraping details
                    page.wait_for_selector("h1", timeout=SELECTOR_TIMEOUT_MS)
                    book_data = scrape_book_details(page)
                    break
                except Exception as e:
                    logger.warning(
                        "Error scraping %s (attempt %d/%d)", url, attempt, retries, exc_info=True
                    )
                    time.sleep(1)
            if not book_data:
                logger.error(
                    "Failed to scrape %s after %d attempts, skipping", url, retries
                )
                continue
            books.append(book_data)
            if idx % 100 == 0:
                logger.info(
                    "Scraped details for %d of %d books", idx, len(book_urls)
                )
            # Politeness delay between requests
            time.sleep(random.uniform(min_delay, max_delay))

        browser.close()
    return books


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    # Command-line interface
    parser = argparse.ArgumentParser(description='Books to Scrape')
    parser.add_argument('--start-page', type=int, default=1, help='Page to start scraping from')
    parser.add_argument('--limit', type=int, default=None, help='Max number of books to scrape')
    parser.add_argument('--min-delay', type=float, default=0.1, help='Minimum delay between book requests (s)')
    parser.add_argument('--max-delay', type=float, default=0.5, help='Maximum delay between book requests (s)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries for detail page fetch')
    parser.add_argument('--dry-run', action='store_true', help='Scrape only, skip DB insertion')
    args = parser.parse_args()
    # Start timer for total runtime
    start_time = time.time()

    try:
        # Ensure database/table exists
        create_database()
        logger.info('Starting scraping: start_page=%d', args.start_page)
        books = scrape_all_books(
            start_page=args.start_page,
            limit=args.limit,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            retries=args.retries
        )
        if args.dry_run:
            logger.info('Dry run: skipping database insertion')
        else:
            insert_books(books)
            all_books = get_all_books()
            logger.info(
                'Inserted/updated %d books, total in DB: %d', len(books), len(all_books)
            )
    except KeyboardInterrupt:
        logger.info('Scraping aborted by user')
    except Exception:
        logger.exception('Unexpected error during scraping')
    finally:
        # Print total runtime
        elapsed = time.time() - start_time
        logger.info('Total runtime: %.2f seconds', elapsed)
