
import requests
import re
from bs4 import BeautifulSoup
import time
import os

BASE_URL = "https://mudrex653095807156433837.freshdesk.com"
START_URL = "https://mudrex653095807156433837.freshdesk.com/support/solutions/folders/1060000499077"
OUTPUT_FILE = "docs/support_faq.md"

def get_soup(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_articles():
    print(f"Starting scrape of {START_URL}")
    
    # 1. Get all article links from pagination
    article_links = []
    
    # We saw pages 1, 2, 3 in the previous view. Let's just try iterating through pages until no more.
    # Pattern seems to be .../page/2 etc.
    
    page = 1
    while True:
        url = START_URL if page == 1 else f"{START_URL}/page/{page}"
        print(f"Scanning page {page}: {url}")
        
        soup = get_soup(url)
        if not soup:
            break
            
        # Find article links
        # Looking at standard freshdesk structure, usually in 'article-list' or similar
        # Based on previous raw text, we just need to find hrefs that look like articles
        # The view_content_chunk showed links like: .../support/solutions/articles/1060000152308-...
        
        links_found_on_page = 0
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/support/solutions/articles/' in href:
                full_url = BASE_URL + href if href.startswith('/') else href
                if full_url not in article_links:
                    article_links.append(full_url)
                    links_found_on_page += 1
        
        print(f"Found {links_found_on_page} articles on page {page}")
        
        if links_found_on_page == 0:
            break
            
        # Check for "Next" button/link to decide if we continue? 
        # Or simpler: just try next page. If 404 or no content, we stop.
        # But Freshdesk might just show empty list.
        # Let's rely on links_found_on_page == 0 to stop.
        
        page += 1
        time.sleep(1) # Be nice
        
    print(f"Total distinct articles found: {len(article_links)}")
    
    # 2. Fetch each article content
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Mudrex API Support FAQs\n\n")
        f.write("Collated from Freshdesk Support Articles.\n\n")
        
        for i, link in enumerate(article_links):
            print(f"[{i+1}/{len(article_links)}] Fetching {link}")
            soup = get_soup(link)
            if not soup:
                continue
                
            # Extract Title
            title_tag = soup.find('h1') or soup.find('h2')
            title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
            
            # Extract Content
            # Usually in a div with class 'description' or 'article-body'
            content_div = soup.find('div', class_='description') or soup.find('article')
            
            if content_div:
                # Basic cleaning
                text = content_div.get_text(separator='\n', strip=True)
            else:
                text = "Could not extract content."
            
            f.write(f"## {title}\n\n")
            f.write(f"**Source**: {link}\n\n")
            f.write(f"{text}\n\n")
            f.write("---\n\n")
            
            time.sleep(0.5)

    print(f"Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_articles()
