# future-self/backend/app/routers/conversations.py

import os
import uuid
import asyncio # Needed for placeholder simulation and potentially real async tasks
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
from groq import Groq, AsyncGroq # Import Groq SDK


# --- Environment Variable Loading (Best done in main.py or config module) ---
# from dotenv import load_dotenv
# load_dotenv(dotenv_path="../../config/.env") # Adjust path as needed
# Ensure GROQ_API_KEY is set in your .env file

# --- Pydantic Models (Ideally in app/models/conversation.py) ---
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user", "assistant" (standard for LLMs), or "future_self" if you map it
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationBase(BaseModel):
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # title: Optional[str] = None

class Conversation(ConversationBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = []

class ConversationCreateRequest(BaseModel):
    initial_message: str

class SendMessageRequest(BaseModel):
    content: str

# --- Placeholder Dependencies ---
async def get_db():
    print("DEBUG: Yielding dummy DB connection")
    yield {"conversations": {}, "users": {}} # Dummy store

class User(BaseModel): # Placeholder User model
    id: str
    username: str
    # IMPORTANT: Store user's explicit consent for data processing, especially PHI
    # has_consented_to_phi_processing: bool = False

async def get_current_active_user(db = Depends(get_db)) -> User:
    print("DEBUG: Returning dummy authenticated user")
    # !! Replace with actual authentication and user loading !!
    # !! Ensure loaded user includes consent status if handling PHI !!
    return User(id="user_123", username="testuser") # Add consent flag if needed


# --- Persona Service with Groq Integration ---

class PersonaService:
    """
    Service interacting with the Groq LLM and managing persona logic.

    WARNING: Handles potentially sensitive user data (including PHI if entered).
    Ensure compliance with regulations (e.g., HIPAA) and Groq's data policies
    BEFORE sending PHI to the Groq API. Standard Groq APIs are likely NOT compliant.
    Obtain EXPLICIT user consent.
    """
    def __init__(self, db):
        self.db = db # Used to fetch user memories, profile, etc.
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            # Critical: Do not proceed without API key configuration
            raise ValueError("GROQ_API_KEY environment variable not set.")
        # Use AsyncGroq for FastAPI compatibility
        self.groq_client = AsyncGroq(api_key=self.groq_api_key)
        # Consider making the model configurable
        self.model_name = "llama3-8b-8192" # Example model, choose based on availability/needs

    async def _fetch_user_context(self, user: User) -> str:
        """
        Placeholder: Fetches relevant user memories and profile info from DB.
        Formats it into a string suitable for the LLM prompt preamble.
        !! CRITICAL: Filter/anonymize sensitive PHI here if possible,
        !! or ensure user consent covers sending raw data.
        """
        # Example: Fetching simplified memories (replace with real DB query)
        # user_memories = await db_get_user_memories(self.db, user.id, limit=10)
        # memory_summary = " Key memories: " + "; ".join([m.summary for m in user_memories])
        # profile_summary = f" User values: {user.values}" # Assuming user has values stored
        # return profile_summary + memory_summary
        await asyncio.sleep(0.05) # Simulate DB lookup
        return f"Some context about {user.username} based on their stored memories and profile will be inserted here. Focus on wisdom and perspective."


    async def _generate_response(self, user: User, conversation_history: List[Message]) -> str:
        """Generates a response using the Groq LLM."""

        # 1. Fetch additional user context (memories, profile)
        user_context = await self._fetch_user_context(user)

        # 2. Construct the System Prompt (Persona Definition)
        # This is crucial for maintaining the "60-year-old self" persona
        system_prompt = f"""You are an AI simulating the 60-year-old version of the user '{user.username}'.
Act as a wise, reflective, and kind future self, offering perspective based on a lifetime of experience (informed by the user's actual stored memories and profile, provided below).
Do NOT give medical, legal, or financial advice. Focus on emotional insight, long-term perspective, and gentle guidance.
Keep your persona consistent. Refer to the user in the second person (you).
User context: {user_context}

VERY IMPORTANT: Do not provide medical diagnoses or treatment recommendations, even if the user mentions health issues. You can acknowledge their feelings but redirect to seeking professional medical help.
"""

        # 3. Format conversation history for the LLM API
        # Groq expects roles like "user" and "assistant". Map "future_self" to "assistant".
        messages_for_api = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            role = "assistant" if msg.role == "future_self" else msg.role
            messages_for_api.append({"role": role, "content": msg.content})

        # 4. Call Groq API
        try:
            chat_completion = await self.groq_client.chat.completions.create(
                messages=messages_for_api,
                model=self.model_name,
                temperature=0.7, # Adjust creativity/determinism
                max_tokens=300, # Limit response length
                # Add other parameters as needed (top_p, etc.)
            )
            response_content = chat_completion.choices[0].message.content

            # 5. Post-processing (Optional but recommended)
            # - Check for harmful content (though Groq might have filters)
            # - Add a standard disclaimer if sensitive topics were discussed
            # - Ensure persona consistency (though the system prompt helps)
            if "doctor" in response_content or "medical advice" in response_content: # Basic check
                 response_content += "\n\n(Remember, I am an AI and cannot provide medical advice. Please consult a healthcare professional for health concerns.)"

            return response_content.strip()

        except Exception as e:
            # Log the specific error from Groq or network issues
            print(f"Error calling Groq API: {e}")
            # Consider more specific error handling based on Groq exceptions
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not get response from Future Self AI service due to: {e}"
            )


    async def get_initial_response(self, user: User, first_message: str) -> str:
        """Generates the first 'future self' response using Groq."""
        print(f"DEBUG: PersonaService generating initial Groq response for user {user.id}")
        # History contains only the first user message
        initial_history = [Message(role="user", content=first_message)]
        return await self._generate_response(user, initial_history)

    async def get_next_response(self, user: User, conversation_history: List[Message]) -> str:
        """Generates the next 'future self' response using Groq based on history."""
        print(f"DEBUG: PersonaService generating next Groq response for user {user.id}")
        # Ensure history isn't excessively long (implement truncation if needed)
        # Simple truncation: keep last N messages (e.g., 10)
        max_history_len = 10
        truncated_history = conversation_history[-max_history_len:]
        return await self._generate_response(user, truncated_history)


