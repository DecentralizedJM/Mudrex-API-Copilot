
import requests
from bs4 import BeautifulSoup
import time
import os

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

OUTPUT_DIR = "docs"

def get_soup(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_docs():
    print(f"Starting API docs scrape of {len(LINKS)} pages")
    
    with open(f"{OUTPUT_DIR}/mudrex_api_deep_reference.md", 'w', encoding='utf-8') as f:
        f.write("# Mudrex API Deep Reference\n\n")
        f.write("Collated from individual doc pages.\n\n")
        
        for i, link in enumerate(LINKS):
            print(f"[{i+1}/{len(LINKS)}] Fetching {link}")
            soup = get_soup(link)
            if not soup:
                continue
                
            # Extract content
            # Usually in main content area
            # Inspection of similar sites suggests 'main' or specific class
            content = soup.find('main') or soup.find('article') or soup.body
            
            if content:
                # Remove navigation if possible (heuristic)
                for nav in content.find_all('nav'):
                    nav.decompose()
                
                text = content.get_text(separator='\n', strip=True)
            else:
                text = "Could not extract content."
            
            slug = link.split('/')[-1]
            f.write(f"## {slug.replace('-', ' ').title()}\n")
            f.write(f"**Source**: {link}\n\n")
            f.write(f"{text}\n\n")
            f.write("---\n\n")
            
            time.sleep(0.5)

    print("Done! Saved to mudrex_api_deep_reference.md")

if __name__ == "__main__":
    scrape_docs()
