# future-self/backend/app/routers/memories.py

import os
import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from fastapi import Form, File, UploadFile
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

logger = logging.getLogger(__name__)
# Ensure logging is configured in main.py, e.g., logging.basicConfig(level=logging.DEBUG)

# --- REAL Dependency Imports (CRITICAL - Ensure this works) ---
User = None
get_db = None
get_current_active_user = None
_dependencies_loaded_successfully = False
MainEmailStr = EmailStr

try:
    from ..main import get_db as main_get_db, \
                       get_current_active_user as main_get_current_active_user, \
                       UserPublic as MainUserPublic, \
                       EmailStr as ImportedEmailStr
    User = MainUserPublic
    get_db = main_get_db
    get_current_active_user = main_get_current_active_user
    MainEmailStr = ImportedEmailStr
    _dependencies_loaded_successfully = True
    logger.info("memories.py: Successfully imported REAL dependencies from ..main.")
except ImportError as e:
    logger.critical(
        f"memories.py: CRITICAL ERROR - FAILED to import REAL dependencies from ..main: {e}. "
        "Using non-functional placeholders.",
        exc_info=True
    )
    class User(BaseModel): id: str = "placeholder_id"; username: str = "placeholder_user"; email: Optional[MainEmailStr] = None
    async def get_db_placeholder() -> AsyncIOMotorDatabase:
        logger.error("memories.py: FATAL - Using FAULTY PLACEHOLDER get_db().")
        raise NotImplementedError("Placeholder get_db() called.")
    get_db = get_db_placeholder
    async def get_current_active_user_placeholder() -> User:
        logger.error("memories.py: FATAL - Using FAULTY PLACEHOLDER get_current_active_user().")
        raise NotImplementedError("Placeholder get_current_active_user() called.")
    get_current_active_user = get_current_active_user_placeholder

# --- Configuration for MongoDB Collection ---
MEMORIES_COLLECTION_NAME = "futureself" # Your specified collection name

