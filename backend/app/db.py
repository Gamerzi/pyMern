# backend/app/db.py

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket, AsyncIOMotorDatabase # Import Database type hint
from dotenv import load_dotenv
from typing import Optional # Import Optional
from pathlib import Path # <--- ADD THIS LINE TO IMPORT Path
from bson import ObjectId # Needed for GridFS ID conversion

# Load env vars
# Corrected path assuming db.py is in backend/app/ and config/.env is in project_root/config/
env_path = Path(__file__).parent.parent.parent / "config" / ".env" # More robust path construction
load_dotenv(dotenv_path=env_path)

# --- Global Variables ---
# Add type hints for clarity
client: Optional[AsyncIOMotorClient] = None
mongodb: Optional[AsyncIOMotorDatabase] = None # Use the specific type hint
fs_bucket: Optional[AsyncIOMotorGridFSBucket] = None

async def connect_db():
    """
    Initialize MongoDB connection, database handle, and GridFS bucket.
    """
    global client, mongodb, fs_bucket
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db_name = os.getenv('MONGODB_DB', 'futureself') # Default value if not set

    # Add check for missing URI
    if not mongo_uri:
        raise ValueError("MONGODB_URI environment variable not set or found in .env file")

    print(f"DEBUG: Connecting to MongoDB at {mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri}...") # Avoid logging credentials
    client = AsyncIOMotorClient(mongo_uri)
    mongodb = client[mongo_db_name] # Assign to global mongodb variable
    fs_bucket = AsyncIOMotorGridFSBucket(mongodb)
    print(f"DEBUG: Connected to database '{mongo_db_name}'.")


async def close_db():
    """
    Close MongoDB connection.
    """
    global client
    if client:
        print("DEBUG: Closing MongoDB connection...")
        client.close()
        print("DEBUG: MongoDB connection closed.")


# --- ADD THIS DEPENDENCY FUNCTION ---
def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI Dependency function to get the database handle.

    Returns the global 'mongodb' object initialized by connect_db during app startup.

    Raises:
        RuntimeError: If the database connection hasn't been established yet.
    """
    # This check ensures connect_db (called by lifespan) has run
    if mongodb is None:
        raise RuntimeError("Database connection not initialized. Lifespan manager might have failed.")
    return mongodb
# --- END OF ADDED FUNCTION ---


def get_collection(name: str):
    """
    Retrieve a collection by name from the database.
    Requires the database to be connected.
    """
    db = get_db() # Use the dependency function to ensure connection
    return db[name]


# --- CRUD utility functions ---
# These should now use get_collection to ensure DB is ready

async def insert_document(collection_name: str, document: dict) -> str:
    """
    Insert a document into the specified collection.
    Returns the inserted document ID as a string.
    """
    coll = get_collection(collection_name)
    result = await coll.insert_one(document)
    return str(result.inserted_id)

async def find_document(collection_name: str, filter: dict) -> Optional[dict]:
    """
    Find a single document matching the filter. Returns None if not found.
    """
    coll = get_collection(collection_name)
    return await coll.find_one(filter)

async def update_document(collection_name: str, filter: dict, update: dict) -> int:
    """
    Update documents matching the filter. Uses $set implicitly for the update dict.
    Returns the count of modified documents.
    """
    coll = get_collection(collection_name)
    # Ensure the update uses operators like $set, $inc, etc.
    # If 'update' only contains fields, wrap it in $set for safety/clarity
    if not any(key.startswith('$') for key in update):
       update_operation = {'$set': update}
    else:
       update_operation = update

    result = await coll.update_many(filter, update_operation)
    return result.modified_count

async def delete_document(collection_name: str, filter: dict) -> int:
    """
    Delete documents matching the filter.
    Returns the count of deleted documents.
    """
    coll = get_collection(collection_name)
    result = await coll.delete_many(filter)
    return result.deleted_count


# --- File upload/download using GridFS ---
# These also need the fs_bucket to be initialized

async def upload_file(file_bytes: bytes, filename: str, metadata: dict = None) -> str:
    """
    Upload a file to GridFS. Returns the file ID as string.
    """
    global fs_bucket
    if fs_bucket is None:
         raise RuntimeError("GridFS bucket not initialized.")
    metadata = metadata or {}
    file_id = await fs_bucket.upload_from_stream(filename, file_bytes, metadata=metadata)
    return str(file_id)

async def download_file(file_id) -> bytes:
    """
    Download a file from GridFS by its ID (can be ObjectId or string).
    Returns file bytes.
    """
    global fs_bucket
    if fs_bucket is None:
         raise RuntimeError("GridFS bucket not initialized.")
    # Convert string ID to ObjectId if necessary
    if isinstance(file_id, str):
        try:
            file_id = ObjectId(file_id)
        except Exception:
             raise ValueError(f"Invalid file_id format: {file_id}")

    grid_out = await fs_bucket.open_download_stream(file_id)
    data = await grid_out.read()
    return data

async def delete_file(file_id) -> None:
    """
    Delete a file from GridFS by its ID (can be ObjectId or string).
    """
    global fs_bucket
    if fs_bucket is None:
         raise RuntimeError("GridFS bucket not initialized.")
    # Convert string ID to ObjectId if necessary
    if isinstance(file_id, str):
        try:
            file_id = ObjectId(file_id)
        except Exception:
             raise ValueError(f"Invalid file_id format: {file_id}")
    await fs_bucket.delete(file_id)