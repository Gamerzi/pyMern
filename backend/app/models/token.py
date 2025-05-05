# backend/app/models/token.py
from pydantic import BaseModel
from typing import Optional

class TokenPayload(BaseModel):
   """Pydantic model for the expected payload within a JWT."""
   sub: Optional[str] = None
   # Add other fields you might include in the token payload if needed
   # exp: Optional[int] = None # 'exp' is usually handled by jose directly