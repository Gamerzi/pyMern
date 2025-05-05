# manual_test_user.py

import sys
import os
from datetime import datetime

# --- Attempt to import ObjectId ---
try:
    from bson import ObjectId # Requires 'pymongo' install: pip install pymongo
except ImportError:
    print("❌ ERROR: 'pymongo' library not found. Please install it: pip install pymongo")
    sys.exit(1)

# --- Manually add project root to sys.path ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End sys.path modification ---

try:
    # Now try importing the models and ValidationError
    from pydantic import ValidationError
    # Ensure user.py contains the CLASS-BASED PyObjectId definition
    from backend.app.models.user import (
        UserBase, UserCreate, UserUpdate, UserInDB, User,
        UserPreferences, PersonaCharacteristics, PyObjectId
    )
    print("✅ Successfully imported User models.")
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    print("Ensure 'backend/app/models/user.py' exists and contains the CLASS-BASED PyObjectId definition.")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1) # Exit if import fails
except Exception as e:
    # Catch other potential errors during import (like the schema generation error)
    print(f"❌ An unexpected error occurred during import or model definition: {e}")
    # Print full traceback for detailed debugging
    import traceback
    traceback.print_exc()
    sys.exit(1)


# --- Test Data ---

valid_user_create_data = {
    "email": "test@example.com",
    "password": "validpassword123",
    "full_name": "Test User",
    "initial_values": ["Integrity"],
    "initial_aspirations": ["Learn Piano"]
}

invalid_user_create_data_email = {
    "email": "test@", # Invalid email
    "password": "validpassword123",
}

invalid_user_create_data_password = {
    "email": "test@example.com",
    "password": "short", # Invalid password (too short)
}

# Create a valid ObjectId instance for testing
try:
    test_object_id = ObjectId()
except Exception as e:
    print(f"❌ Failed to create ObjectId for testing: {e}")
    sys.exit(1)

user_in_db_dict_data = {
    "_id": test_object_id, # Use the alias for loading from dict
    "email": "dbuser@example.com",
    "username": "dbuser",
    "full_name": "Database User",
    "hashed_password": "a_very_secure_hashed_password",
    "is_active": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow(),
    "preferences": {
        "memory_storage_opt_in": True,
        "communication_style_preference": "empathetic"
    },
    "persona": {
        "core_trait": "Wise",
        "key_life_lessons": ["Patience is key"],
        "last_updated": datetime.utcnow()
    },
    "life_snapshot": {"childhood_dream": "Astronaut"}
}


# --- Test Functions ---