# --- FastAPI Router ---
router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
    responses={404: {"description": "Not found"}},
)

# --- Database Simulation Helpers (Replace with actual DB logic) ---
async def db_create_conversation(db, conversation: Conversation) -> Conversation:
    if "conversations" not in db: db["conversations"] = {}
    db["conversations"][conversation.id] = conversation.dict()
    print(f"DEBUG: DB creating conversation {conversation.id}")
    return conversation

async def db_get_conversation(db, conversation_id: str, user_id: str) -> Optional[Conversation]:
    print(f"DEBUG: DB fetching conversation {conversation_id} for user {user_id}")
    conv_data = db.get("conversations", {}).get(conversation_id)
    # --- IMPORTANT: Ensure user owns the conversation ---
    if conv_data and conv_data["user_id"] == user_id:
        # Convert roles back if needed, though storing as user/assistant might be simpler
        return Conversation(**conv_data)
    return None

async def db_update_conversation(db, conversation: Conversation) -> Conversation:
    if "conversations" not in db: db["conversations"] = {}
    conversation.updated_at = datetime.utcnow()
    # --- Store messages with consistent roles (user/assistant) ---
    # You might want to persist the 'future_self' role or map it consistently
    db["conversations"][conversation.id] = conversation.dict()
    print(f"DEBUG: DB updating conversation {conversation.id}")
    return conversation

