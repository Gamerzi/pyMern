# backend/app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
# Import datetime and timedelta here
from datetime import datetime, timedelta
from typing import Annotated, Any
from bson import ObjectId

# --- App Modules (Using 'app.' absolute imports) ---
# Use absolute imports starting from the 'app' package
# This imports UserPreferences along with other user models
from app.models.user import User, UserCreate, UserInDB, UserPreferences
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash
)
from app.core.config import settings
from app.db import get_db, find_document, insert_document
# --- REMOVED: from ..crud import user as user_crud --- # Keep this removed

# --- Pydantic Models ---
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Router Setup ---
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

# --- Authentication Endpoints ---

@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def signup_new_user(
    user_in: UserCreate,
    db: Annotated[Any, Depends(get_db)]
):
    """Sign up a new user (Simplified: Uses db functions directly)."""
    existing_user_dict = await find_document("users", {"email": user_in.email})
    if existing_user_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    hashed_password = get_password_hash(user_in.password)
    user_data_for_db = user_in.model_dump(exclude={"password"})

    user_to_insert = {
        **user_data_for_db,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(), # Use imported datetime
        "updated_at": datetime.utcnow(), # Use imported datetime
        "preferences": UserPreferences().model_dump(), # Use imported UserPreferences
        "persona": None,
        "life_snapshot": None
    }

    try:
        inserted_id_str = await insert_document("users", user_to_insert)
        new_user_dict = await find_document("users", {"_id": ObjectId(inserted_id_str)})
        if not new_user_dict:
             raise HTTPException(status_code=500, detail="Failed to retrieve created user.")
        created_user = UserInDB(**new_user_dict)
    except Exception as e:
        print(f"Error during user creation/retrieval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user account.",
        )
    return created_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Any, Depends(get_db)]
):
    """Login user (Simplified: Uses db functions directly)."""
    user_dict = await find_document("users", {"email": form_data.username})

    if user_dict:
        try:
            user = UserInDB(**user_dict)
        except Exception as model_error:
             print(f"ERROR converting DB dict to UserInDB: {model_error} - Data: {user_dict}")
             raise HTTPException(status_code=500, detail="Internal server error processing user data.")
    else:
        user = None

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    user_id_for_token = str(user.id)
    access_token = create_access_token(
        subject=user.email,
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")

# --- Removed redundant imports from the bottom ---
# from datetime import datetime # Removed - already imported at top
# No need to re-import UserPreferences if imported above with 'app.' prefix