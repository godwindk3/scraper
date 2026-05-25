import scrapy
from urllib.parse import urlparse, urlunparse

class ItviecUrlsCrawlSpider(scrapy.Spider):
    name = 'itviec_urls'
    
    allowed_domains = ['itviec.com']
    
    start_urls = [
        'https://itviec.com/it-jobs/ha-noi',
        'https://itviec.com/it-jobs/ho-chi-minh-hcm',
        'https://itviec.com/it-jobs/da-nang',
        'https://itviec.com/it-jobs/others'
    ]

    def parse(self, response):
        job_urls = response.css('h3[data-url]::attr(data-url)').getall()
        
        if not job_urls:
            self.logger.warning(f"Can't find any job at {response.url}")
            self.logger.warning("HTML export to check")
            with open("cloudflare_block.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            return 
        
       
        for raw_url in job_urls:
            full_url = response.urljoin(raw_url)
            parsed_url = urlparse(full_url)
            clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
            
            yield {
                'job_url': clean_url,
                'source_page': response.url
            }

        next_page = response.xpath(
            '//link[@rel="next"]/@href | '
            '//a[@rel="next"]/@href | '
            '//a[contains(@class, "next")]/@href'
        ).get()
        
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(
                url=next_page_url, 
                callback=self.parse,
                headers={'Referer': response.url} 
            )