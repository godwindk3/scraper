import json
import pandas as pd

def inspect_json(file_path):
    # Load JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Nếu JSON là 1 object duy nhất -> convert thành list
    if isinstance(data, dict):
        data = [data]

    # Flatten JSON
    df = pd.json_normalize(data)

    print("=" * 60)
    print("COLUMNS")
    print("=" * 60)

    for col in df.columns:
        print(col)

    print("\n" + "=" * 60)
    print("SAMPLE DATA")
    print("=" * 60)

    print(df.head(3).to_string())

    print("\n" + "=" * 60)
    print("DATA TYPES")
    print("=" * 60)

    print(df.dtypes)

if __name__ == "__main__":
    inspect_json("topdev_detail.json")