def run_tests():
    print("\n--- Running Manual Tests for user.py Models (Pydantic V2 - Class-Based PyObjectId) ---")
    errors = 0

    # Test 1: UserPreferences Defaults
    print("\n[Test 1] UserPreferences Defaults")
    try:
        prefs = UserPreferences()
        assert prefs.memory_storage_opt_in is True
        assert prefs.communication_style_preference is None
        print("  ✅ Passed")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors += 1

    # Test 2: PersonaCharacteristics Defaults
    print("\n[Test 2] PersonaCharacteristics Defaults")
    try:
        persona = PersonaCharacteristics()
        assert persona.core_trait is None
        assert persona.key_life_lessons == []
        assert isinstance(persona.last_updated, datetime)
        print("  ✅ Passed")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors += 1

    # Test 3: Valid UserCreate Instantiation
    print("\n[Test 3] Valid UserCreate Instantiation")
    try:
        user = UserCreate(**valid_user_create_data)
        assert user.email == valid_user_create_data["email"]
        assert user.password == valid_user_create_data["password"] # Password still plain here
        assert user.is_active is True # Check default
        print("  ✅ Passed")
    except ValidationError as e:
        print(f"  ❌ FAILED: Unexpected validation error: {e}")
        errors += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors += 1

    # Test 4: Invalid UserCreate (Bad Email) - Expect ValidationError
    print("\n[Test 4] Invalid UserCreate (Bad Email)")
    try:
        UserCreate(**invalid_user_create_data_email)
        print("  ❌ FAILED: Expected ValidationError but none was raised.")
        errors += 1
    except ValidationError:
        print("  ✅ Passed (Caught expected ValidationError)")
    except Exception as e:
        print(f"  ❌ FAILED: Unexpected error: {e}")
        errors += 1

    # Test 5: Invalid UserCreate (Short Password) - Expect ValidationError
    print("\n[Test 5] Invalid UserCreate (Short Password)")
    try:
        UserCreate(**invalid_user_create_data_password)
        print("  ❌ FAILED: Expected ValidationError but none was raised.")
        errors += 1
    except ValidationError as e:
        password_error_found = any('password' in loc for err in e.errors() for loc in err.get('loc',[]))
        if password_error_found:
             print("  ✅ Passed (Caught expected ValidationError for password)")
        else:
             print(f"  ⚠️ Passed (Caught ValidationError, but maybe not for password? Details: {e})")
    except Exception as e:
        print(f"  ❌ FAILED: Unexpected error: {e}")
        errors += 1

    # Test 6: UserInDB Instantiation from Dict (Simulating DB Load)
    print("\n[Test 6] UserInDB Instantiation from Dict")
    try:
        user_db = UserInDB(**user_in_db_dict_data)
        assert isinstance(user_db.id, ObjectId) # Check if it's an ObjectId
        assert user_db.id == user_in_db_dict_data["_id"] # Check alias mapping
        assert user_db.email == user_in_db_dict_data["email"]
        assert isinstance(user_db.preferences, UserPreferences)
        assert user_db.preferences.communication_style_preference == "empathetic"
        assert isinstance(user_db.persona, PersonaCharacteristics)
        assert user_db.persona.core_trait == "Wise"
        print("  ✅ Passed")
    except ValidationError as e:
        print(f"  ❌ FAILED: Unexpected validation error: {e}")
        errors += 1
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        errors += 1

    # Test 7: UserInDB Serialization to Dict (JSON mode)
    print("\n[Test 7] UserInDB Serialization to Dict (JSON mode)")
    try:
        user_db = UserInDB(**user_in_db_dict_data)
        # Pydantic V2: Use model_dump with mode='json' and by_alias=True
        serialized_dict = user_db.model_dump(mode='json', by_alias=True) # <-- Use model_dump() in V2
        assert "_id" in serialized_dict, "'_id' alias missing in JSON dump"
        assert "id" not in serialized_dict, "'id' field should not be in alias dump"
        # Check if the serialized ID is a string
        assert isinstance(serialized_dict.get("_id"), str), \
            f"Expected _id to be str in dump, but got {type(serialized_dict.get('_id'))}"
        # Compare string representations
        assert serialized_dict["_id"] == str(user_in_db_dict_data["_id"])
        assert isinstance(serialized_dict.get("preferences"), dict) # .model_dump() converts nested models
        print(f"  Output dict (JSON mode): {serialized_dict}")
        print("  ✅ Passed")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        # Add traceback for better debugging during serialization issues
        import traceback
        traceback.print_exc()
        errors += 1

    # Test 8: User (Response Model) Creation from UserInDB
    print("\n[Test 8] User (Response Model) Creation from UserInDB")
    try:
        user_db = UserInDB(**user_in_db_dict_data)
        # Pydantic V2: Use model_validate for ORM-like creation (from_attributes=True)
        user_response = User.model_validate(user_db)

        assert isinstance(user_response.id, ObjectId) # ID should be ObjectId instance
        assert user_response.id == user_db.id # Compare ObjectIds
        assert user_response.email == user_db.email
        assert isinstance(user_response.preferences, UserPreferences) # Check nested model type

        # Check sensitive field is NOT present
        has_password = hasattr(user_response, 'hashed_password')
        assert not has_password, "hashed_password should not be present in User response model"
        print("  ✅ Passed (Sensitive data excluded)")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        errors += 1

    # --- Summary ---
    print("\n--- Test Summary ---")
    if errors == 0:
        print("🎉 All manual tests passed!")
    else:
        print(f"🔥 {errors} test(s) failed.")
    print("--------------------\n")
    return errors # Return number of errors


# --- Run the Tests ---
if __name__ == "__main__":
    # Make sure pymongo is installed
    try:
        import pymongo
    except ImportError:
        print("Reminder: 'pymongo' is required for ObjectId. Run: pip install pymongo")
        sys.exit(1)

    num_errors = run_tests()
    sys.exit(num_errors) # Exit with status 0 if no errors, >0 otherwise