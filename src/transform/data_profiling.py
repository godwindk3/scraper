from pathlib import Path
import json
import html
from bs4 import BeautifulSoup
import re

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DETAILS_DIR = BASE_DIR / "data" / "data_details" 

all_files = DATA_DETAILS_DIR.iterdir()


def jsonl_handle(file):
    with open(file, "r", encoding="utf-8") as f:
        
        rows = [json.loads(line) for line in f]
    if isinstance(rows, list) and len(rows) > 0:

        print("---Structure JSONL: LIST ---")
        print(f"Total items: {len(rows)}")

        first_row = rows[0]
        
        if isinstance(first_row, dict):

            print("Key in the first item:")
            print(list(first_row.keys()))

    print("=====" * 50)

def json_handle(file):
    with open(file, "r", encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list) and len(data) > 0:
        print("---Structure JSON: LIST ---")
        print(f"Total items: {len(data)}")
        print("Keys in the first item:")
        print(list(data[0].keys()))

    print("====" * 50)


def file_reader(all_files):
    for file in all_files:
        if file.suffix == ".json":
            json_handle(file)
        elif file.suffix == ".jsonl":
            jsonl_handle(file)


def clean_text(text):
    """
    Cleans string data by removing HTML tags, unescaping HTML entities,
    and removing excess whitespace.
    """
    if not isinstance(text, str):
        return text
    
    # Decode HTML entities (e.g., &nbsp; becomes a space)
    text = html.unescape(text)
    
    # Remove HTML tags using regex
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def flatten_and_clean_json(nested_json, separator='_'):
    """
    Flattens a nested JSON object and applies text cleaning to all string values.
    """
    flattened_dict = {}

    def flatten(current_item, parent_key=''):
        # Check if the current item is a dictionary
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                new_key = f"{parent_key}{key}{separator}" if parent_key else f"{key}{separator}"
                flatten(value, new_key)
                
        # Check if the current item is a list
        elif isinstance(current_item, list):
            for index, item in enumerate(current_item):
                new_key = f"{parent_key}{index}{separator}" if parent_key else f"{index}{separator}"
                flatten(item, new_key)
                
        # Base case: handle primitive data types and clean text
        else:
            cleaned_value = clean_text(current_item)
            flattened_dict[parent_key[:-len(separator)]] = cleaned_value

    # Start the recursive process
    flatten(nested_json)
    return flattened_dict

def process_and_filter_data(file_path, output_path, keys_to_keep):
    """
    Reads the JSON file, flattens, cleans HTML/Unicode, filters specific keys,
    and saves a beautified version.
    """
    # Load JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure data is a list for uniform processing
    if not isinstance(data, list):
        data = [data]
        
    processed_data = []
    
    for item in data:
        # Flatten and clean the current item
        flat_item = flatten_and_clean_json(item)
        
        # Filter only the requested keys
        filtered_item = {}
        for key in keys_to_keep:
            # Check if the key exists in the flattened item
            if key in flat_item:
                filtered_item[key] = flat_item[key]
            else:
                # Assign None (null in JSON) if the key is missing from the original data
                filtered_item[key] = None 
                
        processed_data.append(filtered_item)
        
    # Save the filtered data with nice indentation
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)
        
    print(f"Done! Cleaned, flattened, and filtered data saved to {output_path}")

# List of specific keys to keep in the final output
KEYS_TO_KEEP = [
    "title",
    "content",
    "benefits_v2_0_description",
    "company_display_name",
    "company_addresses_sort_addresses",
    "company_skills_str",
    "skills_str",
    "experiences_str",
    "job_levels_str",
    "detail_url",
    "benefits_original_0_value",
    "responsibilities_original",
    "requirements_original",
    "mapped_location"
]



topdev_path = DATA_DETAILS_DIR / "topdev_detail.json"
topdev_processed_path = DATA_DETAILS_DIR / "topdev_processed_detail.json"

# process_and_filter_data(topdev_path, topdev_processed_path, KEYS_TO_KEEP)

file_reader(all_files)