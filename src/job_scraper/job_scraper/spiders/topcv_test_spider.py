import scrapy
import re

class TopcvTestSpider(scrapy.Spider):
    name = 'topcv_test'
    
    # Test cả 3 link: MB Bank (layout dị), Kamereo (brand chuẩn), và Link thường
    start_urls = [
        'https://www.topcv.vn/brand/nganhangthuongmaicophanquandoi/tuyen-dung/ai-software-engineer-python-go-c-c-backend-ai-agents-khoi-cong-nghe-thong-tin-2026td450888-j2143686.html',
        'https://www.topcv.vn/brand/kamereo/tuyen-dung/product-owner-j2167873.html',
        'https://www.topcv.vn/viec-lam/php-laravel-lead/2172185.html'
    ]


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
        # Extract the raw text from the <title> tag
        title_text = response.xpath('//title/text()').get(default='').strip()
        
        if title_text:
            # Use regex to extract the exact job title.
            # It captures everything after "Tuyển " or "Tuyển dụng " 
            # and stops before " làm việc tại", " tại", or " - "
            match = re.search(r'Tuyển\s+(?:dụng\s+)?(.*?)(?:\s+làm việc tại|\s+tại|\s+-)', title_text, re.IGNORECASE)
            
            if match:
                # Return the matched group containing the job title
                return match.group(1).strip()
            
            # Fallback cleanup just in case the title format is slightly different
            clean_title = re.sub(r'^Tuyển(?: dụng)?\s+', '', title_text, flags=re.IGNORECASE)
            return clean_title.split(' tại ')[0].strip()

        # Absolute fallback to h1 if the <title> tag is completely missing (extremely rare)
        texts = response.css('h1 *::text').getall()
        title = ' '.join([t.strip() for t in texts if t.strip()])
        return re.sub(r'^Ứng tuyển\s+', '', title, flags=re.IGNORECASE).strip()

    def get_tags(self, response, group_keyword):
        # Khu vực Tags của TopCV có class ổn định, cứ rà theo class là chuẩn
        groups = response.xpath('//div[contains(@class, "job-tags__group")]')
        for group in groups:
            name = group.xpath('.//div[contains(@class, "job-tags__group-name")]//text()').get(default="").strip().lower()
            if group_keyword in name:
                texts = group.xpath('.//a[contains(@class, "item")]//text()').getall()
                return [t.strip() for t in texts if t.strip()]
        return []

    def get_section(self, response, header_keyword):
        # THUẬT TOÁN ĐỊNH VỊ BÁM RỄ (Root-anchored positioning)
        # B1: Lấy toàn bộ các thẻ có khả năng là Tiêu đề
        headers = response.css('h2, h3, h4, .title')
        
        for header in headers:
            # B2: Rút text của tiêu đề ra, đưa về chữ thường để so sánh chống trượt
            header_text = ' '.join(header.css('*::text').getall()).strip().lower()
            
            # B3: Nếu đúng tiêu đề mình cần tìm (Ví dụ: có chữ "mô tả công việc")
            if header_keyword in header_text:
                # Nhảy lên thẻ div bọc ngoài cùng (parent) của tiêu đề này
                parent = header.xpath('..')
                
                # Cào toàn bộ text nằm bên trong thẻ bọc ngoài đó
                all_texts = parent.css('*::text').getall()
                header_texts_raw = header.css('*::text').getall()
                
                # Loại bỏ phần text của chính cái tiêu đề đi, chỉ lấy phần ruột
                content_texts = [t.strip() for t in all_texts if t not in header_texts_raw and t.strip()]
                return ' '.join(content_texts)
        
        return ""

    def get_benefits(self, response):
        benefits = self.get_section(response, 'quyền lợi')
        
        # Vét nốt các quyền lợi kiểu icon (Thiết bị làm việc, etc.) thường có ở trang Brand
        custom_items = response.css('.custom-form-job__item--content::text').getall()
        if custom_items:
            extra = ' | '.join([t.strip() for t in custom_items if t.strip()])
            benefits = f"{benefits} || Extra: {extra}" if benefits else f"Extra: {extra}"
            
        return benefits

    def get_location(self, response):
        location_text = self.get_section(response, 'địa điểm làm việc')
        
        # Bào sạch cái cục text hướng dẫn hành chính rườm rà
        location_text = re.sub(r'\(đã được cập nhật theo Danh mục Hành chính mới.*?\)', '', location_text, flags=re.IGNORECASE).strip()
        return location_text