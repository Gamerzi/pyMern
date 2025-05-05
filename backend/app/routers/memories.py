# future-self/backend/app/routers/memories.py

import uuid
import asyncio # Only for simulating async DB calls in placeholders
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from pydantic import BaseModel, Field, validator

# --- Placeholder Dependencies (Same ones used in conversation.py) ---
# You'll replace these with your actual DB connection and authentication logic

# Assuming User model is defined (e.g., in conversation.py or a models file)
class User(BaseModel):
    id: str
    username: str

async def get_db():
    print("DEBUG: Yielding dummy DB connection (Memories)")
    # This should yield your actual async DB client/session in a real app
    # For now, using a shared dummy store if main.py overrides it,
    # otherwise, it creates its own here. A real app should share the connection.
    yield {"memories": {}, "users": {"user_123": {"id":"user_123", "username":"testuser"}}}

async def get_current_active_user(db = Depends(get_db)) -> User:
    print("DEBUG: Returning dummy authenticated user (Memories)")
    # Replace with actual token verification and user lookup
    # Ensure the user exists in db['users'] if using this dummy setup
    return User(id="user_123", username="testuser")

# --- Pydantic Models for Memories ---

class MemoryBase(BaseModel):
    """Base fields for a memory, used for creation and updates."""
    title: str = Field(..., min_length=3, max_length=100, description="A short title for the memory.")
    description: str = Field(..., description="The detailed content of the memory.")
    event_date: Optional[datetime] = Field(None, description="Approximate date/time the event occurred.")
    significance: int = Field(default=3, ge=1, le=5, description="User-rated significance (1=low, 5=high).")
    tags: Optional[List[str]] = Field(default_factory=list, description="Keywords or themes associated with the memory.")

    class Config:
        from_attributes = True # Renamed from orm_mode in Pydantic v2

class MemoryCreate(MemoryBase):
    """Model for creating a new memory."""
    pass # Inherits all fields from MemoryBase

class MemoryUpdate(BaseModel):
    """Model for partially updating an existing memory. All fields optional."""
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None)
    event_date: Optional[datetime] = Field(None)
    significance: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = Field(None)

class Memory(MemoryBase):
    """Full memory model including server-set fields, used for responses."""
    id: str = Field(..., description="Unique identifier for the memory.")
    user_id: str = Field(..., description="ID of the user who owns the memory.")
    created_at: datetime = Field(..., description="Timestamp when the memory was created.")
    updated_at: datetime = Field(..., description="Timestamp when the memory was last updated.")


# --- FastAPI Router ---
router = APIRouter(
    prefix="/memories",
    tags=["Memories"],
    responses={404: {"description": "Memory not found"}},
    # Apply authentication dependency to all routes in this router
    dependencies=[Depends(get_current_active_user)]
)

# --- Database Simulation Helpers (Replace with actual async DB logic) ---

async def db_create_memory(db: Dict, memory_data: Memory) -> Memory:
    """Simulates inserting a new memory into the DB."""
    if "memories" not in db: db["memories"] = {}
    if memory_data.id in db["memories"]: # Should not happen with UUIDs
        raise HTTPException(status_code=500, detail="Memory ID collision")
    db["memories"][memory_data.id] = memory_data.dict()
    print(f"DEBUG: DB creating memory {memory_data.id}")
    return memory_data

async def db_get_memory(db: Dict, memory_id: str, user_id: str) -> Optional[Memory]:
    """Simulates retrieving a memory, ensuring user ownership."""
    print(f"DEBUG: DB fetching memory {memory_id} for user {user_id}")
    memory_data = db.get("memories", {}).get(memory_id)
    if memory_data and memory_data["user_id"] == user_id:
        return Memory(**memory_data)
    return None

async def db_get_user_memories(db: Dict, user_id: str, skip: int = 0, limit: int = 100) -> List[Memory]:
    """Simulates fetching a list of memories for a user."""
    print(f"DEBUG: DB fetching memories for user {user_id} (skip={skip}, limit={limit})")
    user_mems = [
        Memory(**data) for data in db.get("memories", {}).values()
        if data["user_id"] == user_id
    ]
    # Sort by creation date descending (newest first) - adjust as needed
    user_mems.sort(key=lambda m: m.created_at, reverse=True)
    return user_mems[skip : skip + limit]

