import scrapy
import json
from urllib.parse import urlencode

class TopdevApiSpider(scrapy.Spider):
    name = 'topdev_api'
    
    # Base URL without parameters
    base_url = 'https://api.topdev.vn/td/v2/jobs/search/v2'
    
    # Configure Scrapy settings to avoid overwhelming the server
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }

    # Mapping dictionary to convert ID to readable location
    region_mapping = {
        '01': 'Ha Noi',
        '79': 'Ho Chi Minh',
        '048': 'Da Nang'
    }

    # Define cookies (Keep your original cookies here)
    cookies = {
        'XSRF-TOKEN': 'eyJpdiI6ImFwZVRoVWIrQ2NOR0kzRWlxT1hESnc9PSIsInZhbHVlIjoiTG1iR2NnNm84c3RsT1VxOUhvWjhoY0dqNk96bmc0cUtCOHQ3QVNRYXc0WkVBRU9NVGduQVF5QmlHa0pvQnMvYU9Xd2k0cHFYQmJVcXg5QmlUc3RpRmhZZ1htSnZtNlRyK3RqZ1lxeXU4a1FQem1WbTRYWjFVcHY2S3JBVGR5STYiLCJtYWMiOiJjZmNkZDEwMDgzZTQ5ZmVlNzc5ZjgyMzE3ZmE0Y2RjZDNiOTI3MTAzMzZhNWE5ZjZiMzA3MGMzZGFiZmY5OWMwIiwidGFnIjoiIn0%3D',
    }

    # Define headers
    headers = {
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://topdev.vn',
        'referer': 'https://topdev.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    }

    async def start(self):
        # Initiate the first request for each region defined in the dictionary
        for region_id in self.region_mapping.keys():
            self.logger.info(f"Starting scrape for region {region_id} ({self.region_mapping[region_id]})")
            yield self.build_request(region_id, page=1)

    def build_request(self, region_id, page):
        # Construct parameters dictionary
        params = {
            'region_ids': region_id,
            'page': page,
            'fields[job]': 'id,title,salary,slug,company,expires,extra_skills,skills_str,skills_arr,skills_ids,job_types_str,job_levels_str,job_levels_arr,job_levels_ids,addresses,status_display,detail_url,job_url,salary,published,refreshed,applied,candidate,requirements_arr,packages,benefits,content,features,contract_types_ids,is_free,is_basic,is_basic_plus,is_distinction,level,contract_types_str,experiences_str,benefits_v2,services,job_category_id',
            'fields[company]': 'tagline,addresses,skills_arr,industries_arr,industries_ids,industries_str,image_cover,image_galleries,num_job_openings,company_size,nationalities_str,skills_str,skills_ids,benefits,num_employees',
            'locale': 'en_US'
        }
        
        # Create the full URL with query parameters
        full_url = f"{self.base_url}?{urlencode(params)}"
        
        # Pass region_id and page in the meta dict to track pagination state
        return scrapy.Request(
            url=full_url,
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse,
            meta={'region_id': region_id, 'page': page}
        )

    def parse(self, response):
        # Retrieve state from meta
        region_id = response.meta['region_id']
        current_page = response.meta['page']
        
        # Parse the JSON response
        try:
            json_response = response.json()
            jobs = json_response.get('data', [])
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON on region {region_id}, page {current_page}")
            return

        # Check stopping condition: if the array is empty, stop paginating for this region
        if not jobs:
            self.logger.info(f"No more data for region {region_id} on page {current_page}. Stopping.")
            return
            
        self.logger.info(f"Scraped {len(jobs)} jobs from region {region_id}, page {current_page}")

        # Yield each job as an item with the location injected
        for job in jobs:
            # Inject the readable location name into the job data
            job['mapped_location'] = self.region_mapping.get(region_id, 'Unknown')
            yield job
            
        # Trigger the request for the next page automatically
        next_page = current_page + 1
        yield self.build_request(region_id, next_page)