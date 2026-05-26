import scrapy
import json
import re
from pathlib import Path
from scrapy.selector import Selector

class VietnamworkDetailSpider(scrapy.Spider):
    name = 'vietnamwork_detail'
    allowed_domains = ['vietnamworks.com']

    # --- SCRAPY & PLAYWRIGHT SETTINGS ---
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'CONCURRENT_REQUESTS': 4, # Giữ ở mức vừa phải để Playwright chạy mượt
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        
        # Playwright handlers
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True, 
            'timeout': 30000,
        },
        'PLAYWRIGHT_MAX_CONTEXTS': 1,
        'PLAYWRIGHT_MAX_PAGES_PER_CONTEXT': 4,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define absolute paths dynamically
        self.input_path = Path(__file__).resolve().parents[3] / 'vietnamwork_urls.json'
        self.output_path = Path(__file__).resolve().parents[3] / 'vietnamwork_detail.jsonl'

    async def start(self):
        scraped_urls = set()

        # 1. Read existing output to prevent duplicate scraping (Resume capability)
        if self.output_path.exists():
            with open(self.output_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if 'url' in data:
                            scraped_urls.add(data['url'])
                    except json.JSONDecodeError:
                        continue # Skip broken lines

        # 2. Load the input file
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"❌ Input file not found at: {self.input_path}")
            return

        # 3. Filter URLs and track pending tasks
        pending_jobs = [job for job in jobs_data if job.get('url') and job['url'] not in scraped_urls]
        
        self.logger.info(f"📊 Total: {len(jobs_data)} | Already Scraped: {len(scraped_urls)} | Pending: {len(pending_jobs)}")

        if not pending_jobs:
            self.logger.info("✅ All jobs scraped successfully. Spider is stopping.")
            return

        # 4. Dispatch requests for pending URLs
        for job in pending_jobs:
            yield scrapy.Request(
                url=job['url'],
                callback=self.parse,
                meta={
                    # Instruct Playwright to pass the Page object to the parse method
                    # so we can interact with it (click buttons)
                    'playwright': True,
                    'playwright_include_page': True, 
                    'original_url': job['url'], # Store for deduplication

                    'playwright_page_goto_kwargs': {
                        # domcontentloaded: Chỉ đợi HTML tải xong, mặc kệ ảnh và CSS/JS load chậm
                        'wait_until': 'domcontentloaded', 
                        # Nâng mức chịu đựng lên 60 giây (60000ms) thay vì 30 giây mặc định
                        'timeout': 60000, 
                    }

                }
            )

    # Note: parse MUST be an async function when using playwright_include_page
    async def parse(self, response):
        page = response.meta.get("playwright_page")
        original_url = response.meta.get("original_url", response.url)
        
        # Check for Cloudflare/Access blocks just in case
        if response.status in [403, 1020] or "Just a moment" in response.css('title::text').get(default=""):
            self.logger.warning(f"🚫 Blocked on {original_url}")
            await page.close()
            return

        try:
            # --- UI INTERACTION: CLICK EXPAND BUTTONS ---
            # Locate all buttons that might hide text based on aria-labels
            button_locators = page.locator('button[aria-label="Xem đầy đủ mô tả công việc"], button[aria-label="Xem thêm"]')
            
            # Fetch the total count of such buttons on the page
            count = await button_locators.count()
            
            for i in range(count):
                btn = button_locators.nth(i)
                try:
                    # If button is visible, click it to expand the DOM
                    if await btn.is_visible(timeout=1000):
                        await btn.click(timeout=2000)
                        # Wait 0.5 seconds for the JavaScript animation/DOM update to finish
                        await page.wait_for_timeout(500)
                except Exception as e:
                    # Ignore individual button errors (e.g., button disappeared) and continue
                    self.logger.debug(f"Could not click a button on {original_url}: {e}")

            # Extract the fully rendered HTML after all clicks are processed
            full_html = await page.content()
            
            # Create a new Scrapy selector from the fully rendered HTML
            sel = Selector(text=full_html)
            
            # --- DATA EXTRACTION ---
            item = {
                'url': original_url,
                'job_title': self.clean_text(sel.css('h1[name="title"] *::text').getall()),
                'job_description': self.get_section(sel, 'Mô tả công việc'),
                'candidate_requirements': self.get_section(sel, 'Yêu cầu công việc'),
                'benefits': self.get_section(sel, 'Các phúc lợi dành cho bạn', has_vnwLayout=True),
                'job_info': self.get_section(sel, 'Thông tin việc làm', has_vnwLayout=True),
                'location': self.get_section(sel, 'Địa điểm làm việc', has_vnwLayout=True)
            }

            # --- MANUAL SAVE TO AVOID '-o' FLAG ISSUES ---
            # Using append mode ('a') guarantees safe pausing/resuming
            with open(self.output_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
            self.logger.info(f"✅ Saved: {item['job_title']}")
            
            # Yield for Scrapy stats tracking
            yield item

        except Exception as e:
            self.logger.error(f"❌ Error parsing {original_url}: {e}")
        finally:
            # CRITICAL: Always close the Playwright page to free up memory
            await page.close()

    # --- HELPER FUNCTIONS ---
    
    # def get_section(self, selector, header_text, has_vnwLayout=False):
    #     """
    #     Dynamically locate a section based on its header text and extract its content.
    #     """
    #     if has_vnwLayout:
    #         # Pattern: <h2>...</h2> followed by <div id="vnwLayout__row">
    #         xpath_query = f'//h2[contains(text(), "{header_text}")]/following-sibling::div[@id="vnwLayout__row"][1]//text()'
    #     else:
    #         # Pattern: <h2>...</h2> followed by a generic <div>
    #         xpath_query = f'//h2[contains(text(), "{header_text}")]/following-sibling::div[1]//text()'
            
    #     raw_texts = selector.xpath(xpath_query).getall()
    #     return self.clean_text(raw_texts, join_char='\n')

    def get_section(self, selector, header_text, has_vnwLayout=False):
        """
        Dynamically locate a section based on its header text.
        Handles cases where ad/premium banners are injected between the h2 and the actual content.
        """
        if has_vnwLayout:
            # Pattern for sections using grid layouts (vnwLayout__row)
            xpath_query = f'(//h2[normalize-space(text())="{header_text}"])[1]/following-sibling::div[@id="vnwLayout__row"][1]//text()'
            raw_texts = selector.xpath(xpath_query).getall()
            return self.clean_text(raw_texts, join_char='\n')
        else:
            # Get the exact h2 header
            h2_xpath = f'(//h2[normalize-space(text())="{header_text}"])[1]'
            
            # Fetch the first 3 sibling divs immediately following the h2
            # This bypasses dynamically injected banner divs (like the premium matching feature)
            siblings_xpath = f'{h2_xpath}/following-sibling::div[position() <= 3]'
            
            candidate_nodes = selector.xpath(siblings_xpath)
            
            best_text = ""
            for node in candidate_nodes:
                raw_texts = node.xpath('.//text()').getall()
                cleaned_text = self.clean_text(raw_texts, join_char='\n')
                
                # The actual job description/requirements will always be significantly longer than a single banner sentence
                if len(cleaned_text) > len(best_text):
                    best_text = cleaned_text
                    
            return best_text

    def clean_text(self, text_list, join_char=' '):
        """
        Clean arrays of text strings, removing excessive whitespaces and blanks.
        """
        if not text_list:
            return ""
        # Strip each text block and filter out empty strings
        cleaned = [t.strip() for t in text_list if t.strip()]
        return join_char.join(cleaned)