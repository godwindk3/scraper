import requests

url = 'https://itviec.com/it-jobs/ha-noi'

# Set headers to mimic a real browser/user
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print(f"Sending request to: {url}...")
response = requests.get(url, headers=headers)

# 1. Check the status code
print(f"Response Status Code: {response.status_code}")

if response.status_code == 200:
    print(" Connection successful (200 OK)!")
    
    # 2. Save the raw HTML content received by Python into a file for inspection
    with open('itviec_test_result.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
        
    print("Page content has been saved to 'itviec_test_result.html'.")
    print("Open this file in a browser or VS Code to see what Python actually receives.")
    
    # 3. Quickly check if the content length is suspiciously short (possible empty page)
    print(f"Downloaded content length: {len(response.text)} characters.")

elif response.status_code == 403:
    print("Access denied (403 Forbidden)! ITViec detected the request as a bot and blocked it.")
else:
    print(f"Encountered another error: {response.status_code}")