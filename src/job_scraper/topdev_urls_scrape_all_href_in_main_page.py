import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin 

url = 'https://topdev.vn/jobs/search?region_ids=79' 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Select all anchor tags
elements = soup.select('a')

data_list = []

for el in elements:
    text = el.get_text(strip=True)
    href = el.get('href')
    
    # Check if href exists and skip empty or javascript triggers
    if href and not href.startswith('javascript:'):
        
        # Convert relative URLs to absolute URLs
        absolute_url = urljoin(url, href)
        
        data_list.append({
            "text": text,
            "url": absolute_url
        })

file_name = 'topdev_urls.json'

# Open file and write data
with open(file_name, 'w', encoding='utf-8') as f:
    json.dump(data_list, f, indent=4, ensure_ascii=False)

print(f"Exported successfully {len(data_list)} URLs to file '{file_name}'!")