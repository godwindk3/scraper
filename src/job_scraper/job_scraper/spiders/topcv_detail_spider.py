import scrapy
import json
import re
from pathlib import Path

class TopcvDetailSpider(scrapy.Spider):
    name = 'topcv_detail'
    allowed_domains = ['topcv.vn']

    # --- UPDATED SETTINGS FOR PLAYWRIGHT ---
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True, # Playwright works better with cookies enabled for Cloudflare
        'CONCURRENT_REQUESTS': 2, # Keep it low, Playwright browsers consume a lot of RAM
        'DOWNLOAD_DELAY': 5,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        
        # 1. Required reactor for Playwright to handle async operations in Scrapy
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        
        # 2. Replace impersonate handlers with Playwright handlers
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        
        # 3. Playwright specific configurations
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True, # Set to False if you want to watch the browser UI
            'timeout': 30000, # 30 seconds timeout to allow slow loading
        },
        
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 7,
        'AUTOTHROTTLE_MAX_DELAY': 30,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1,
    }
    # custom_settings = {
    #     'ROBOTSTXT_OBEY': False,
    #     'COOKIES_ENABLED': True,
        
    #     # --- TỐI ƯU CHO 32GB RAM ---
    #     'CONCURRENT_REQUESTS': 8,             # Mở 8 tab cùng lúc. Quá an toàn cho 32GB RAM (chỉ tốn cỡ 2-3GB).
    #     'CONCURRENT_REQUESTS_PER_DOMAIN': 8,  # Giới hạn số lượng request đồng thời vào chung 1 domain (topcv).
        
    #     # --- TINH CHỈNH PLAYWRIGHT ---
    #     'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    #     'DOWNLOAD_HANDLERS': {
    #         'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    #         'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
    #     },
    #     'PLAYWRIGHT_LAUNCH_OPTIONS': {
    #         'headless': True,
    #         'timeout': 30000,
    #     },
    #     # Tối ưu hóa Context của Playwright để dùng chung tài nguyên RAM/CPU tốt hơn
    #     'PLAYWRIGHT_MAX_CONTEXTS': 1,         
    #     'PLAYWRIGHT_MAX_PAGES_PER_CONTEXT': 8, 
        
    #     # --- ÉM NHẸM TỐC ĐỘ (TRÁNH CLOUDFLARE) ---
    #     'DOWNLOAD_DELAY': 2,                  # Giảm thời gian chờ giữa các request xuống 2 giây (trước là 5s)
    #     'RANDOMIZE_DOWNLOAD_DELAY': True,     # Scrapy sẽ random chờ từ 1s đến 3s để giả làm người thật
        
    #     'AUTOTHROTTLE_ENABLED': True,
    #     'AUTOTHROTTLE_START_DELAY': 2,
    #     'AUTOTHROTTLE_MAX_DELAY': 15,         # Nếu server TopCV phản hồi chậm lại, tối đa chỉ đợi 15s rồi ép chạy tiếp
    #     'AUTOTHROTTLE_TARGET_CONCURRENCY': 8,
    # }

    # Changed from 'async def start' to standard Scrapy 'start_requests'
    async def start(self):
        # Locate the JSON file containing all job URLs
        input_path = Path(__file__).resolve().parents[3] / 'topcv_urls.json'
        
        # Define the output file path. Always use JSONLines (.jsonl) for pausing/resuming
        output_path = Path(__file__).resolve().parents[3] / 'topcv_detail.jsonl'

        scraped_urls = set()

        # Step 1: Read the output file if it exists to find already scraped URLs
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if 'url' in data:
                            scraped_urls.add(data['url'])
                    except json.JSONDecodeError:
                        # Skip corrupted lines
                        continue

        # Step 2: Load the initial target URLs
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_urls = data.get('job_urls', [])
        except FileNotFoundError:
            self.logger.error(f"Cannot find input file at: {input_path}")
            return

        # Step 3: Filter out URLs that are already in the scraped set
        pending_urls = [url for url in all_urls if url not in scraped_urls]

        # Log the progress status
        self.logger.info(f"Total: {len(all_urls)} | Scraped: {len(scraped_urls)} | Pending: {len(pending_urls)}")

        if not pending_urls:
            self.logger.info("All URLs have been scraped. Stopping spider.")
            return

        # Step 4: Yield requests only for the pending URLs
        for url in pending_urls:
            yield scrapy.Request(
                url=url, 
                callback=self.parse,
                meta={
                    # Instruct Scrapy to route this request through the Playwright browser
                    'playwright': True,
                    'original_url': url
                }
            )

    def parse(self, response):
        # Check if we hit a Cloudflare block (usually 403 or title contains specific text)
        if response.status in [403, 1020] or "Just a moment" in response.css('title::text').get(default=""):
            self.logger.warning(f"Blocked by Cloudflare on {response.url}")
            return

        yield {
            'url': response.meta.get('original_url', response.url),
            'job_title': self.get_job_title(response),
            'requirement_tags': self.get_tags(response, 'yêu cầu'),
            'benefit_tags': self.get_tags(response, 'quyền lợi'),
            'expertise_tags': self.get_tags(response, 'chuyên môn'),
            'job_description': self.get_section(response, 'mô tả công việc'),
            'candidate_requirements': self.get_section(response, 'yêu cầu ứng viên'),
            'detailed_benefits': self.get_benefits(response),
            'location': self.get_location(response),
            'working_time': self.get_section(response, 'thời gian làm việc')
        }

    def get_job_title(self, response):
        # Extract title from meta tags or main h1 header
        title_text = response.css('h1.job-detail__info--title *::text').getall()
        if not title_text:
            title_text = [response.xpath('//title/text()').get(default='').strip()]
            
        title = ' '.join([t.strip() for t in title_text if t.strip()])
        
        # Clean up common prefixes used in Vietnamese job postings
        clean_title = re.sub(r'^(Tuyển dụng|Tuyển|Ứng tuyển)\s+', '', title, flags=re.IGNORECASE)
        return clean_title.split(' - ')[0].strip()

    def get_tags(self, response, group_keyword):
        # Locate the specific tag group based on the keyword
        groups = response.xpath('//div[contains(@class, "job-tags__group")]')
        for group in groups:
            name = group.xpath('.//div[contains(@class, "job-tags__group-name")]//text()').get(default="").strip().lower()
            if group_keyword in name:
                texts = group.xpath('.//a[contains(@class, "item")]//text()').getall()
                return [t.strip() for t in texts if t.strip()]
        return []

    def get_section(self, response, header_keyword):
        # Find headers and extract the following sibling content block
        headers = response.css('h2, h3, h4, .title')
        for header in headers:
            header_text = ' '.join(header.css('*::text').getall()).strip().lower()
            if header_keyword in header_text:
                # Extract text from the immediate next div or content wrapper
                content_node = header.xpath('following-sibling::div[1]')
                if content_node:
                    content_texts = content_node.css('*::text').getall()
                    # Clean and format the extracted text
                    cleaned_texts = [t.strip() for t in content_texts if t.strip()]
                    return '\n'.join(cleaned_texts)
        return ""

    def get_benefits(self, response):
        benefits = self.get_section(response, 'quyền lợi')
        
        # Check for alternative layout formats
        custom_items = response.css('.custom-form-job__item--content::text').getall()
        if custom_items:
            extra = ' | '.join([t.strip() for t in custom_items if t.strip()])
            benefits = f"{benefits}\nExtra: {extra}" if benefits else f"Extra: {extra}"
            
        return benefits.strip()

    def get_location(self, response):
        location_text = self.get_section(response, 'địa điểm làm việc')
        # Remove administrative boundary updates notes
        location_text = re.sub(r'\(đã được cập nhật theo Danh mục Hành chính mới.*?\)', '', location_text, flags=re.IGNORECASE).strip()
        # Replace newlines with commas for address formatting
        return location_text.replace('\n', ', ')