"""
Mudrex API Training Data Scraper
Scrapes official documentation into individual Markdown files for bot training.
Target: https://docs.trade.mudrex.com/docs
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import logging
from pathlib import Path
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of all documentation pages to scrape
LINKS = [
    "https://docs.trade.mudrex.com/docs/authentication-rate-limits",
    "https://docs.trade.mudrex.com/docs/error-handling",
    "https://docs.trade.mudrex.com/docs/wallet",
    "https://docs.trade.mudrex.com/docs/get-spot-funds",
    "https://docs.trade.mudrex.com/docs/post-transfer-funds",
    "https://docs.trade.mudrex.com/docs/futures-wallet",
    "https://docs.trade.mudrex.com/docs/get-available-funds-futures",
    "https://docs.trade.mudrex.com/docs/get-asset-listing",
    "https://docs.trade.mudrex.com/docs/get",
    "https://docs.trade.mudrex.com/docs/leverage",
    "https://docs.trade.mudrex.com/docs/get-leverage-by-asset-id",
    "https://docs.trade.mudrex.com/docs/set",
    "https://docs.trade.mudrex.com/docs/orders",
    "https://docs.trade.mudrex.com/docs/post-market-order",
    "https://docs.trade.mudrex.com/docs/get-order-by-id",
    "https://docs.trade.mudrex.com/docs/get-open-orders",
    "https://docs.trade.mudrex.com/docs/get-order-history",
    "https://docs.trade.mudrex.com/docs/delete-order",
    "https://docs.trade.mudrex.com/docs/positions",
    "https://docs.trade.mudrex.com/docs/get-open-positions",
    "https://docs.trade.mudrex.com/docs/get-liquidation-price",
    "https://docs.trade.mudrex.com/docs/add-margin",
    "https://docs.trade.mudrex.com/docs/set-sl-tp",
    "https://docs.trade.mudrex.com/docs/edit-sl-tp",
    "https://docs.trade.mudrex.com/docs/reverse",
    "https://docs.trade.mudrex.com/docs/partial-close",
    "https://docs.trade.mudrex.com/docs/square-off",
    "https://docs.trade.mudrex.com/docs/get-position-history",
    "https://docs.trade.mudrex.com/docs/fees",
    "https://docs.trade.mudrex.com/docs/faq",
    "https://docs.trade.mudrex.com/docs/changelogs"
]

OUTPUT_DIR = Path("docs/training_materials")

def get_soup(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def clean_content(soup):
    """Extract and clean the main content"""
    # Try multiple selectors for main content
    content = (
        soup.find('article') or 
        soup.find('main') or 
        soup.find('div', class_='content') or
        soup.body
    )
    
    if not content:
        return None
        
    # Remove navigation, headers, footers
    for tag in content.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
        tag.decompose()
        
    # Get text
    text = content.get_text(separator='\n\n', strip=True)
    return text

def scrape_training_data():
    logger.info(f"Starting scrape of {len(LINKS)} pages...")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    for i, link in enumerate(LINKS):
        logger.info(f"[{i+1}/{len(LINKS)}] Scraping {link}")
        
        soup = get_soup(link)
        if not soup:
            continue
            
        content = clean_content(soup)
        if not content:
            logger.warning(f"No content found for {link}")
            continue
            
        # Get title
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Documentation"
        
        # Create filename from URL slug
        parsed_url = urlparse(link)
        slug = parsed_url.path.strip('/').split('/')[-1]
        if not slug:
            slug = "index"
        filename = f"{slug}.md"
        filepath = OUTPUT_DIR / filename
        
        # Create file content with metadata header
        file_content = f"""# {title}
Source: {link}
Date Scraped: {time.strftime('%Y-%m-%d')}

---

{content}
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            logger.info(f"Saved: {filename}")
            success_count += 1
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            
        # Be nice to the server
        time.sleep(0.5)
        
    logger.info(f"Scrape complete! {success_count}/{len(LINKS)} pages saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    scrape_training_data()
