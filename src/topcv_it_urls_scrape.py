import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os

# Base URL setup
BASE_URL = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257?type_keyword=1&page={}&category_family=r257&saturday_status=0"
OUTPUT_FILE = "topcv_urls.json"
YOUR_BROWSER_COOKIE = '_ga=GA1.2.362508722.1756093392; _ga_F385SHE0Y3=GS2.1.s1757649272$o2$g1$t1757649290$j42$l0$h0; _taid=zijv0oYGcY.1777861930881; popup-ebook-cv=1; _tafp=f3abbc73cac1e8d2444841d1914d017b; popup-anti-scam=false; _tasid=RTIVKqSyAv.1779680336819; appier=%7B%22event%22%3A%22job_searched%22%2C%22payload%22%3A%7B%22searched_keyword%22%3A%22%22%2C%22job_category%22%3A%22%22%2C%22company_category%22%3A%22%22%2C%22work_location%22%3A%22%22%7D%7D; cf_clearance=tHp5Ll7pkfTaKATb6AHjn3wxakx912fI.qpjb.wIw.0-1779682111-1.2.1.1-1XQicYJaL.HYc1W74.WqDeB.eJENa_bG7hpBAWsAzVmx7FsF1.xtabdqs8aLt7obm4cyZakuMQfvywGLFld1a3gxIYCyWTCaOhna65arPwdVb14FWOlNnmTz3LEElKkADvzmWSY1iySurTOhXwBass8N3HvT4SWBrc8nxtbJeZZueltI5OdLbrA9sMKJaZYZ6kXZj2Z1Tk.1yr1wVeCtNUWA66VWJiAIVJuTfxELV_xO9Dn.WKis2aQZgD5yMsWQvvi1LaNz5IQaIWuB0jQG420ey7Uzns2O0vYg9Qlq3Y_QkwQWi7XJ5BuvudmnbTFm1UI3W490daPh.7y.WmroE29aIekExgTzPJ2WyWEcTYUbK_28cudXy8uapjpDQ4rYZuyFJUP4ZbCPzCVfwRVUbx6hDkQl8YMGAfGKGuSm39Q; _tasla=1779682135431; g_state={"i_l":0,"i_ll":1779682135951,"i_b":"rVW6+jHgsff+nJUOtaWT+B1G8wXwR2Ui4sclF+4535M","i_e":{"enable_itp_optimization":0},"i_et":1776392569753}; ref_source_tracking_id=eyJpdiI6Im5GeWVFMTl0aCtVY1YzMUk0Zkx3MGc9PSIsInZhbHVlIjoiQkNiaDc4T2pZWnRXcGY5OUlIWG1DaUlSRVNaeFN0emQ4d2p5SFJTRGlqNmxNSENmU2Jyeit0dmFjR1c3TWFoYXRmaWI0Vjl4di9RQTB0RVZMdGRESDhQNzczUCtxSmh6RVVFMXBORitPR2s9IiwibWFjIjoiMTAwNDdhODYwYmExZDYyNzI3OTYzMTVjNGU5MjkzMWQ0ZTg3YzZmNDAwYjJiODBlZTg4MzViMTAyYzRkNTBjMiIsInRhZyI6IiJ9; XSRF-TOKEN=eyJpdiI6IlYvcVViOEpvSTFUTFEvVUF6TGsrOXc9PSIsInZhbHVlIjoiaGQ3Zm9mbVl0Q3Rac3FzQUV1VUVzUXpIWEszRzRqZ0R0YWd1LytlT1VhTWRkYkc1c0hPRWN6YWNOWlJ3ZGRsNmFsbW1XSUN0UitDK2tubElCNDN5L0RaaWxFN2l3cURyRis4UEQ2bTNhalh3dk0xWVQ2UitxOGRUbHA5MGZnNlciLCJtYWMiOiI5MThiMWU4OTc3NjIwYjIwMzhlMGQ3ZDQ4ZmFhZTkzZmNkMzJjMmQ5M2MzNTAzZTQ2YTAxM2UxYzZhYzEyYTY3IiwidGFnIjoiIn0%3D; topcv_session=eyJpdiI6IjFaYlRlaU5aZG9MOUxieVhXWC9EMkE9PSIsInZhbHVlIjoic05NSW9qNDY5WEtnSUEzV2VqbnltVGFnbkVEVVRiYnBHU0loc2h0ZkxXQ3pXN3NMZnJHWDRLdkphaXVuakJoOFVnTUpEYk9wMzRtWU5BNkgrdVB1UytuUFpwdHV4ZVZpLy9Nd243YllMYVJVdk5NVktIb1h2T21Gb3Rua2VBV0UiLCJtYWMiOiI0NWNmYTZkMTc4ZDE0ZTI3NmIwODBhOGZiNDEzNDA0ZGRlOGU3ZDUzNmI2Y2RmMTc4OTJmYTMxNTgyYWQwMWQwIiwidGFnIjoiIn0%3D'

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

def save_progress_incrementally(new_urls, filename):
    # Initialize empty data structure
    existing_data = {"total_jobs": 0, "job_urls": []}
    
    # Load existing data if the file already exists
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
    
    # Merge existing URLs with new ones and remove duplicates using set
    all_urls = list(set(existing_data.get("job_urls", []) + new_urls))
    
    output_data = {
        "total_jobs": len(all_urls),
        "job_urls": all_urls
    }
    
    # Write the updated data back to the JSON file immediately
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

def robust_scraper(start_page, max_pages):
    current_page = start_page

    while current_page <= max_pages:
        print(f"Scraping page {current_page}...")
        target_url = BASE_URL.format(current_page)
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": "https://www.topcv.vn/",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Cookie": YOUR_BROWSER_COOKIE
        }

        try:
            # Fetch HTML content with timeout
            response = requests.get(target_url, headers=headers, timeout=15)
            
            if response.status_code == 403:
                print(f"\n[CRITICAL] Blocked by 403 Forbidden at page {current_page}.")
                break
                
            if response.status_code == 404:
                print("Page not found (404). Reached the end.")
                break
                
            response.raise_for_status()

            # Parse DOM to find JSON-LD scripts
            soup = BeautifulSoup(response.text, "html.parser")
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            
            urls_on_current_page = []

            # Extract job URLs from the parsed scripts
            for script in json_ld_scripts:
                if not script.string:
                    continue
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        for obj in data:
                            if "mainEntity" in obj and "itemListElement" in obj["mainEntity"]:
                                job_items = obj["mainEntity"]["itemListElement"]
                                for element in job_items:
                                    if "item" in element and "url" in element["item"]:
                                        urls_on_current_page.append(element["item"]["url"])
                except json.JSONDecodeError:
                    continue

            # Stop pagination if no new URLs are found
            if not urls_on_current_page:
                print("No job URLs found. Stopping pagination.")
                break

            print(f"-> Found {len(urls_on_current_page)} jobs. Saving to disk...")
            
            # Save data to disk immediately after finishing the page
            save_progress_incrementally(urls_on_current_page, OUTPUT_FILE)
            
            current_page += 1

            # Sleep to prevent getting blocked again
            sleep_time = random.uniform(5.0, 10.0)
            print(f"Sleeping for {sleep_time:.2f} seconds...\n")
            time.sleep(sleep_time)

        except requests.exceptions.RequestException as e:
            print(f"Network error on page {current_page}: {e}")
            break

if __name__ == "__main__":
    # Start fresh from page 1 since previous data was not saved
    robust_scraper(start_page=57, max_pages=150)