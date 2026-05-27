from pathlib import Path
import json

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

        

    print("===================================")

def json_handle(file):
    with open(file, "r", encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list) and len(data) > 0:
        print("---Structure JSON: LIST ---")
        print(f"Total items: {len(data)}")
        print("Keys in the first item:")
        print(list(data[0].keys()))

    print("===================================")


for file in all_files:
    if file.suffix == ".json":
        json_handle(file)
    elif file.suffix == ".jsonl":
        jsonl_handle(file)