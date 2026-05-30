import json
from pathlib import Path

# Define the standard schema keys
CORE_KEYS = [
    "job_url", "job_title", "company_name", "location_raw", 
    "salary_raw", "job_description", "requirements", 
    "benefits", "skills", "source_platform"
]

def load_data(filepath: Path):
    """
    Read data from JSON or JSONL file using pathlib.Path 
    and return a list of dictionaries.
    """
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return []

    ext = filepath.suffix.lower()
    data_list = []

    try:
        if ext == '.jsonl':
            with filepath.open('r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data_list.append(json.loads(line))
        elif ext == '.json':
            with filepath.open('r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle cases where JSON contains a list of objects or a single object
                if isinstance(data, list):
                    data_list.extend(data)
                elif isinstance(data, dict):
                    data_list.append(data)
    except Exception as e:
        print(f"Error reading file {filepath.name}: {e}")
        
    return data_list

def extract_company_name(company_field):
    """
    Helper function to safely extract the company name 
    if it is nested within a dictionary object.
    """
    if isinstance(company_field, dict):
        # Fallback to various common keys inside the company object
        return company_field.get("name") or company_field.get("company_name") or str(company_field)
    return str(company_field) if company_field else None

# def standardize_item(raw_item, source_platform):
#     """
#     Map raw data to the core schema and push the remaining fields to metadata.
#     """
#     # Initialize all core fields with None (null in JSON)
#     std_item = {key: None for key in CORE_KEYS}
#     std_item["source_platform"] = source_platform
#     std_item["additional_metadata"] = {}
    
#     # Track keys that have been mapped to the core schema
#     mapped_keys = set()

#     def get_and_mark(key, default=None):
#         if key in raw_item:
#             mapped_keys.add(key)
#             return raw_item[key]
#         return default

#     # Mapping logic based on the source platform
#     if source_platform == "File1_JSON":
#         std_item["job_url"] = get_and_mark("job_url")
#         std_item["job_title"] = get_and_mark("job_title")
#         std_item["company_name"] = get_and_mark("company_name")
        
#         # Combine city and office locations
#         city = get_and_mark("city_location", "")
#         office = get_and_mark("office_location", "")
#         std_item["location_raw"] = f"{city} - {office}".strip(" -")
        
#         std_item["job_description"] = get_and_mark("text_data")
#         std_item["requirements"] = get_and_mark("job_domain")
        
#         # Combine different skill fields
#         skills_1 = get_and_mark("skills", [])
#         skills_2 = get_and_mark("job_expertise", [])
#         if isinstance(skills_1, list) and isinstance(skills_2, list):
#             std_item["skills"] = skills_1 + skills_2
#         else:
#             std_item["skills"] = [str(skills_1), str(skills_2)]

#     elif source_platform == "File2_JSONL":
#         std_item["job_url"] = get_and_mark("url")
#         std_item["job_title"] = get_and_mark("job_title")
#         std_item["location_raw"] = get_and_mark("location")
#         std_item["job_description"] = get_and_mark("job_description")
#         std_item["requirements"] = get_and_mark("candidate_requirements")
        
#         # Combine detailed benefits and benefit tags
#         ben_1 = get_and_mark("detailed_benefits", "")
#         ben_2 = get_and_mark("benefit_tags", [])
#         std_item["benefits"] = f"{ben_1} | {ben_2}"
        
#         std_item["skills"] = get_and_mark("requirement_tags", []) + get_and_mark("expertise_tags", [])

#     elif source_platform == "File3_JSON":
#         std_item["job_url"] = get_and_mark("detail_url") or get_and_mark("job_url")
#         std_item["job_title"] = get_and_mark("title")
#         std_item["company_name"] = extract_company_name(get_and_mark("company"))
#         std_item["location_raw"] = get_and_mark("mapped_location") or get_and_mark("addresses")
#         std_item["salary_raw"] = get_and_mark("salary")
#         std_item["job_description"] = get_and_mark("content")
#         std_item["requirements"] = get_and_mark("requirements_original") or get_and_mark("requirements_arr")
#         std_item["benefits"] =  get_and_mark("benefits_original")
#         std_item["skills"] = get_and_mark("skills_arr") or get_and_mark("skills_str")

#     elif source_platform == "File4_JSONL":
#         std_item["job_url"] = get_and_mark("url")
#         std_item["job_title"] = get_and_mark("job_title")
#         std_item["location_raw"] = get_and_mark("location")
#         std_item["job_description"] = get_and_mark("job_description")
#         std_item["requirements"] = get_and_mark("candidate_requirements")
#         std_item["benefits"] = get_and_mark("benefits")

#     # Push all unmapped/redundant keys into the additional_metadata field
#     for key, value in raw_item.items():
#         if key not in mapped_keys:
#             std_item["additional_metadata"][key] = value

#     return std_item

def standardize_item(raw_item, source_platform):
    # Khởi tạo bộ khung Nested Schema
    std_item = {
        "metadata": {
            "source": source_platform,
            "job_url": None
        },
        "job_info": {
            "title": None,
            "levels": [],
            "experience": None,
            "working_model": None
        },
        "company_info": {
            "name": None,
            "size": None,
            "industry": []
        },
        "location": {
            "city": None,
            "full_address": None
        },
        "salary": {
            "raw_text": None,
            "min": None,
            "max": None,
            "currency": None
        },
        "content": {
            "description": None,
            "requirements": None,
            "benefits": None
        },
        "tags": {
            "skills": []
        },
        # Backup lại dữ liệu gốc 100% để không bao giờ mất data ngầm
        "raw_data": raw_item 
    }

    # Bắt đầu mapping theo từng site
    if source_platform == "topdev":
        std_item["metadata"]["job_url"] = raw_item.get("detail_url")
        std_item["job_info"]["title"] = raw_item.get("title")
        std_item["job_info"]["levels"] = raw_item.get("job_levels_arr", [])
        std_item["job_info"]["experience"] = raw_item.get("experiences_str")
        std_item["job_info"]["working_model"] = raw_item.get("job_types_str")
        
        company_data = raw_item.get("company", {})
        std_item["company_info"]["name"] = company_data.get("display_name")
        std_item["company_info"]["size"] = company_data.get("company_size")
        std_item["company_info"]["industry"] = company_data.get("industries_arr", [])
        
        std_item["location"]["city"] = raw_item.get("mapped_location")
        addresses = raw_item.get("addresses", {})
        full_addrs = addresses.get("full_addresses", [])
        std_item["location"]["full_address"] = full_addrs[0] if full_addrs else None
        
        salary_data = raw_item.get("salary", {})
        std_item["salary"]["min"] = salary_data.get("min")
        std_item["salary"]["max"] = salary_data.get("max")
        std_item["salary"]["currency"] = salary_data.get("currency")
        
        std_item["content"]["description"] = raw_item.get("content")
        std_item["content"]["requirements"] = raw_item.get("requirements_original")
        std_item["content"]["benefits"] = str(raw_item.get("benefits_original", ""))
        std_item["tags"]["skills"] = raw_item.get("skills_arr", [])

    elif source_platform == "itviec":
        std_item["metadata"]["job_url"] = raw_item.get("job_url")
        std_item["job_info"]["title"] = raw_item.get("job_title")
        std_item["job_info"]["working_model"] = raw_item.get("working_model")
        
        std_item["company_info"]["name"] = raw_item.get("company_name")
        comp_info = raw_item.get("company_info", {})
        std_item["company_info"]["size"] = comp_info.get("size")
        std_item["company_info"]["industry"] = [comp_info.get("industry")] if comp_info.get("industry") else []
        
        std_item["location"]["city"] = raw_item.get("city_location")
        std_item["location"]["full_address"] = raw_item.get("office_location")
        
        text_data = raw_item.get("text_data", {})
        std_item["content"]["description"] = text_data.get("job_description")
        std_item["content"]["requirements"] = text_data.get("requirements")
        std_item["content"]["benefits"] = text_data.get("why_love_working_here")
        
        std_item["tags"]["skills"] = raw_item.get("skills", [])

    elif source_platform == "topcv":
        std_item["metadata"]["job_url"] = raw_item.get("url")
        
        # Xử lý title bị dính chữ "làm việc tại CÔNG TY..."
        raw_title = raw_item.get("job_title", "")
        if "làm việc tại" in raw_title:
            parts = raw_title.split("làm việc tại")
            std_item["job_info"]["title"] = parts[0].strip()
            std_item["company_info"]["name"] = parts[1].strip()
        else:
            std_item["job_info"]["title"] = raw_title
            
        std_item["job_info"]["working_model"] = raw_item.get("working_time")
        std_item["job_info"]["experience"] = ", ".join(raw_item.get("requirement_tags", []))
        
        std_item["location"]["full_address"] = raw_item.get("location")
        # Extract Tỉnh/Thành phố từ chuỗi location (cần parse regex thêm nếu muốn chuẩn)
        
        std_item["content"]["description"] = raw_item.get("job_description")
        std_item["content"]["requirements"] = raw_item.get("candidate_requirements")
        std_item["content"]["benefits"] = raw_item.get("detailed_benefits")
        
        std_item["tags"]["skills"] = raw_item.get("expertise_tags", [])

    elif source_platform == "vietnamworks":
        std_item["metadata"]["job_url"] = raw_item.get("url")
        std_item["job_info"]["title"] = raw_item.get("job_title")
        std_item["location"]["full_address"] = raw_item.get("location")
        
        std_item["content"]["description"] = raw_item.get("job_description")
        std_item["content"]["requirements"] = raw_item.get("candidate_requirements")
        std_item["content"]["benefits"] = raw_item.get("benefits")
        
        # VietnamWorks nhét cực nhiều thứ vào chuỗi job_info, tạm thời lưu thô vào tags
        std_item["tags"]["skills"] = [raw_item.get("job_info")] 

    return std_item

def determine_platform(filename: str):
    """
    Automatically identify the mapping rule based on the filename.
    Adjust the keywords ('itviec', 'topcv'...) to match your actual file names.
    """
    name = filename.lower()
    if "itviec" in name:
        return "File1_JSON"
    elif "topdev" in name:
        return "File2_JSONL"
    elif "topcv" in name:
        return "File3_JSON"
    elif "vietnamworks" in name:
        return "File4_JSONL"
    else:
        return None

def main():
    # 1. Configure base and data paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DETAILS_DIR = BASE_DIR / "data" / "data_details" 
    PROCESSED_DIR = BASE_DIR / "data" / "data_processed"
    
    # 2. Automatically create the processed directory if it doesn't exist
    # parents=True: Automatically create parent directories if missing
    # exist_ok=True: Do not throw an error if the directory already exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    unified_data = []

    # 3. Scan all files in the source directory
    if not DATA_DETAILS_DIR.exists():
        print(f"Source directory does not exist: {DATA_DETAILS_DIR}")
        return

    all_files = DATA_DETAILS_DIR.iterdir()

    for filepath in all_files:
        # Process files only (ignore sub-directories)
        if filepath.is_file() and filepath.suffix.lower() in ['.json', '.jsonl']:
            
            # Identify the mapping rule from the filename
            platform = determine_platform(filepath.name)
            if not platform:
                print(f"Skipping file with unknown source: {filepath.name}")
                continue
                
            print(f"Processing {filepath.name} (Rule: {platform})...")
            raw_items = load_data(filepath)
            
            for item in raw_items:
                std_item = standardize_item(item, platform)
                unified_data.append(std_item)

    # 4. Save the unified dataset to the processed directory
    output_file = PROCESSED_DIR / "unified_jobs_dataset.json"
    
    print(f"\nMerge complete! Saving {len(unified_data)} records to {output_file}...")
    
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(unified_data, f, ensure_ascii=False, indent=4)
        
    print("Process finished successfully!")

if __name__ == "__main__":
    main()