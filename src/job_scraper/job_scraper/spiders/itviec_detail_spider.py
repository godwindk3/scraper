import scrapy
import json
from pathlib import Path # Import Path instead of os

class ItviecDetailSpider(scrapy.Spider):
    name = 'itviec_detail'
    allowed_domains = ['itviec.com']


    async def start(self):
        # 1. Get the absolute path of the current file, 
        # go up 3 levels (parents[2]) to the outer 'job_scraper' directory,
        # and join the filename using the '/' operator
        file_path = Path(__file__).resolve().parents[2] / 'itviec_jobs_url.json'
        # Log the path for debugging purposes
        self.logger.info(f"Looking for JSON file at: {file_path}")
        
        # 2. Check if the file exists using pathlib's built-in .exists() method
        if not file_path.exists():
            self.logger.error(f"File not found at: {file_path}")
            return

        # 3. Load the JSON file (the built-in open() natively supports Path objects)
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                jobs = json.load(f)
            except json.JSONDecodeError:
                self.logger.error("Invalid JSON format. Please check the file.")
                return

        for job in jobs:
            job_url = job.get('job_url')
            source_page = job.get('source_page', '')

            if not job_url:
                continue

            # Parse the city location from the source_page URL 
            city_slug = source_page.split('/')[-1] if '/' in source_page else 'Unknown'
            
            # Special case for HCM because the URL slug is 'ho-chi-minh-hcm'
            if city_slug == 'ho-chi-minh-hcm':
                city_location = 'Ho Chi Minh'
            else:
                city_location = city_slug.replace('-', ' ').title()

            # Pass the parsed city_location to the parse callback using 'meta'
            yield scrapy.Request(
                url=job_url,
                callback=self.parse,
                meta={'city_location': city_location}
            )


    def parse(self, response):
        # Retrieve the city location passed from start_requests
        city_location = response.meta.get('city_location')

        # Helper function to extract and clean nested text without HTML tags
        def extract_clean_text(xpath_query):
            # The //text() automatically extracts text from all nested child nodes
            raw_texts = response.xpath(xpath_query + '//text()').getall()
            # Remove newlines, tabs, and filter out empty strings
            clean_texts = [text.replace('\n', ' ').strip() for text in raw_texts if text.strip()]
            # Join them with a space to form clean paragraphs
            return " ".join(clean_texts) if clean_texts else None

        # Helper function for cleaning simple text strings
        def clean_text(text):
            return text.replace('\n', ' ').strip() if text else None

        # Helper function for cleaning lists
        def clean_list(lst):
            return [t.replace('\n', ' ').strip() for t in lst if t.strip()] if lst else []

        # --- 1. Core Metadata ---
        job_title = response.css('h1.ipt-xl-6::text').get()
        company_name = response.css('div.employer-name::text').get()
        office_location = response.xpath('//svg[contains(@class, "feather-icon")]/following-sibling::span/text()').get()
        posted_time = response.xpath('//span[contains(text(), "Posted")]/text()').get()
        working_model = response.xpath('//span[contains(text(), "At office") or contains(text(), "Hybrid") or contains(text(), "Remote")]/text()').get()

        # --- 2. Categorical Data ---
        skills = response.xpath('//div[contains(text(), "Skills:")]/following-sibling::div[1]/a/text()').getall()
        job_expertise = response.xpath('//div[contains(text(), "Job Expertise:")]/following-sibling::div[1]/a/text()').getall()
        job_domain = response.xpath('//div[contains(text(), "Job Domain:")]/following-sibling::div[1]/div/text()').getall()

        company_type = response.xpath('//div[contains(text(), "Company type")]/following-sibling::div/text()').get()
        company_industry = response.xpath('//div[contains(text(), "Company industry")]/following-sibling::div//text()').getall()
        company_size = response.xpath('//div[contains(text(), "Company size")]/following-sibling::div/text()').getall()
        country = response.xpath('//div[contains(text(), "Country")]/following-sibling::div//span/text()').get()
        working_days = response.xpath('//div[contains(text(), "Working days")]/following-sibling::div/text()').get()
        overtime_policy = response.xpath('//div[contains(text(), "Overtime policy")]/following-sibling::div/text()').get()

        # --- 3. Unstructured Text (Stripped of HTML) ---
        reasons_to_join = extract_clean_text('//h2[contains(text(), "Top 3 reasons to join us")]/following-sibling::ul[1]')
        job_description = extract_clean_text('//h2[contains(text(), "Job description")]/following-sibling::p | //h2[contains(text(), "Job description")]/following-sibling::ul')
        requirements = extract_clean_text('//h2[contains(text(), "Your skills and experience")]/following-sibling::p | //h2[contains(text(), "Your skills and experience")]/following-sibling::ul')
        why_love_working_here = extract_clean_text('//h2[contains(text(), "Why you\'ll love working here")]/following-sibling::ul[1]')

        # --- Yield Final Item ---
        yield {
            'job_url': response.url,
            'job_title': clean_text(job_title),
            'company_name': clean_text(company_name),
            'city_location': city_location,
            'office_location': clean_text(office_location),
            'working_model': clean_text(working_model),
            'posted_time': clean_text(posted_time),
            'skills': clean_list(skills),
            'job_expertise': clean_list(job_expertise),
            'job_domain': clean_list(job_domain),
            'company_info': {
                'type': clean_text(company_type),
                'industry': " ".join(clean_list(company_industry)),
                'size': " ".join(clean_list(company_size)),
                'country': clean_text(country),
                'working_days': clean_text(working_days),
                'overtime_policy': clean_text(overtime_policy)
            },
            'text_data': {
                'reasons_to_join': reasons_to_join,
                'job_description': job_description,
                'requirements': requirements,
                'why_love_working_here': why_love_working_here
            }
        }