async def db_update_memory(db: Dict, memory_id: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Memory]:
    """Simulates updating an existing memory, ensuring user ownership."""
    print(f"DEBUG: DB attempting update for memory {memory_id} by user {user_id}")
    existing_memory_data = db.get("memories", {}).get(memory_id)

    if not existing_memory_data or existing_memory_data["user_id"] != user_id:
        return None # Not found or not owned by user

    # Merge updates
    existing_memory_data.update(update_data)
    existing_memory_data["updated_at"] = datetime.utcnow() # Update timestamp

    # Ensure significance is within bounds if updated
    if 'significance' in update_data:
         sig = update_data['significance']
         if not (isinstance(sig, int) and 1 <= sig <= 5):
              raise ValueError("Significance must be an integer between 1 and 5") # Or handle differently


    db["memories"][memory_id] = existing_memory_data # Save back to dummy store
    print(f"DEBUG: DB updated memory {memory_id}")
    return Memory(**existing_memory_data)


async def db_delete_memory(db: Dict, memory_id: str, user_id: str) -> bool:
    """Simulates deleting a memory, ensuring user ownership. Returns True if deleted."""
    print(f"DEBUG: DB attempting delete for memory {memory_id} by user {user_id}")
    if "memories" not in db or memory_id not in db["memories"]:
        return False # Not found

    if db["memories"][memory_id]["user_id"] == user_id:
        del db["memories"][memory_id]
        print(f"DEBUG: DB deleted memory {memory_id}")
        return True
    else:
        # Found, but doesn't belong to user - treat as not found for deletion purposes
        return False


# --- API Endpoints ---

@router.post(
    "/",
    response_model=Memory,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new memory",
    description="Adds a new memory entry to the user's repository.",
)
async def create_memory(
    memory_in: MemoryCreate = Body(...),
    db: Dict = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates a new memory associated with the logged-in user.
    """
    now = datetime.utcnow()
    new_memory = Memory(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        created_at=now,
        updated_at=now,
        **memory_in.dict() # Unpack fields from the input model
    )
    try:
        created_memory = await db_create_memory(db, new_memory)
    except Exception as e:
        # Log the error securely
        print(f"Error saving memory to DB: {e}")
        raise HTTPException(status_code=500, detail="Could not save the memory.")
    return created_memory


@router.get(
    "/",
    response_model=List[Memory],
    summary="List user's memories",
    description="Retrieves a list of memories belonging to the current user, with pagination.",
)
async def list_memories(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination."),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return."),
    db: Dict = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves all memories for the currently authenticated user.
    Supports pagination using `skip` and `limit`.
    """
    memories = await db_get_user_memories(db, current_user.id, skip=skip, limit=limit)
    return memories


@router.get(
    "/{memory_id}",
    response_model=Memory,
    summary="Get a specific memory",
    description="Retrieves the details of a single memory by its ID.",
)
async def get_memory(
    memory_id: str = Path(..., description="The unique ID of the memory to retrieve."),
    db: Dict = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves a specific memory by its ID.
    Ensures the memory belongs to the currently authenticated user.
    """
    memory = await db_get_memory(db, memory_id, current_user.id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found or you don't have permission to access it."
        )
    return memory


@router.patch( # Using PATCH for partial updates
    "/{memory_id}",
    response_model=Memory,
    summary="Update a memory",
    description="Partially updates the details of an existing memory.",
)
async def update_memory(
    memory_id: str = Path(..., description="The unique ID of the memory to update."),
    memory_update: MemoryUpdate = Body(...),
    db: Dict = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates specific fields of a memory belonging to the current user.
    Only fields provided in the request body will be updated.
    """
    # Get update data, excluding fields that were not set in the request
    update_data = memory_update.dict(exclude_unset=True)

    if not update_data:
         raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="No fields provided for update."
         )

    try:
        updated_memory = await db_update_memory(db, memory_id, current_user.id, update_data)
    except ValueError as ve: # Catch validation errors from DB helper
         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
         print(f"Error updating memory in DB: {e}")
         raise HTTPException(status_code=500, detail="Could not update the memory.")


    if not updated_memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found or you don't have permission to update it."
        )
    return updated_memory


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
    description="Permanently deletes a memory entry.",
)
async def delete_memory(
    memory_id: str = Path(..., description="The unique ID of the memory to delete."),
    db: Dict = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes a specific memory by its ID.
    Ensures the memory belongs to the currently authenticated user.
    Returns 204 No Content on successful deletion.
    """
    deleted = await db_delete_memory(db, memory_id, current_user.id)
    if not deleted:
        # Raise 404 whether it didn't exist or belonged to someone else
        # to avoid leaking information about existence.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found or you don't have permission to delete it."
        )
    # No response body needed for 204 status code
    return None # Or: return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Include in main.py ---
# Remember to import and include this router in your main FastAPI app:
#
# from app.routers import conversation, memories # etc.
#
# app.include_router(memories.router)
#