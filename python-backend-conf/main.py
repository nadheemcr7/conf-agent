from context import AirlineAgentContext
from context_utils import create_initial_context, load_user_context
from fastapi import FastAPI
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv
from agents import Agent, Runner
from schedule_agent_tools import get_conference_sessions, get_all_speakers, get_all_tracks, get_all_rooms
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Define input model for chat endpoint
class ChatRequest(BaseModel):
    message: str
    registration_id: str | None = None

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define agents with minimal instructions to avoid context length issues
conference_agent = Agent(
    name="ConferenceAgent",
    instructions="Help with Aviation Tech Summit 2025 conference queries. Use tools to get sessions, speakers, tracks, and rooms.",
    tools=[get_conference_sessions, get_all_speakers, get_all_tracks, get_all_rooms],
    model="groq/llama3-8b-8192"
)

triage_agent = Agent(
    name="TriageAgent", 
    instructions="Route conference queries to ConferenceAgent. For sessions, speakers, tracks, rooms use ConferenceAgent.",
    tools=[],
    model="groq/llama3-8b-8192"
)

async def create_context(registration_id: str | None = None) -> AirlineAgentContext:
    """Create context."""
    ctx = await create_initial_context()
    if registration_id:
        ctx.registration_id = str(registration_id)
    return ctx

# Initialize Runner
runner = Runner()

def route_request(message: str) -> Agent:
    """Route requests to appropriate agent."""
    message_lower = message.lower()
    conference_keywords = ["session", "speaker", "track", "room", "schedule", "conference"]
    
    if any(keyword in message_lower for keyword in conference_keywords):
        return conference_agent
    return triage_agent

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat requests."""
    try:
        logger.info(f"Processing message: {request.message}")
        
        # Handle empty messages
        if not request.message or not request.message.strip():
            return {
                "response": "Hello! I can help you with Aviation Tech Summit 2025. Ask me about sessions, speakers, tracks, or rooms.",
                "agent": "TriageAgent",
                "current_agent": "TriageAgent",
                "conversation_id": "initial",
                "context": {"registration_id": request.registration_id},
                "agents": [
                    {"name": "TriageAgent", "description": "Routes requests", "handoffs": ["ConferenceAgent"], "tools": [], "input_guardrails": []},
                    {"name": "ConferenceAgent", "description": "Conference queries", "handoffs": ["TriageAgent"], "tools": ["get_conference_sessions"], "input_guardrails": []}
                ],
                "events": [],
                "guardrails": [{"id": "1", "name": "relevance", "input": "", "reasoning": "OK", "passed": True, "timestamp": "2024-01-01T00:00:00Z"}],
                "customer_info": {
                    "customer": {"name": "Conference Attendee", "registration_id": request.registration_id, "is_conference_attendee": True, "conference_name": "Aviation Tech Summit 2025"},
                    "bookings": []
                }
            }
        
        # Create context
        ctx = await create_context(request.registration_id)
        
        # Route to agent
        selected_agent = route_request(request.message)
        logger.info(f"Using agent: {selected_agent.name}")
        
        # Get response from agent
        response = await runner.run(selected_agent, request.message, context=ctx)
        response_text = str(response) if response else "I'm sorry, I couldn't process that request."
        
        return {
            "response": response_text,
            "agent": selected_agent.name,
            "current_agent": selected_agent.name,
            "conversation_id": f"conv_{request.registration_id or 'default'}",
            "context": {"registration_id": ctx.registration_id},
            "agents": [
                {"name": "TriageAgent", "description": "Routes requests", "handoffs": ["ConferenceAgent"], "tools": [], "input_guardrails": []},
                {"name": "ConferenceAgent", "description": "Conference queries", "handoffs": ["TriageAgent"], "tools": ["get_conference_sessions", "get_all_speakers", "get_all_tracks", "get_all_rooms"], "input_guardrails": []}
            ],
            "events": [
                {"id": "1", "type": "message", "agent": selected_agent.name, "content": f"Processed: {request.message[:30]}...", "timestamp": "2024-01-01T00:00:00Z", "metadata": {}}
            ],
            "guardrails": [
                {"id": "1", "name": "relevance", "input": request.message, "reasoning": "Message is relevant", "passed": True, "timestamp": "2024-01-01T00:00:00Z"}
            ],
            "customer_info": {
                "customer": {"name": "Conference Attendee", "registration_id": ctx.registration_id, "is_conference_attendee": True, "conference_name": "Aviation Tech Summit 2025"},
                "bookings": []
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {
            "response": "I'm sorry, there was an error. Please try again.",
            "agent": "System",
            "current_agent": "System", 
            "conversation_id": "error",
            "context": {},
            "agents": [],
            "events": [],
            "guardrails": [],
            "customer_info": None
        }

@app.get("/user/{user_id}")
async def get_user(user_id: str):
    """Get user by registration ID."""
    try:
        from database import db_client
        
        response = db_client.table("users").select("id, details").filter("details->>registration_id", "eq", str(user_id)).execute()
        
        if response.data:
            user = response.data[0]
            return {
                "user_id": user["id"],
                "registration_id": str(user_id),
                "status": "found",
                "details": user["details"]
            }
        else:
            return {"error": "User not found"}, 404
            
    except Exception as e:
        logger.error(f"Error in /user/{user_id}: {e}", exc_info=True)
        return {"error": "Internal server error"}, 500