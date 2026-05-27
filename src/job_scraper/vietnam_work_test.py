import urllib.parse
import json
from playwright.sync_api import sync_playwright

def scrape_vietnamworks_combined(base_url: str, max_pages: int = 5):
    # List to store all scraped job data across all pages
    all_links_data = []

    with sync_playwright() as p:
        # Launch browser (headless=False to see it in action)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Outer loop: Iterate through pagination (page 1, 2, 3...)
        for page_num in range(1, max_pages + 1):
            current_url = f"{base_url}&page={page_num}"
            print(f"\n{'='*40}")
            print(f"🚀 [PAGE {page_num}/{max_pages}] Navigating to: {current_url}")
            
            page.goto(current_url)

            try:
                # Wait for the first job elements to appear on the new page
                page.wait_for_selector("h2 > a", timeout=15000)
            except Exception:
                print(f"❌ Failed to load data on page {page_num}. Ending pagination.")
                break

            print("⏳ Scrolling down to lazy-load all items on this page...")
            
            # Inner loop variables for infinite scroll on the CURRENT page
            previous_item_count = 0
            retries = 0
            max_retries = 3

            # Inner loop: Scroll to the bottom until no new items appear
            while True:
                # Press 'End' to jump to the bottom
                page.keyboard.press("End")
                
                # Wait for network request to return lazy-loaded jobs
                page.wait_for_timeout(2000)
                
                # Count current elements in the DOM
                current_item_count = page.locator("h2 > a").count()
                
                if current_item_count == previous_item_count:
                    retries += 1
                    # If retried 3 times and count doesn't increase, we hit the bottom of this page
                    if retries >= max_retries:
                        print(f"✅ Reached the bottom of page {page_num}. Total items: {current_item_count}")
                        break
                else:
                    # Reset retries if new items successfully loaded
                    retries = 0
                    previous_item_count = current_item_count

            print("📥 Extracting data from this page...")
            
            # Extract data from all elements rendered on the current page
            elements = page.locator("h2 > a").all()
            
            for el in elements:
                title = el.inner_text().strip()
                href = el.get_attribute("href")
                
                if href:
                    # Resolve relative URL to absolute URL
                    full_url = urllib.parse.urljoin(current_url, href)
                    all_links_data.append({
                        "title": title,
                        "url": full_url
                    })

        # Close browser when all pages are done
        browser.close()
        return all_links_data

if __name__ == "__main__":
    target_base_url = "https://www.vietnamworks.com/viec-lam?g=5" 
    
    # Run the scraper for 5 pages (adjust max_pages as needed)
    results = scrape_vietnamworks_combined(target_base_url, max_pages=30)

    print(f"\n🎉 SUCCESSFULLY SCRAPED {len(results)} TOTAL ITEMS.")
    
    # Save output to JSON file with UTF-8 to handle Vietnamese text
    output_file = "vietnamwork_urls.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        
    print(f"💾 Data saved to {output_file}")