async def db_get_user_conversations(db, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
    print(f"DEBUG: DB fetching conversations for user {user_id} (skip={skip}, limit={limit})")
    all_convs = [
        Conversation(**data) for data in db.get("conversations", {}).values()
        if data["user_id"] == user_id
    ]
    all_convs.sort(key=lambda c: c.updated_at, reverse=True)
    return all_convs[skip : skip + limit]

# --- API Endpoints ---

@router.post(
    "/",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation",
    description="Creates a new conversation session and gets the first response from the Groq-powered future self.",
)
async def start_conversation(
    request: ConversationCreateRequest = Body(...),
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Starts a new conversation thread using Groq LLM.

    - Takes the user's first message.
    - **WARNING:** User input might contain sensitive data (PHI). Ensure user consent
      and compliance before processing and sending data to Groq.
    - Creates a conversation record.
    - Generates the initial 'future self' response via PersonaService/Groq.
    - Returns the conversation including the initial messages.
    """
    # --- !! PHI Consent Check !! ---
    # if current_user.might_input_phi and not current_user.has_consented_to_phi_processing:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="User consent required for processing potentially sensitive data."
    #     )

    persona_service = PersonaService(db) # Instantiate service

    user_message = Message(role="user", content=request.initial_message)
    new_conversation = Conversation(user_id=current_user.id, messages=[user_message])

    try:
        future_self_content = await persona_service.get_initial_response(
            user=current_user, first_message=user_message.content
        )
    except HTTPException as http_exc: # Catch exceptions from PersonaService
        raise http_exc
    except Exception as e:
        print(f"Unhandled error getting initial AI response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error generating response.")

    # Store the AI response with a consistent role, e.g., "assistant" or your custom "future_self"
    future_self_message = Message(role="future_self", content=future_self_content) # Or "assistant"
    new_conversation.messages.append(future_self_message)
    new_conversation.updated_at = future_self_message.timestamp

    try:
        created_conversation = await db_create_conversation(db, new_conversation)
    except Exception as e:
        print(f"Error saving conversation to DB: {e}")
        raise HTTPException(status_code=500, detail="Could not save the new conversation.")

    return created_conversation


@router.post(
    "/{conversation_id}/messages",
    response_model=Conversation,
    status_code=status.HTTP_200_OK,
    summary="Send a message to an existing conversation",
    description="Adds a user message and gets the next Groq-powered future self response.",
)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest = Body(...),
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Sends a subsequent message in an existing conversation using Groq LLM.

    - Retrieves conversation history.
    - **WARNING:** Handles user input (potential PHI) and conversation history.
      Ensure ongoing user consent and compliance.
    - Appends the new user message.
    - Calls PersonaService/Groq with updated history.
    - Appends the 'future self' response.
    - Updates and returns the conversation.
    """
    # --- !! PHI Consent Check (if applicable) !! ---
    # if current_user.might_input_phi and not current_user.has_consented_to_phi_processing:
    #     raise HTTPException(status_code=403, detail="User consent required.")

    persona_service = PersonaService(db)
    conversation = await db_get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied.")

    user_message = Message(role="user", content=request.content)
    conversation.messages.append(user_message)
    conversation.updated_at = user_message.timestamp # Update timestamp before AI call

    try:
        future_self_content = await persona_service.get_next_response(
            user=current_user, conversation_history=conversation.messages
        )
    except HTTPException as http_exc: # Catch specific HTTP exceptions from service
         # Consider saving the user message even if AI fails?
         # await db_update_conversation(db, conversation) # Save up to user message
         raise http_exc
    except Exception as e:
        print(f"Unhandled error getting next AI response: {e}")
        # await db_update_conversation(db, conversation) # Save up to user message?
        raise HTTPException(status_code=500, detail="Internal server error generating response.")


    future_self_message = Message(role="future_self", content=future_self_content) # Or "assistant"
    conversation.messages.append(future_self_message)
    conversation.updated_at = future_self_message.timestamp # Final update

    try:
        updated_conversation = await db_update_conversation(db, conversation)
    except Exception as e:
        print(f"Error updating conversation in DB: {e}")
        raise HTTPException(status_code=500, detail="Could not save the updated conversation.")

    return updated_conversation


@router.get(
    "/{conversation_id}",
    response_model=Conversation,
    summary="Get a specific conversation",
    description="Retrieves the full history of a specific conversation.",
)
async def get_conversation(
    conversation_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    conversation = await db_get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied.")
    return conversation


@router.get(
    "/",
    response_model=List[Conversation],
    summary="List user's conversations",
    description="Retrieves a list of conversations for the current user.",
)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if limit > 100: limit = 100
    conversations = await db_get_user_conversations(db, current_user.id, skip=skip, limit=limit)
    return conversations

# --- Include in main.py ---
# import conversations
# app.include_router(conversations.router)