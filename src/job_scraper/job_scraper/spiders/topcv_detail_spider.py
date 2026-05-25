import scrapy
import json
import re
import random
from pathlib import Path

class TopcvDetailSpider(scrapy.Spider):
    name = 'topcv_detail'
    allowed_domains = ['topcv.vn']

    
    custom_settings = {
    'ROBOTSTXT_OBEY': False,
    'COOKIES_ENABLED': False,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 16,      # Giảm xuống 1
    'DOWNLOAD_DELAY': 2,                      # Tăng delay
    'RANDOMIZE_DOWNLOAD_DELAY': True,
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 5,
    'AUTOTHROTTLE_MAX_DELAY': 25,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 8,
    
    # Thêm headers ngẫu nhiên
    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
    },
    }

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
        # Chrome Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        
        # Chrome macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        
        # Firefox
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0',
        
        # Edge
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
        
        # Mobile (rất hữu ích để đa dạng fingerprint)
        'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 18_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Mobile/15E148 Safari/604.1',
        
        # Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    ]

    async def start(self):
        # Trỏ chính xác đến file URLs của mày bằng Path
        file_path = Path(__file__).resolve().parents[3] / 'topcv_urls.json'

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                urls = data.get('job_urls', [])
        except FileNotFoundError:
            self.logger.error(f"Không tìm thấy file tại: {file_path}")
            return

        self.logger.info(f"Bắt đầu cào {len(urls)} URLs...")

        for url in urls:
            # Xoay vòng User-Agent để lách tường lửa
            headers = {'User-Agent': random.choice(self.USER_AGENTS)}
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        yield {
            'url': response.url,
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
        title_text = response.xpath('//title/text()').get(default='').strip()
        
        if title_text:
            match = re.search(r'Tuyển\s+(?:dụng\s+)?(.*?)(?:\s+làm việc tại|\s+tại|\s+-)', title_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            clean_title = re.sub(r'^Tuyển(?: dụng)?\s+', '', title_text, flags=re.IGNORECASE)
            return clean_title.split(' tại ')[0].strip()

        texts = response.css('h1 *::text').getall()
        title = ' '.join([t.strip() for t in texts if t.strip()])
        return re.sub(r'^Ứng tuyển\s+', '', title, flags=re.IGNORECASE).strip()

    def get_tags(self, response, group_keyword):
        groups = response.xpath('//div[contains(@class, "job-tags__group")]')
        for group in groups:
            name = group.xpath('.//div[contains(@class, "job-tags__group-name")]//text()').get(default="").strip().lower()
            if group_keyword in name:
                texts = group.xpath('.//a[contains(@class, "item")]//text()').getall()
                return [t.strip() for t in texts if t.strip()]
        return []

    def get_section(self, response, header_keyword):
        headers = response.css('h2, h3, h4, .title')
        for header in headers:
            header_text = ' '.join(header.css('*::text').getall()).strip().lower()
            if header_keyword in header_text:
                parent = header.xpath('..')
                all_texts = parent.css('*::text').getall()
                header_texts_raw = header.css('*::text').getall()
                
                content_texts = [t.strip() for t in all_texts if t not in header_texts_raw and t.strip()]
                return ' '.join(content_texts)
        return ""

    def get_benefits(self, response):
        benefits = self.get_section(response, 'quyền lợi')
        
        custom_items = response.css('.custom-form-job__item--content::text').getall()
        if custom_items:
            extra = ' | '.join([t.strip() for t in custom_items if t.strip()])
            benefits = f"{benefits} || Extra: {extra}" if benefits else f"Extra: {extra}"
            
        return benefits

    def get_location(self, response):
        location_text = self.get_section(response, 'địa điểm làm việc')
        location_text = re.sub(r'\(đã được cập nhật theo Danh mục Hành chính mới.*?\)', '', location_text, flags=re.IGNORECASE).strip()
        return location_text