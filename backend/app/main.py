# future-self/backend/app/main.py

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List # Added List for scope use

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter # Add APIRouter here
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware # Added for frontend interaction

from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

print("--- Starting main.py ---")

# --- 1. Configuration Loading ---
print("Loading configuration...")
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Environment Variable Check & Settings ---
# (Ideally in a core/config.py Pydantic Settings model)
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "future_self_db" # Or load from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Used by conversation.py's PersonaService

# JWT Settings (Ideally from core/config.py)
SECRET_KEY = os.getenv("SECRET_KEY") # NEED TO SET THIS IN .env (e.g., openssl rand -hex 32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Or load from .env

# --- Check Essential Config ---
if not MONGODB_URI:
    raise ValueError("FATAL ERROR: MONGODB_URL environment variable not set.")
if not GROQ_API_KEY:
    # Note: conversation.py checks this too, but good to know early
    print("WARNING: GROQ_API_KEY environment variable not set. Conversation AI will fail.")
if not SECRET_KEY:
    raise ValueError("FATAL ERROR: SECRET_KEY environment variable not set. Needed for JWT.")

print("Configuration loaded.")


# --- 2. Pydantic Models ---
# (Ideally in separate files like models/user.py, models/token.py)
print("Defining Pydantic models...")

class UserBase(BaseModel):
    email: EmailStr = Field(..., unique=True)
    username: str = Field(..., min_length=3, index=True)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserInDBBase(UserBase):
    id: str = Field(..., alias="_id") # Use alias for MongoDB's default _id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Add other fields as needed: is_active, etc.

    class Config:
        from_attributes = True # Pydantic v2
        populate_by_name = True # Allow alias usage
        arbitrary_types_allowed = True # Needed for ObjectId if used directly

class UserInDB(UserInDBBase):
    hashed_password: str

class UserPublic(UserInDBBase): # Model for returning user info publicly (no password)
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    # Add scopes if using permission scopes
    # scopes: List[str] = []

print("Models defined.")

# --- 3. Security Utilities ---
# (Ideally in a separate core/security.py)
print("Setting up security utilities...")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token") # Points to our login route

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[str]:
    """Decodes JWT, returns username (or subject) if valid, else None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub") # 'sub' is standard JWT subject claim
        if username is None:
            return None # Or raise credential_exception
        # Optional: Check for token expiration more explicitly if needed, though decode handles it
        return username
    except JWTError:
        return None # Or raise credential_exception

print("Security utilities set up.")


# --- 4. Database Setup ---
print("Setting up database connection...")
# Use app.state for sharing client/db across requests and lifespan events
app_state: Dict[str, Any] = {}

async def startup_db_client():
    """Connects to MongoDB on application startup."""
    print(f"Connecting to MongoDB at {MONGODB_URI}...")
    app_state["mongodb_client"] = AsyncIOMotorClient(MONGODB_URI)
    app_state["mongodb"] = app_state["mongodb_client"][DB_NAME] # Select DB
    # Optional: Create indexes (ensure indexes on user email/username for lookups)
    try:
        await app_state["mongodb"]["users"].create_index("email", unique=True)
        await app_state["mongodb"]["users"].create_index("username", unique=True)
        print(f"Connected to MongoDB! Using database: {DB_NAME}")
        print("Ensured indexes on 'users' collection (email, username).")
    except Exception as e:
         print(f"ERROR setting up indexes: {e}")


async def shutdown_db_client():
    """Disconnects from MongoDB on application shutdown."""
    if "mongodb_client" in app_state:
        print("Disconnecting from MongoDB...")
        app_state["mongodb_client"].close()
        print("Disconnected.")

# --- Database Dependency Injector ---
async def get_db() -> AsyncIOMotorDatabase:
    """Dependency function to get the database instance for a request."""
    if "mongodb" not in app_state:
         # This should not happen if startup completed successfully
         raise HTTPException(status_code=500, detail="Database connection not available.")
    return app_state["mongodb"]

print("Database setup configured.")


# --- 5. Authentication Dependencies & Logic ---
print("Setting up authentication dependencies...")

async def get_user_from_db(db: AsyncIOMotorDatabase, username: str) -> Optional[UserInDB]:
    """Helper to fetch user from database by username."""
    user_doc = await db["users"].find_one({"username": username})
    if user_doc:
        # Explicitly map _id to id if needed by Pydantic model alias
        if '_id' in user_doc and 'id' not in user_doc:
             user_doc['id'] = str(user_doc['_id'])
        try:
            return UserInDB(**user_doc)
        except Exception as e:
            print(f"Error parsing user from DB: {e}, Data: {user_doc}")
            return None # Or raise an internal server error
    return None

async def authenticate_user(db: AsyncIOMotorDatabase, username: str, password: str) -> Optional[UserInDB]:
    """Authenticates a user against the database."""
    user = await get_user_from_db(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_active_user(
    token: str = Depends(oauth2_scheme), # Gets token from Authorization header
    db: AsyncIOMotorDatabase = Depends(get_db) # Gets DB connection
) -> UserPublic: # Return the public user model (no hash)
    """
    Dependency to get the current logged-in user.
    Verifies JWT token and fetches user from DB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = decode_access_token(token)
    if username is None:
        raise credentials_exception

    user = await get_user_from_db(db, username=username)
    if user is None:
        raise credentials_exception

    # Optional: Check if user is active
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    # Return the public version of the user model
    return UserPublic(**user.dict())

