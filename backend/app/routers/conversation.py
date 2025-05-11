# future-self/backend/app/routers/conversations.py

import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

# --- CORRECTED IMPORT: Added Query ---
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
# --- END CORRECTION ---

from pydantic import BaseModel, Field, VERSION as PYDANTIC_VERSION
from groq import Groq, AsyncGroq
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

# --- Logger ---
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO) # Configure in main.py

# --- REAL Dependency Imports ---
try:
    from ..main import get_db, get_current_active_user, UserPublic
    User = UserPublic
    logger.info("conversations.py: Successfully imported REAL dependencies from ..main.")
except ImportError as e:
    logger.critical(
        f"conversations.py: CRITICAL ERROR - FAILED to import REAL dependencies from ..main: {e}. "
        "This router WILL NOT function with actual DB or Auth. Using placeholders.",
        exc_info=True
    )
    class User(BaseModel): id: str = "placeholder_conv_id"; username: str = "placeholder_conv_user"
    async def get_db() -> AsyncIOMotorDatabase:
        logger.error("conversations.py: FATAL - Using PLACEHOLDER get_db().")
        raise NotImplementedError("Placeholder get_db() called. Real 'get_db' failed to import.")
    async def get_current_active_user() -> User:
        logger.error("conversations.py: FATAL - Using PLACEHOLDER get_current_active_user().")
        raise NotImplementedError("Placeholder get_current_active_user() called. Real 'get_current_active_user' failed to import.")

# --- Configuration for MongoDB Collections ---
CONVERSATIONS_COLLECTION_NAME = "conversations_collection"
MEMORIES_COLLECTION_NAME_FOR_CONTEXT = "futureself"

# --- Pydantic Models ---
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationBase(BaseModel):
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    title: Optional[str] = None

class ConversationInDB(ConversationBase):
    id: str = Field(alias="_id")
    messages: List[Message] = []
    class Config: from_attributes = True; populate_by_name = True

class ConversationResponse(ConversationBase):
    id: str
    messages: List[Message] = []
    class Config: from_attributes = True

class ConversationCreateRequest(BaseModel):
    initial_message: str
    title: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str