# --- Pydantic Models ---
class MemoryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    significance: int = Field(default=3, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    class Config: from_attributes = True

class MemoryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    significance: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = Field(None)

class Memory(MemoryBase):
    id: str = Field(..., alias="_id")
    user_id: str = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    attachments: List[str] = Field(default_factory=list)
    class Config: from_attributes = True; populate_by_name = True

# --- FastAPI Router ---
router_dependencies_list = []
if _dependencies_loaded_successfully and callable(get_current_active_user):
    router_dependencies_list = [Depends(get_current_active_user)]
else:
    logger.error("memories.py: Router dependencies cannot be set, get_current_active_user FAILED to load.")

router = APIRouter(
    tags=["Memories"],
    responses={404: {"description": "Memory resource not found"}},
    dependencies=router_dependencies_list
)

# --- File Saving Helper ---
UPLOAD_DIR = "uploads"; os.makedirs(UPLOAD_DIR, exist_ok=True)
async def save_upload_file(upload_file: UploadFile, user_id: str) -> str:
    original_filename, original_ext = os.path.splitext(upload_file.filename)
    safe_filename_base = "".join(c if c.isalnum() else "_" for c in original_filename[:50])
    unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{safe_filename_base}{original_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    try:
        with open(file_path, "wb") as buffer: content = await upload_file.read(); buffer.write(content)
        logger.info(f"Successfully saved file: {file_path} for user {user_id}")
        return f"/static/uploads/{unique_filename}" # Ensure your static files are served from this path
    except Exception as e:
        logger.error(f"Error saving file {upload_file.filename} for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not save file: {upload_file.filename}")

# --- API Endpoints ---
@router.post("/memories", response_model=Memory, status_code=status.HTTP_201_CREATED, summary="Create new memory")
async def create_new_memory(
    title: str = Form(...), description: str = Form(...), significance: int = Form(default=3, ge=1, le=5),
    tags_json: str = Form("[]"), files: Optional[List[UploadFile]] = File(None),
    db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    logger.info(f"CREATE_MEMORY User '{current_user.id}' attempting to create memory. Title: '{title}'. DB type: {type(db)}")
    if not _dependencies_loaded_successfully:
        logger.error("CREATE_MEMORY: ABORTING due to failed real dependency import.")
        raise HTTPException(status_code=500, detail="Server configuration error preventing memory creation.")
    try:
        tags_list: List[str] = json.loads(tags_json)
        if not isinstance(tags_list, list) or not all(isinstance(tag, str) for tag in tags_list):
            raise ValueError("Tags must be a list of strings.")
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"CREATE_MEMORY: Invalid tags_json format from user '{current_user.id}': {tags_json}. Error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid 'tags' format: {e}")

    attachment_paths: List[str] = []
    if files:
        for file_upload in files:
            if file_upload and file_upload.filename:
                try: saved_path = await save_upload_file(file_upload, current_user.id); attachment_paths.append(saved_path)
                except HTTPException as eHttp: raise eHttp
                except Exception as eFile: logger.error(f"CREATE_MEMORY: File save failed for user '{current_user.id}', file '{file_upload.filename}': {eFile}", exc_info=True); raise HTTPException(status_code=500, detail=f"Error processing file: {file_upload.filename}")

    now = datetime.utcnow(); memory_id_str = str(uuid.uuid4())
    memory_doc = {
        "_id": memory_id_str, "user_id": current_user.id, "title": title, "description": description,
        "significance": significance, "tags": tags_list, "attachments": attachment_paths,
        "created_at": now, "updated_at": now,
    }
    logger.debug(f"CREATE_MEMORY: Document to insert into MongoDB: {memory_doc}")
    try:
        memories_collection: AsyncIOMotorCollection = db[MEMORIES_COLLECTION_NAME]
        insert_result = await memories_collection.insert_one(memory_doc)
        if not insert_result.inserted_id:
            logger.error(f"CREATE_MEMORY: MongoDB insert_one FAILED for user '{current_user.id}'. No inserted_id.")
            raise HTTPException(status_code=500, detail="Failed to save memory to DB.")
        logger.info(f"CREATE_MEMORY: MongoDB insert_one successful. Inserted ID: {insert_result.inserted_id}")

        created_memory_doc_from_db = await memories_collection.find_one({"_id": memory_doc["_id"]})
        if not created_memory_doc_from_db:
            logger.error(f"CREATE_MEMORY: MongoDB find_one FAILED after insert for memory_id '{memory_doc['_id']}', user '{current_user.id}'.")
            raise HTTPException(status_code=500, detail="Failed to retrieve memory after creation.")

        logger.info(f"CREATE_MEMORY: Memory '{created_memory_doc_from_db['_id']}' created for user '{current_user.id}'.")
        return Memory(**created_memory_doc_from_db)
    except Exception as eDB:
        logger.error(f"CREATE_MEMORY: DB EXCEPTION creating memory for user '{current_user.id}': {eDB}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save memory due to DB error.")

@router.get("/memories", response_model=List[Memory], summary="List user memories")
async def list_memories(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    logger.info(f"LIST_MEMORIES User '{current_user.id}' listing memories. Skip: {skip}, Limit: {limit}. DB type: {type(db)}")
    if not _dependencies_loaded_successfully:
        logger.error("LIST_MEMORIES: ABORTING due to failed real dependency import.")
        return [] # Return empty list, FastAPI will handle serialization
    try:
        memories_collection: AsyncIOMotorCollection = db[MEMORIES_COLLECTION_NAME]
        cursor = memories_collection.find({"user_id": current_user.id}).sort("created_at", -1).skip(skip).limit(limit)
        db_memories_raw = await cursor.to_list(length=limit)
        logger.debug(f"LIST_MEMORIES: Raw documents from DB for user '{current_user.id}': {json.dumps(db_memories_raw, default=str)}")

        # Create Pydantic instances. 'id' field should be populated from '_id' here.
        pydantic_memory_instances = [Memory(**mem_doc) for mem_doc in db_memories_raw]

        if pydantic_memory_instances:
            # Optional: Log the structure of the first Pydantic instance before FastAPI serializes it.
            # This helps confirm that 'id' is present on the model instance itself.
            try:
                # For Pydantic V2:
                first_instance_dict_check = pydantic_memory_instances[0].model_dump(by_alias=False)
            except AttributeError:
                # For Pydantic V1:
                first_instance_dict_check = pydantic_memory_instances[0].dict(by_alias=False) # Use by_alias=False to check field names

            logger.info(f"LIST_MEMORIES: First Pydantic instance (internal check, will be serialized by FastAPI): {json.dumps(first_instance_dict_check, default=str, indent=2)}")
            if "id" not in first_instance_dict_check:
                 logger.error(f"LIST_MEMORIES: CRITICAL - First Pydantic instance check (by_alias=False) is MISSING 'id' field! Object: {first_instance_dict_check}")
            elif first_instance_dict_check.get("id") is None:
                 logger.error(f"LIST_MEMORIES: CRITICAL - First Pydantic instance check (by_alias=False) has 'id' field as None! Object: {first_instance_dict_check}")
        else:
            logger.info(f"LIST_MEMORIES: No memories found for user '{current_user.id}'. Returning empty list of Pydantic instances.")

        # Return the list of Pydantic model instances.
        # FastAPI will serialize them according to the Memory model's field names (e.g., 'id'),
        # because `response_model=List[Memory]` is set and `response_model_by_alias=True` is not.
        return pydantic_memory_instances
    except Exception as e:
        logger.error(f"LIST_MEMORIES: DB error listing memories for user '{current_user.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve memories.")

@router.get("/memories/{memory_id}", response_model=Memory, summary="Get a specific memory")
async def get_memory(
    memory_id: str = Path(...), db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"GET_MEMORY User '{current_user.id}' getting memory_id '{memory_id}'. DB type: {type(db)}")
    if not _dependencies_loaded_successfully:
        logger.error(f"GET_MEMORY: ABORTING for memory '{memory_id}' due to failed real dependency import.")
        raise HTTPException(status_code=500, detail="Server configuration error.")
    try:
        memories_collection: AsyncIOMotorCollection = db[MEMORIES_COLLECTION_NAME]
        memory_doc = await memories_collection.find_one({"_id": memory_id, "user_id": current_user.id})
        if not memory_doc:
            logger.warning(f"GET_MEMORY: Memory_id '{memory_id}' not found for user '{current_user.id}'.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found or access denied")
        logger.info(f"GET_MEMORY: Memory '{memory_id}' (raw _id: {memory_doc.get('_id')}) retrieved for user '{current_user.id}'.")
        return Memory(**memory_doc) # Pydantic handles _id -> id for response
    except HTTPException: raise
    except Exception as e:
        logger.error(f"GET_MEMORY: DB error getting memory '{memory_id}' for user '{current_user.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not retrieve memory '{memory_id}'.")

@router.patch("/memories/{memory_id}", response_model=Memory, summary="Update a memory")
async def update_memory_endpoint(
    memory_id: str = Path(...), memory_update: MemoryUpdate = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    logger.info(f"UPDATE_MEMORY User '{current_user.id}' updating memory_id '{memory_id}'. DB type: {type(db)}")
    if not _dependencies_loaded_successfully:
        logger.error(f"UPDATE_MEMORY: ABORTING for memory '{memory_id}' due to failed real dependency import.")
        raise HTTPException(status_code=500, detail="Server configuration error.")
    update_data = memory_update.model_dump(exclude_unset=True, by_alias=False) if hasattr(memory_update,"model_dump") else memory_update.dict(exclude_unset=True, by_alias=False)
    if not update_data: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    update_data["updated_at"] = datetime.utcnow()
    logger.debug(f"UPDATE_MEMORY: Update data for '{memory_id}': {update_data}")
    try:
        memories_collection: AsyncIOMotorCollection = db[MEMORIES_COLLECTION_NAME]
        result = await memories_collection.update_one(
            {"_id": memory_id, "user_id": current_user.id}, {"$set": update_data}
        )
        logger.info(f"UPDATE_MEMORY: MongoDB update_one result for '{memory_id}': matched_count={result.matched_count}, modified_count={result.modified_count}")
        if result.matched_count == 0:
            logger.warning(f"UPDATE_MEMORY: Update failed: Memory_id '{memory_id}' not found/denied for user '{current_user.id}'.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found or access denied for update")

        updated_doc = await memories_collection.find_one({"_id": memory_id, "user_id": current_user.id})
        if not updated_doc:
            logger.error(f"UPDATE_MEMORY: Failed to retrieve memory '{memory_id}' after update for user '{current_user.id}'. THIS SHOULD NOT HAPPEN if matched_count was 1.")
            raise HTTPException(status_code=404, detail="Memory not found after update attempt.")
        logger.info(f"UPDATE_MEMORY: Memory '{memory_id}' updated for user '{current_user.id}'.")
        return Memory(**updated_doc) # Pydantic handles _id -> id for response
    except HTTPException: raise
    except Exception as e:
        logger.error(f"UPDATE_MEMORY: DB error updating memory '{memory_id}' for user '{current_user.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not update memory '{memory_id}'.")

@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a memory")
async def delete_memory_endpoint(
    memory_id: str = Path(...), db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger.info(f"DELETE_MEMORY User '{current_user.id}' deleting memory_id '{memory_id}'. DB type: {type(db)}")
    if not _dependencies_loaded_successfully:
        logger.error(f"DELETE_MEMORY: ABORTING for memory '{memory_id}' due to failed real dependency import.")
        raise HTTPException(status_code=500, detail="Server configuration error.")
    try:
        memories_collection: AsyncIOMotorCollection = db[MEMORIES_COLLECTION_NAME]
        logger.debug(f"DELETE_MEMORY: Attempting to delete from collection '{MEMORIES_COLLECTION_NAME}' with query: {{'_id': '{memory_id}', 'user_id': '{current_user.id}'}}")
        result = await memories_collection.delete_one({"_id": memory_id, "user_id": current_user.id})
        logger.info(f"DELETE_MEMORY: MongoDB delete_one result for '{memory_id}': deleted_count={result.deleted_count}")
        if result.deleted_count == 0:
            logger.warning(f"DELETE_MEMORY: Delete failed: Memory_id '{memory_id}' not found/denied for user '{current_user.id}'.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found or access denied")
        logger.info(f"DELETE_MEMORY: Memory '{memory_id}' deleted for user '{current_user.id}'.")
        # No content to return, FastAPI handles the 204 status.
    except HTTPException: raise
    except Exception as e:
        logger.error(f"DELETE_MEMORY: DB error deleting memory '{memory_id}' for user '{current_user.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not delete memory '{memory_id}'.")

@router.post("/memories/{memory_id}/upload-attachment", response_model=Memory, summary="Upload attachment")
async def upload_attachment_to_memory(
    memory_id: str = Path(...), file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    logger.info(f"UPLOAD_ATTACHMENT User '{current_user.id}' uploading attachment for memory_id '{memory_id}'. DB type: {type(db)}")
    if not _dependencies_loaded_successfully:
        logger.error(f"UPLOAD_ATTACHMENT: ABORTING for memory '{memory_id}' due to failed real dependency import.")
        raise HTTPException(status_code=500, detail="Server configuration error.")
    try:
        memories_collection: AsyncIOMotorCollection = db[MEMORIES_COLLECTION_NAME]
        memory_doc = await memories_collection.find_one({"_id": memory_id, "user_id": current_user.id})
        if not memory_doc:
            logger.warning(f"UPLOAD_ATTACHMENT: Memory_id '{memory_id}' not found/denied for user '{current_user.id}'.")
            raise HTTPException(status_code=404, detail="Memory not found or access denied")

        saved_path = await save_upload_file(file, current_user.id)

        result = await memories_collection.update_one(
            {"_id": memory_id, "user_id": current_user.id},
            {"$push": {"attachments": saved_path}, "$set": {"updated_at": datetime.utcnow()}}
        )
        logger.info(f"UPLOAD_ATTACHMENT: MongoDB update_one result for '{memory_id}' after $push: matched_count={result.matched_count}, modified_count={result.modified_count}")
        if result.modified_count == 0 and result.matched_count > 0 :
             logger.warning(f"UPLOAD_ATTACHMENT: Attachment upload for memory '{memory_id}' (user '{current_user.id}') resulted in modified_count=0. Path might have already existed or other issue.")
        elif result.matched_count == 0:
            logger.error(f"UPLOAD_ATTACHMENT: Memory '{memory_id}' not found for update for user '{current_user.id}'.") # Should have been caught by find_one
            raise HTTPException(status_code=404, detail="Memory not found during attachment update.")

        updated_doc = await memories_collection.find_one({"_id": memory_id, "user_id": current_user.id})
        if not updated_doc or saved_path not in updated_doc.get("attachments", []):
            logger.error(f"UPLOAD_ATTACHMENT: Failed to confirm attachment '{saved_path}' in memory '{memory_id}' after update for user '{current_user.id}'. Doc: {updated_doc}")
            raise HTTPException(status_code=500, detail="Failed to update memory with attachment path.")
        logger.info(f"UPLOAD_ATTACHMENT: Attachment added to memory '{memory_id}' for user '{current_user.id}'.")
        return Memory(**updated_doc) # Pydantic handles _id -> id for response
    except HTTPException: raise
    except Exception as e:
        logger.error(f"UPLOAD_ATTACHMENT: Error uploading attachment for memory '{memory_id}', user '{current_user.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process attachment.")