# backend/app/models/user.py

# --- Essential Imports ---
from typing import Any, Optional, List, Dict
from datetime import datetime
from bson import ObjectId  # Requires pymongo: pip install pymongo

# --- Pydantic V2 Imports ---
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    GetCoreSchemaHandler, # For custom types
)
from pydantic_core import core_schema, PydanticCustomError # For custom types


# --- Pydantic V2 Compliant ObjectId Handling (Class-Based Approach) ---
# <<< THIS IS THE CORRECT CLASS DEFINITION - REPLACES THE 'Annotated' version >>>
class PyObjectId(ObjectId):
    """
    Custom Pydantic V2 type for MongoDB ObjectId, handling validation and serialization.
    Inherits directly from bson.ObjectId.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Defines how Pydantic should handle this type for validation and serialization.
        Args:
            source_type: The source type being annotated (e.g., PyObjectId).
            handler: A callable to get the core schema for other types.
        Returns:
            A core schema definition.
        """
        # Define a validation function specific to this context
        def validate_from_input(value: Any) -> ObjectId:
            """Validates input is a valid ObjectId or str representation."""
            if isinstance(value, ObjectId):
                return value
            # Only attempt conversion if it's a string
            if isinstance(value, str) and ObjectId.is_valid(value):
                return ObjectId(value)
            # Raise a specific error for invalid types or invalid ObjectId strings
            raise PydanticCustomError(
                'object_id_invalid',
                'Value must be a valid BSON ObjectId or its string representation',
                {'value': value}
            )

        # Create a schema that uses our validation function on Python input
        python_schema = core_schema.no_info_plain_validator_function(validate_from_input)

        # Define how to serialize the ObjectId to a string
        serialization_schema = core_schema.plain_serializer_function_ser_schema(
            lambda v: str(v), when_used='json-unless-none', return_schema=core_schema.str_schema()
        )

        # Combine the validation and serialization logic.
        return core_schema.union_schema(
            [
                # Priority 1: Check if it's already an ObjectId instance
                core_schema.is_instance_schema(ObjectId),
                # Priority 2: If not, try validating it using our custom function
                python_schema,
            ],
            serialization=serialization_schema, # Apply serialization rule
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema_obj: core_schema.CoreSchema, handler: GetCoreSchemaHandler
    ) -> Dict[str, Any]:
        """
        Defines how this type should be represented in JSON Schema (e.g., for OpenAPI).
        Args:
            core_schema_obj: The generated core schema for this type.
            handler: A callable to get the JSON schema for other types.
        Returns:
            A dictionary representing the JSON schema.
        """
        json_schema = handler(core_schema_obj)
        json_schema.update(type='string', format='objectid') # Represent as string in JSON schema
        return json_schema

# --- User Preferences Model ---
class UserPreferences(BaseModel):
    """Preferences settings for the user account."""
    memory_storage_opt_in: bool = Field(True, description="User agrees to store memories.")
    data_purging_preference: Optional[str] = Field(None, description="User's preference for automatic data deletion (e.g., 'manual', '30_days_inactive').")
    communication_style_preference: Optional[str] = Field(None, description="Preferred communication style for the Future Self (e.g., 'formal', 'casual', 'empathetic').")
    receive_notifications: bool = Field(False, description="User opts-in to receive system notifications.")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str} # Fallback encoder
    }


# --- Future Self Persona Characteristics ---
class PersonaCharacteristics(BaseModel):
    """Represents the generated characteristics of the user's future self."""
    core_trait: Optional[str] = Field(None, description="Dominant personality trait (e.g., Wise, Reflective, Pragmatic).")
    voice_tone: Optional[str] = Field(None, description="Predominant tone of voice (e.g., Calm, Empathetic, Direct).")
    key_life_lessons: List[str] = Field(default_factory=list, description="List of key life lessons derived from memories.")
    wisdom_snippets: List[str] = Field(default_factory=list, description="Short pieces of advice or perspective.")
    consistency_markers: Optional[Dict[str, Any]] = Field(None, description="Internal data used by LLM to maintain persona consistency.")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            ObjectId: str, # Fallback
            datetime: lambda dt: dt.isoformat()
        }
    }


# --- Base User Model (Common Fields) ---
class UserBase(BaseModel):
    """Base model with common user fields."""
    email: EmailStr = Field(..., description="Unique email address for the user.")
    username: Optional[str] = Field(None, description="Optional unique username.")
    full_name: Optional[str] = Field(None, description="User's full name.")
    is_active: bool = Field(True, description="Whether the user account is active.")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str} # Fallback
    }

# --- User Model for Creation ---
class UserCreate(UserBase):
    """Model used when creating a new user (includes password)."""
    password: str = Field(..., min_length=8, description="User's password (will be hashed before storage).")
    initial_values: Optional[List[str]] = Field(default_factory=list, description="Initial core values provided during signup.")
    initial_aspirations: Optional[List[str]] = Field(default_factory=list, description="Initial life aspirations provided during signup.")


# --- User Model for Update ---
class UserUpdate(BaseModel):
    """Model used when updating user information (all fields optional)."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[UserPreferences] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str} # Fallback
    }


# --- User Model as stored in Database ---
class UserInDB(UserBase):
    """Model representing the user document as stored in MongoDB."""
    # Use the new class-based PyObjectId type hint directly.
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    hashed_password: str = Field(..., description="Stored hashed password.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    persona: Optional[PersonaCharacteristics] = Field(None, description="Embedded future self persona characteristics.")
    life_snapshot: Optional[Dict[str, Any]] = Field(None, description="Data from the initial life snapshot questionnaire.")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()} # Only need datetime here
    }


# --- User Model for API Responses (Public) ---
class User(UserBase):
    """Model representing user data returned by the API (excludes sensitive info)."""
    id: PyObjectId = Field(..., description="Unique user identifier.")
    created_at: datetime
    updated_at: datetime
    preferences: UserPreferences
    persona: Optional[PersonaCharacteristics]

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_encoders": {datetime: lambda dt: dt.isoformat()} # Only need datetime here
    }