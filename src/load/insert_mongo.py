import json
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

def load_data_to_mongo():
    # Setup paths assuming this script is in the 'load' folder
    # This resolves to the project_root directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    PROCESSED_FILE = BASE_DIR / "data" / "data_processed" / "unified_jobs_dataset.json"

    # Check if the processed file exists before proceeding
    if not PROCESSED_FILE.exists():
        print(f"Cannot find the data file at: {PROCESSED_FILE}")
        return

    # Replace this string with your actual MongoDB Atlas connection string
    # Remember to replace <username> and <password>
    MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.xxxx.mongodb.net/?appName=it-job"
    
    try:
        # Initialize MongoDB client
        client = MongoClient(MONGO_URI)
        
        # Select the database and collection
        # MongoDB will create them automatically if they don't exist
        db = client["job_market_db"]
        collection = db["jobs_nested_schema"]

        # Read the unified JSON data
        print(f"Reading data from {PROCESSED_FILE.name}...")
        with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)

        if not jobs_data:
            print("The dataset is empty. Nothing to insert.")
            return

        # Insert data into MongoDB using insert_many for batch processing
        # This is significantly faster than looping and inserting one by one
        print(f"Inserting {len(jobs_data)} records into MongoDB...")
        result = collection.insert_many(jobs_data)
        
        print(f"Successfully inserted {len(result.inserted_ids)} records!")

    except BulkWriteError as bwe:
        # Catch specific errors related to bulk operations
        print(f"Batch insert error: {bwe.details}")
    except Exception as e:
        # Catch general connection or execution errors
        print(f"An error occurred: {e}")
    finally:
        # Ensure the connection is always closed gracefully
        if 'client' in locals():
            client.close()
            print("MongoDB connection closed.")

if __name__ == "__main__":
    load_data_to_mongo()