# --- Persona Service with Groq Integration AND MEMORY FETCHING ---
class PersonaService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
        # --- !!! HARDCODED API KEY FOR TESTING !!! ---
        # --- !!! REMOVE THIS AND REVERT AFTER TESTING !!! ---
        self.groq_api_key = "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" # YOUR HARDCODED KEY
        logger.warning("!!! conversations.py WARNING: GROQ_API_KEY IS CURRENTLY HARDCODED IN PersonaService FOR TESTING !!!")
        # --- !!! END OF HARDCODED SECTION !!! ---

        if not self.groq_api_key:
            logger.critical("GROQ_API_KEY is unexpectedly empty even after hardcoding.")
            raise ValueError("CRITICAL: GROQ_API_KEY is not configured (hardcoding failed).")
        
        logger.info(f"PersonaService: Using hardcoded GROQ_API_KEY: "
                    f"{self.groq_api_key[:7]}...{self.groq_api_key[-4:]}")

        try:
            self.groq_client = AsyncGroq(api_key=self.groq_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Groq client with hardcoded key: {e}", exc_info=True)
            raise RuntimeError(f"Could not initialize Groq client: {e}")
            
        self.model_name = os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192") # Still get model from env or default
        # Or hardcode for test: self.model_name = "llama3-8b-8192"
        logger.info(f"PersonaService: Using model '{self.model_name}'.")


    async def _fetch_user_memories_for_context(self, user: User, limit: int = 5) -> str:
        logger.info(f"Fetching memories for user '{user.id}' from '{MEMORIES_COLLECTION_NAME_FOR_CONTEXT}' collection.")
        if not isinstance(self.db, AsyncIOMotorDatabase): # Check if we have a real DB object
            logger.warning(f"PersonaService._fetch_user_memories_for_context using non-DB object (type: {type(self.db)}). Likely placeholder. Returning no memory context.")
            return "No specific memories available for context (using placeholder database)."

        memories_collection: AsyncIOMotorCollection = self.db[MEMORIES_COLLECTION_NAME_FOR_CONTEXT]
        try:
            cursor = memories_collection.find({"user_id": user.id}).sort("created_at", -1).limit(limit)
            user_memories_docs = await cursor.to_list(length=limit)
            if not user_memories_docs:
                logger.info(f"No memories found for user '{user.id}' in '{MEMORIES_COLLECTION_NAME_FOR_CONTEXT}'.")
                return "User has not recorded specific memories relevant to this discussion yet."
            formatted_memories = []
            for i, mem_doc in enumerate(user_memories_docs):
                title = mem_doc.get("title", "Untitled Memory")
                description = mem_doc.get("description", "")
                description_snippet = (description[:100] + '...') if len(description) > 103 else description
                tags = ", ".join(mem_doc.get("tags", []))
                formatted_memories.append(
                    f"  Memory {i+1}: '{title}' (Tags: {tags if tags else 'None'}). Snippet: \"{description_snippet}\""
                )
            memory_summary = "\nHere are some relevant past memories to consider:\n" + "\n".join(formatted_memories)
            logger.info(f"Formatted memory context for user '{user.id}': {memory_summary[:200]}...")
            return memory_summary
        except Exception as e:
            logger.error(f"Error fetching memories for user '{user.id}': {e}", exc_info=True)
            return "There was an issue recalling specific memories at this time."

    async def _generate_response(self, user: User, conversation_history: List[Message]) -> str:
        memory_context = await self._fetch_user_memories_for_context(user)
        system_prompt = f"""You are an AI simulating the 60-year-old version of the user '{user.username}'.
Act as a wise, reflective, and kind future self, offering perspective based on a lifetime of experience.
Your insights should be informed by the user's actual stored memories and profile, provided below if available.
Do NOT give medical, legal, or financial advice. Focus on emotional insight, long-term perspective, and gentle guidance.
Keep your persona consistent. Refer to the user in the second person (you).

User's Past Memories Context:
{memory_context}

VERY IMPORTANT: Do not provide medical diagnoses or treatment recommendations. Acknowledge feelings but redirect to professionals for health concerns.
"""
        messages_for_api = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            role = "assistant" if msg.role == "future_self" else msg.role
            messages_for_api.append({"role": role, "content": msg.content})
        
        logger.debug(f"Calling Groq API for user '{user.id}'. Model: {self.model_name}. System prompt includes memory context.")
        try:
            chat_completion = await self.groq_client.chat.completions.create(
                messages=messages_for_api, model=self.model_name, temperature=0.7, max_tokens=450,
            )
            response_content = chat_completion.choices[0].message.content.strip()
            return response_content
        except Exception as e:
            error_message = f"Error with AI service (Groq)."; status_code_to_raise = status.HTTP_503_SERVICE_UNAVAILABLE
            if hasattr(e, 'status_code'): status_code_to_raise = e.status_code; error_message = f"AI service error (Status {e.status_code})"
            if hasattr(e, 'message'): error_message += f": {e.message}"
            elif hasattr(e, 'body') and e.body and 'error' in e.body: error_message += f": {e.body['error'].get('message', str(e.body['error']))}"
            else: error_message += f": {str(e)}"
            if hasattr(e, 'status_code') and e.status_code == 401: logger.error(f"CRITICAL GROQ API ERROR: 401. Detail: {error_message}"); error_message = "AI service authentication failed: Invalid API Key."
            logger.error(f"Groq API call failed: {error_message}", exc_info=True)
            raise HTTPException(status_code=status_code_to_raise if not (hasattr(e, 'status_code') and e.status_code == 401) else status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

    async def get_initial_response(self, user: User, first_message_content: str) -> str:
        initial_history = [Message(role="user", content=first_message_content)]
        return await self._generate_response(user, initial_history)

    async def get_next_response(self, user: User, conversation_history: List[Message]) -> str:
        max_history_messages = 10
        truncated_history = conversation_history[-max_history_messages:] if len(conversation_history) > max_history_messages else conversation_history
        return await self._generate_response(user, truncated_history)

# --- FastAPI Router ---
router = APIRouter(
    tags=["Conversations"],
    responses={404: {"description": "Conversation resource not found"}},
    dependencies=[Depends(get_current_active_user)]
)

# --- Database Interaction Helpers for Conversations ---
async def db_create_conversation(db: AsyncIOMotorDatabase, conversation: ConversationInDB) -> ConversationInDB:
    logger.info(f"Creating new conversation '{conversation.id}' for user '{conversation.user_id}' in DB.")
    if not isinstance(db, AsyncIOMotorDatabase):
        logger.error("db_create_conversation: `db` is not AsyncIOMotorDatabase. Placeholder active.")
        raise HTTPException(status_code=500, detail="DB service misconfigured for conversation creation.")
    try:
        conversations_collection: AsyncIOMotorCollection = db[CONVERSATIONS_COLLECTION_NAME]
        doc_to_insert = conversation.model_dump(by_alias=True) if hasattr(conversation, "model_dump") else conversation.dict(by_alias=True)
        insert_result = await conversations_collection.insert_one(doc_to_insert)
        if not insert_result.inserted_id:
            logger.error(f"Failed to insert conversation '{conversation.id}' into DB.")
            raise HTTPException(status_code=500, detail="Could not save new conversation.")
        created_doc = await conversations_collection.find_one({"_id": insert_result.inserted_id})
        if not created_doc:
            logger.error(f"Failed to retrieve conversation '{conversation.id}' after insert.")
            raise HTTPException(status_code=500, detail="Error retrieving conversation post-creation.")
        return ConversationInDB(**created_doc)
    except Exception as e:
        logger.error(f"DB error creating conversation '{conversation.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="DB error during conversation creation.")

async def db_get_conversation(db: AsyncIOMotorDatabase, conversation_id: str, user_id: str) -> Optional[ConversationInDB]:
    logger.debug(f"Fetching conversation '{conversation_id}' for user '{user_id}'.")
    if not isinstance(db, AsyncIOMotorDatabase):
        logger.error("db_get_conversation: `db` is not AsyncIOMotorDatabase. Placeholder active.")
        return None
    try:
        conversations_collection: AsyncIOMotorCollection = db[CONVERSATIONS_COLLECTION_NAME]
        conv_doc = await conversations_collection.find_one({"_id": conversation_id, "user_id": user_id})
        return ConversationInDB(**conv_doc) if conv_doc else None
    except Exception as e:
        logger.error(f"DB error fetching conversation '{conversation_id}': {e}", exc_info=True)
        return None

async def db_update_conversation(db: AsyncIOMotorDatabase, conversation: ConversationInDB) -> ConversationInDB:
    logger.info(f"Updating conversation '{conversation.id}' for user '{conversation.user_id}'.")
    if not isinstance(db, AsyncIOMotorDatabase):
        logger.error("db_update_conversation: `db` is not AsyncIOMotorDatabase. Placeholder active.")
        raise HTTPException(status_code=500, detail="DB service misconfigured for conversation update.")
    try:
        conversations_collection: AsyncIOMotorCollection = db[CONVERSATIONS_COLLECTION_NAME]
        conversation.updated_at = datetime.utcnow()
        doc_to_update = conversation.model_dump(by_alias=True) if hasattr(conversation, "model_dump") else conversation.dict(by_alias=True)
        update_result = await conversations_collection.replace_one(
            {"_id": conversation.id, "user_id": conversation.user_id}, doc_to_update
        )
        if update_result.matched_count == 0:
            logger.warning(f"Conversation '{conversation.id}' not found or user mismatch during update.")
            raise HTTPException(status_code=404, detail="Conversation not found or access denied for update.")
        updated_doc = await conversations_collection.find_one({"_id": conversation.id})
        if not updated_doc:
            logger.error(f"Failed to retrieve conversation '{conversation.id}' after update.")
            raise HTTPException(status_code=500, detail="Error retrieving conversation post-update.")
        return ConversationInDB(**updated_doc)
    except Exception as e:
        logger.error(f"DB error updating conversation '{conversation.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="DB error during conversation update.")

# --- API Endpoints ---
@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, summary="Start a new conversation")
async def start_new_conversation(
    request_body: ConversationCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user),
):
    logger.info(f"API: User '{current_user.id}' starting new conversation. Title: '{request_body.title}'.")
    try:
        persona_service = PersonaService(db)
    except ValueError as e: raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except RuntimeError as e: raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    user_message = Message(role="user", content=request_body.initial_message)
    conversation_id = str(uuid.uuid4())
    new_conv_data = ConversationInDB(
        _id=conversation_id, user_id=current_user.id, messages=[user_message],
        title=request_body.title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )
    try:
        ai_response_content = await persona_service.get_initial_response(user=current_user, first_message_content=user_message.content)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"API: Unhandled error getting initial AI response: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate initial AI response.")
    ai_message = Message(role="future_self", content=ai_response_content)
    new_conv_data.messages.append(ai_message)
    new_conv_data.updated_at = ai_message.timestamp
    created_conversation_in_db = await db_create_conversation(db, new_conv_data)
    return ConversationResponse(id=created_conversation_in_db.id, **created_conversation_in_db.model_dump(exclude={"id"}))

@router.post("/conversations/{conversation_id}/messages", response_model=ConversationResponse, summary="Send a message")
async def send_message_to_conversation(
    conversation_id: str, request_body: SendMessageRequest,
    db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user),
):
    logger.info(f"API: User '{current_user.id}' sending message to conversation '{conversation_id}'.")
    existing_conversation_in_db = await db_get_conversation(db, conversation_id, current_user.id)
    if not existing_conversation_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or access denied.")
    try: persona_service = PersonaService(db)
    except ValueError as e: raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except RuntimeError as e: raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    user_message = Message(role="user", content=request_body.content)
    existing_conversation_in_db.messages.append(user_message)
    try:
        ai_response_content = await persona_service.get_next_response(user=current_user, conversation_history=existing_conversation_in_db.messages)
    except HTTPException: raise
    except Exception as e:
        logger.error(f"API: Unhandled error getting next AI response for conv '{conversation_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate AI response.")
    ai_message = Message(role="future_self", content=ai_response_content)
    existing_conversation_in_db.messages.append(ai_message)
    updated_conversation_in_db = await db_update_conversation(db, existing_conversation_in_db)
    return ConversationResponse(id=updated_conversation_in_db.id, **updated_conversation_in_db.model_dump(exclude={"id"}))

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse, summary="Get a specific conversation")
async def get_conversation_details(
    conversation_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    conv_in_db = await db_get_conversation(db, conversation_id, current_user.id)
    if not conv_in_db: raise HTTPException(status_code=404, detail="Conversation not found or access denied.")
    return ConversationResponse(id=conv_in_db.id, **conv_in_db.model_dump(exclude={"id"}))

@router.get("/conversations", response_model=List[ConversationResponse], summary="List user's conversations")
async def list_conversations(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), # Query was missing import
    db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    logger.debug(f"Listing conversations for user '{current_user.id}', skip={skip}, limit={limit}")
    if not isinstance(db, AsyncIOMotorDatabase):
        logger.error("list_conversations: `db` is not AsyncIOMotorDatabase. Placeholder active.")
        return []
    try:
        conversations_collection: AsyncIOMotorCollection = db[CONVERSATIONS_COLLECTION_NAME]
        cursor = conversations_collection.find({"user_id": current_user.id}).sort("updated_at", -1).skip(skip).limit(limit)
        db_convs = await cursor.to_list(length=limit)
        response_list = [
            ConversationResponse(id=conv_doc["_id"], **{k:v for k,v in conv_doc.items() if k != "_id"}) 
            for conv_doc in db_convs
        ]
        return response_list
    except Exception as e:
        logger.error(f"DB error listing conversations for user '{current_user.id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving conversations.")