# backend/app/db.py

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket, AsyncIOMotorDatabase
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path
from bson import ObjectId
import certifi  # <--- IMPORT certifi

# Load env vars
env_path = Path(__file__).parent.parent.parent / "config" / ".env"
load_dotenv(dotenv_path=env_path)

# --- Global Variables ---
client: Optional[AsyncIOMotorClient] = None
mongodb: Optional[AsyncIOMotorDatabase] = None
fs_bucket: Optional[AsyncIOMotorGridFSBucket] = None

async def connect_db():
    """
    Initialize MongoDB connection, database handle, and GridFS bucket.
    Uses certifi for reliable TLS certificate validation.
    """
    global client, mongodb, fs_bucket
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db_name = os.getenv('MONGODB_DB', 'futureself')

    if not mongo_uri:
        raise ValueError("MONGODB_URI environment variable not set or found in .env file")

    # ---> START CHANGE <---
    # Get the path to the CA bundle from certifi
    ca = certifi.where()
    print(f"DEBUG: Using CA certificate bundle from: {ca}")
    # ---> END CHANGE <---

    # Avoid logging credentials in production logs
    log_uri = mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri
    print(f"DEBUG: Connecting to MongoDB at {log_uri}...")

    try:
        # ---> MODIFIED LINE: Pass tlsCAFile=ca to the client constructor <---
        client = AsyncIOMotorClient(mongo_uri, tlsCAFile=ca)

        # Optional: Add server selection timeout for faster failure if needed,
        # but the default (30s) is usually fine. Example:
        # client = AsyncIOMotorClient(mongo_uri, tlsCAFile=ca, serverSelectionTimeoutMS=15000)

        # The ismaster command is cheap and does explicit server selection.
        # Good for verifying the connection works immediately.
        await client.admin.command('ismaster')
        print("DEBUG: Successfully connected to MongoDB and verified connection.")

        mongodb = client[mongo_db_name]
        fs_bucket = AsyncIOMotorGridFSBucket(mongodb)
        print(f"DEBUG: Initialized database handle '{mongo_db_name}' and GridFS bucket.")

    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        # Re-raise the exception so the application knows connection failed
        raise

async def close_db():
    """
    Close MongoDB connection.
    """
    global client
    if client:
        print("DEBUG: Closing MongoDB connection...")
        client.close()
        client = None # Ensure client is reset
        mongodb = None # Reset DB handle too
        fs_bucket = None # Reset GridFS bucket
        print("DEBUG: MongoDB connection closed.")


# --- Dependency Function ---
def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI Dependency function to get the database handle.
    """
    if mongodb is None:
        # This might happen if connect_db failed during startup
        print("ERROR: get_db called but database connection is not initialized.")
        raise RuntimeError("Database connection not initialized. Lifespan manager might have failed or connection error occurred.")
    return mongodb

# --- Collection Helper ---
def get_collection(name: str):
    """
    Retrieve a collection by name from the database.
    """
    db = get_db() # Use the dependency function
    return db[name]

# --- GridFS Helper ---
def get_fs_bucket() -> AsyncIOMotorGridFSBucket:
    """
    Gets the GridFS bucket instance. Ensures it's initialized.
    """
    global fs_bucket
    if fs_bucket is None:
        print("ERROR: get_fs_bucket called but GridFS bucket is not initialized.")
        raise RuntimeError("GridFS bucket not initialized. Check database connection.")
    return fs_bucket


# --- CRUD utility functions ---

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

async def upload_file(file_bytes: bytes, filename: str, metadata: dict = None) -> str:
    """
    Upload a file to GridFS. Returns the file ID as string.
    """
    fs = get_fs_bucket() # Use helper function
    metadata = metadata or {}
    # Note: upload_from_stream expects a stream-like object or bytes directly.
    # If file_bytes is already bytes, this is fine.
    file_id = await fs.upload_from_stream(filename, file_bytes, metadata=metadata)
    return str(file_id)

async def download_file(file_id) -> bytes:
    """
    Download a file from GridFS by its ID (can be ObjectId or string).
    Returns file bytes.
    """
    fs = get_fs_bucket() # Use helper function
    if isinstance(file_id, str):
        try:
            file_id = ObjectId(file_id)
        except Exception:
             raise ValueError(f"Invalid file_id format: {file_id}")

    grid_out = await fs.open_download_stream(file_id)
    data = await grid_out.read()
    return data

async def delete_file(file_id) -> None:
    """
    Delete a file from GridFS by its ID (can be ObjectId or string).
    """
    fs = get_fs_bucket() # Use helper function
    if isinstance(file_id, str):
        try:
            file_id = ObjectId(file_id)
        except Exception:
             raise ValueError(f"Invalid file_id format: {file_id}")
    await fs.delete(file_id)