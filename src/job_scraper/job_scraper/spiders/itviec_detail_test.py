import scrapy

class ItviecDetailTestSpider(scrapy.Spider):
    name = 'itviec_test'
    allowed_domains = ['itviec.com']
    
    
    start_urls = ['https://itviec.com/it-jobs/hn-hcm-product-owner-ai-platform-one-mount-group-1551'] 

    def parse(self, response):
        
        job_title = response.css('h1.ipt-xl-6::text').get()
        company_name = response.css('div.employer-name::text').get()
        
        location = response.xpath('//svg[contains(@class, "feather-icon")]/following-sibling::span/text()').get()
        
        posted_time = response.xpath('//span[contains(text(), "Posted")]/text()').get()
        working_model = response.xpath('//span[contains(text(), "At office") or contains(text(), "Hybrid") or contains(text(), "Remote")]/text()').get()

        skills = response.xpath('//div[contains(text(), "Skills:")]/following-sibling::div[1]/a/text()').getall()
        job_expertise = response.xpath('//div[contains(text(), "Job Expertise:")]/following-sibling::div[1]/a/text()').getall()
        job_domain = response.xpath('//div[contains(text(), "Job Domain:")]/following-sibling::div[1]/div/text()').getall()

        company_type = response.xpath('//div[contains(text(), "Company type")]/following-sibling::div/text()').get()
        company_industry = response.xpath('//div[contains(text(), "Company industry")]/following-sibling::div//text()').getall()
        company_size = response.xpath('//div[contains(text(), "Company size")]/following-sibling::div/text()').getall()
        country = response.xpath('//div[contains(text(), "Country")]/following-sibling::div//span/text()').get()
        working_days = response.xpath('//div[contains(text(), "Working days")]/following-sibling::div/text()').get()
        overtime_policy = response.xpath('//div[contains(text(), "Overtime policy")]/following-sibling::div/text()').get()

        reasons_to_join = response.xpath('//h2[contains(text(), "Top 3 reasons to join us")]/following-sibling::ul[1]').get()
        job_description = response.xpath('//h2[contains(text(), "Job description")]/following-sibling::p | //h2[contains(text(), "Job description")]/following-sibling::ul').getall()
        requirements = response.xpath('//h2[contains(text(), "Your skills and experience")]/following-sibling::p | //h2[contains(text(), "Your skills and experience")]/following-sibling::ul').getall()
        why_love_working_here = response.xpath('//h2[contains(text(), "Why you\'ll love working here")]/following-sibling::ul[1]').get()

        def clean_text(text):
            return text.strip() if text else None
            
        def clean_list(lst):
            return [t.strip() for t in lst if t.strip()] if lst else []

        yield {
            'job_url': response.url,
            'job_title': clean_text(job_title),
            'company_name': clean_text(company_name),
            'location': clean_text(location),
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
                'job_description': "".join(job_description) if job_description else None,
                'requirements': "".join(requirements) if requirements else None,
                'why_love_working_here': why_love_working_here
            }
        }