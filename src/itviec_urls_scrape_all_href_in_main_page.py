import json
import requests
from bs4 import BeautifulSoup

url = 'https://itviec.com/' 
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
elements = soup.select('[data-controller="utm-tracking"]')

data_list = []

for el in elements:
    text = el.get_text(strip=True)
    href = el.get('href')
    

    if href:
        
        data_list.append({
            "text": text,
            "url": href
        })


file_name = 'itviec_urls.json'

with open(file_name, 'w', encoding='utf-8') as f:
    
    json.dump(data_list, f, indent=4, ensure_ascii=False)

print(f"Export successfully  {len(data_list)} to file '{file_name}'!")