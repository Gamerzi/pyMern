# backend/app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import jwt, JWTError # Import JWT handling functions
from passlib.context import CryptContext # Import password hashing context
from pydantic import ValidationError

# --- App Modules ---
# Import settings from the config module within the same directory
from app.core.config import settings # Use 'app.' prefix
from app.models.token import TokenPayload # Use 'app.' prefix

# --- Password Hashing Setup ---
# Configure passlib context: Use bcrypt, mark others as deprecated auto-detected
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Password Utility Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a stored hash using the configured context.
    Args:
        plain_password: The password attempt from the user.
        hashed_password: The stored hash from the database.
    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Handle potential errors during verification (e.g., invalid hash format)
        return False

def get_password_hash(password: str) -> str:
    """
    Generates a secure hash for a plain password using the configured context.
    Args:
        password: The plain text password to hash.
    Returns:
        The generated password hash string.
    """
    return pwd_context.hash(password)


# --- JWT Handling ---

# Load JWT settings from the central configuration
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY # Ensure this is loaded securely from your config!


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a JWT access token with an optional expiry delta.
    Args:
        subject: The data to encode in the token's 'sub' (subject) claim.
                 Should uniquely identify the user (e.g., email or user ID as string).
        expires_delta: Optional timedelta object for token expiry duration.
                       If None, uses default ACCESS_TOKEN_EXPIRE_MINUTES from settings.
    Returns:
        The encoded JWT access token as a string.
    """
    # Calculate expiry time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Use default expiry from settings if no delta is provided
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Prepare the data payload for the token
    to_encode = {"exp": expire, "sub": str(subject)} # Ensure subject is always a string

    # Encode the payload into a JWT string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Optional but Recommended: Function to Decode and Validate Tokens ---
# This function will be essential later for creating dependencies that
# protect your other API endpoints, ensuring only logged-in users can access them.

def decode_token(token: str) -> Optional[str]:
    """
    Decodes a JWT token, verifies its signature and expiry,
    and validates its payload structure.
    Args:
        token: The JWT token string to decode.
    Returns:
        The subject ('sub' claim) from the token payload if the token is valid,
        otherwise returns None.
    """
    try:
        # Decode the token. This automatically verifies signature and expiry.
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM] # Specify allowed algorithms
        )
        # Validate the payload structure against the TokenPayload model
        # This ensures the 'sub' field exists (even if None, though decode should error if missing)
        token_data = TokenPayload(**payload)

        # Return the subject claim if validation passes
        # It might be None if 'sub' was optional and not present,
        # but usually 'sub' should be mandatory for auth tokens.
        return token_data.sub

    except (JWTError, ValidationError, TypeError, AttributeError) as e:
        # Log the error for debugging (optional)
        # print(f"Token decode/validation failed: {e}")
        # Return None if any error occurs during decoding or validation
        return None