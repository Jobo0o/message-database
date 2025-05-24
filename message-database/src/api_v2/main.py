from fastapi import FastAPI
from contextlib import asynccontextmanager
from ..database.mongodb import db  # Updated import path
from ..utils.logger import logger # Assuming logger is used in db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("API starting up...")
    if not db.connected:
        db.connect()
    yield
    # Shutdown
    logger.info("API shutting down...")
    if db.connected:
        db.disconnect()

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import Path, Query, HTTPException # Added Path
import os

API_V2_DESCRIPTION = """
The Message API V2 provides read-only access to the message database.
It allows users to list messages with pagination and retrieve individual messages by their ID.
The API also serves a simple frontend for interacting with these messages.
"""

app = FastAPI(
    title="Message API V2",
    version="0.1.0",
    lifespan=lifespan,
    description=API_V2_DESCRIPTION,
    openapi_tags=[  # Optional: Define tags for better organization in docs
        {"name": "Messages", "description": "Operations to read messages."},
        {"name": "Frontend", "description": "Access to the web UI."},
    ]
)

# Determine the correct path to the frontend directory
# main.py is in message-database/src/api_v2/
# frontend is in message-database/frontend/
# So, the relative path from main.py to frontend is ../../frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "../../frontend")

# Mount static files for CSS and JS first, using a specific path to avoid conflicts
app.mount("/ui/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="frontend-css")
app.mount("/ui/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="frontend-js")

from typing import List, Optional
from fastapi import HTTPException, Query
from ..models.message import Message  # Updated import path
from bson import ObjectId # For converting string ID to ObjectId for MongoDB
from pymongo.errors import PyMongoError

@app.get(
    "/",
    summary="Root Endpoint",
    description="Provides a welcome message for API V2.",
    tags=["Messages"] # Assigning to a tag
)
async def read_root():
    return {"message": "Welcome to Message API V2"}

@app.get(
    "/messages",
    response_model=List[Message],
    summary="List All Messages",
    description="Retrieves a list of messages from the database with pagination support. "
                "Messages are returned in the order they are stored, which is typically by insertion time.",
    tags=["Messages"],
    responses={
        200: {"description": "A list of messages."},
        500: {"description": "Internal server error while fetching messages."},
        503: {"description": "Database not connected."},
    }
)
async def list_messages(
    skip: int = Query(0, ge=0, description="Number of messages to skip from the beginning."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of messages to return.")
):
    if not db.connected:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        messages_cursor = db.collection.find().skip(skip).limit(limit)
        # Ensure _id (ObjectId) is converted to string if your Pydantic model expects str for an id field
        # and if your Message model doesn't handle ObjectId conversion for _id.
        # For this example, we assume Message model handles data types correctly.
        messages = [Message(**msg) for msg in messages_cursor]
        return messages
    except PyMongoError as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Error fetching messages from database")

@app.get(
    "/messages/{message_id}",
    response_model=Message,
    summary="Get a Specific Message",
    description="Retrieves a single message by its unique `message_id`. "
                "The `message_id` is a string identifier specific to each message.",
    tags=["Messages"],
    responses={
        200: {"description": "The requested message."},
        404: {"description": "Message with the specified ID was not found."},
        500: {"description": "Internal server error while fetching the message."},
        503: {"description": "Database not connected."},
    }
)
async def get_message(
    message_id: str = Path(..., description="The unique identifier of the message to retrieve.")
):
    if not db.connected:
        raise HTTPException(status_code=503, detail="Database not connected")
    try:
        # Assuming 'message_id' is a string field in your documents, not the MongoDB '_id'.
        # Assuming 'message_id' is a string field in your documents, not the MongoDB '_id'.
        # If 'message_id' is meant to be the document's primary key '_id',
        # then it might need conversion to ObjectId if stored as such:
        # from bson import ObjectId
        # message_doc = db.collection.find_one({"_id": ObjectId(message_id)})
        # For this implementation, we assume 'message_id' is a direct queryable string field.
        message_doc = db.collection.find_one({"message_id": message_id})
        if message_doc:
            return Message(**message_doc)
        else:
            raise HTTPException(status_code=404, detail=f"Message with ID '{message_id}' not found")
    except PyMongoError as e:
        logger.error(f"Error fetching message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching message {message_id} from database")

# Serve index.html at /ui and /ui/
@app.get(
    "/ui/{path:path}",
    include_in_schema=False, # Exclude from OpenAPI schema as it's for serving files
    tags=["Frontend"]
)
@app.get(
    "/ui/",
    include_in_schema=False, # Exclude from OpenAPI schema
    summary="Serve Frontend Application",
    description="Serves the main HTML page of the frontend application. "
                "CSS and JS are served by separate static mounts.",
    tags=["Frontend"]
)
async def serve_frontend_index(path: Optional[str] = Path(None, description="Path to a frontend asset (not typically used directly).")):
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return HTMLResponse(content=open(index_path).read(), media_type="text/html")
    raise HTTPException(status_code=404, detail="Frontend index.html not found")

# Further endpoints will be added here.
# Note on _id vs message_id: The current implementation queries by "message_id".
# If "message_id" is meant to be MongoDB's primary key "_id", then Pydantic models
# might need alias for "_id" (e.g., `id: str = Field(..., alias='_id')`) and
# queries might need `ObjectId(message_id)`. The current code assumes "message_id"
# is a distinct, queryable string field.