print("Authentication dependencies set up.")


# --- 6. FastAPI App Instance & Middleware ---
print("Creating FastAPI app instance...")
app = FastAPI(
    title="FutureSelf API",
    description="API for FutureSelf application with integrated auth and DB.",
    version="1.0.0",
    on_startup=[startup_db_client], # Run DB connection on startup
    on_shutdown=[shutdown_db_client], # Close DB connection on shutdown
)

# CORS (Cross-Origin Resource Sharing) Middleware
# Allows frontend (e.g., running on localhost:3000) to talk to backend (localhost:8000)
origins = [
     "http://localhost:5173", # Allow your React frontend origin
     # Allow your React frontend origin
    # Add production frontend origins here later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)
print("CORS middleware added.")


# --- 7. Authentication Router/Endpoints ---
# (Ideally in routers/auth.py)
print("Defining authentication routes...")
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    db: AsyncIOMotorDatabase = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends() # Handles username/password form data
):
    """Provides an access token for valid username/password."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
        # Add scopes here if using them: data={"sub": user.username, "scopes": form_data.scopes}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Registers a new user."""
    # Check if user already exists
    existing_user_email = await db["users"].find_one({"email": user_in.email})
    if existing_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    existing_user_username = await db["users"].find_one({"username": user_in.username})
    if existing_user_username:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user_in.password)
    user_id = str(uuid.uuid4()) # Generate a unique ID

    user_db_data = user_in.dict()
    user_db_data["hashed_password"] = hashed_password
    del user_db_data["password"] # Don't store plain password
    user_db_data["_id"] = user_id # Set the _id field
    user_db_data["created_at"] = datetime.utcnow()

    # Insert into database
    try:
        await db["users"].insert_one(user_db_data)
    except Exception as e: # Catch potential duplicate key errors if index check failed somehow
        print(f"Error inserting user: {e}")
        raise HTTPException(status_code=500, detail="Could not register user.")

    # Return the public representation of the created user
    created_user = await db["users"].find_one({"_id": user_id})
    if not created_user:
         raise HTTPException(status_code=500, detail="Failed to retrieve created user.")

    return UserPublic(**created_user) # Use alias mapping


@auth_router.get("/users/me", response_model=UserPublic)
async def read_users_me(current_user: UserPublic = Depends(get_current_active_user)):
    """Returns the details of the currently logged-in user."""
    # The dependency already validated and fetched the user
    return current_user

# --- Include Auth Router ---
app.include_router(auth_router)
print("Authentication routes defined and included.")


# --- 8. Feature Routers ---
print("Importing and including feature routers...")
try:
    # Ensure these files exist and have routers defined within them
    from app.routers import conversation, memories
    app.include_router(conversation.router, prefix="/api/v1")
    app.include_router(memories.router, prefix="/api/v1")
    print("Included 'conversation' and 'memories' routers.")
except ImportError as e:
    print(f"ERROR: Could not import feature routers: {e}")
    print("Make sure 'backend/app/routers/conversation.py' and 'memories.py' exist.")
except AttributeError as e:
    print(f"ERROR: Could not find '.router' attribute in imported module: {e}")
    print("Make sure 'conversation.py' and 'memories.py' define an APIRouter named 'router'.")


# --- 9. Root Endpoint ---
@app.get("/api/v1/", tags=["Root"])
async def read_root():
    """API Root Endpoint."""
    return {"message": "Welcome to the FutureSelf API V1"}

print("--- Main.py setup complete. Starting application server... ---")

# Note: When running with uvicorn, it handles the server loop.
# Example: uvicorn app.main:app --reload --port 8000 --host 0.0.0.0