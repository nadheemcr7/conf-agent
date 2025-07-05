from context import AirlineAgentContext, BusinessDetails
from context_utils import create_initial_context, load_user_context, load_customer_context
from fastapi import FastAPI
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv
from agents import Agent, Runner
from schedule_agent_tools import get_conference_sessions, get_all_speakers, get_all_tracks, get_all_rooms
from semantic_mappings import SEMANTIC_MAPPINGS
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Define input model for chat endpoint
class ChatRequest(BaseModel):
    message: str
    confirmation_number: str | None = None
    account_number: str | None = None
    registration_id: str | None = None
    user_id: str | None = None
    business_details: dict | None = None
    organization_id: str | None = None

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

# Define agent tools
CONFERENCE_TOOLS = [
    get_conference_sessions,
    get_all_speakers,
    get_all_tracks,
    get_all_rooms,
]

# Define agents with shorter instructions to avoid context length issues
conference_agent = Agent(
    name="ConferenceAgent",
    instructions=(
        "You are a conference assistant for Aviation Tech Summit 2025. "
        "Help users find sessions, speakers, tracks, and rooms. "
        "Use tools to fetch data and respond clearly with organized information."
    ),
    tools=CONFERENCE_TOOLS,
    model="groq/llama3-8b-8192"
)

triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "Route user requests to appropriate agents. "
        "For conference queries (sessions, speakers, tracks, rooms), use ConferenceAgent. "
        "If unclear, ask for clarification."
    ),
    tools=[],
    model="groq/llama3-8b-8192"
)

async def create_context(
    confirmation_number: str | None = None,
    account_number: str | None = None,
    registration_id: str | None = None,
    user_id: str | None = None,
    business_details: dict | None = None,
    organization_id: str | None = None,
) -> AirlineAgentContext:
    """Create and populate an AirlineAgentContext based on provided identifiers."""
    logger.debug(f"Creating context with registration_id={registration_id}")
    
    ctx = await create_initial_context()
    
    # Load user context if registration_id is provided
    if registration_id:
        try:
            ctx = await load_user_context(str(registration_id))
        except Exception as e:
            logger.warning(f"Failed to load user context: {e}")
    
    # Update context with additional fields
    if confirmation_number:
        ctx.confirmation_number = str(confirmation_number)
    if user_id:
        ctx.user_id = str(user_id)
    if organization_id:
        ctx.organization_id = str(organization_id)
    if registration_id:
        ctx.registration_id = str(registration_id)
    
    logger.info(f"Context created successfully")
    return ctx

# Initialize Runner
runner = Runner()

# Define semantic routing logic
def route_request(message: str, ctx: AirlineAgentContext) -> Agent:
    """Route the request to the appropriate agent based on the message content."""
    message_lower = message.lower()
    
    # Check for conference-related keywords
    conference_keywords = ["session", "speaker", "track", "room", "schedule", "conference", "summit", "aviation"]
    if any(keyword in message_lower for keyword in conference_keywords):
        logger.debug("Routing to ConferenceAgent")
        return conference_agent
    
    logger.debug("Routing to TriageAgent")
    return triage_agent

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle user chat requests and route to appropriate agent."""
    try:
        logger.debug(f"Received chat request: {request.message}")
        
        # Validate message is not empty
        if not request.message or not request.message.strip():
            return {
                "response": "Please enter a message to get started. I can help you with Aviation Tech Summit 2025 conference information!",
                "agent": "TriageAgent",
                "current_agent": "TriageAgent",
                "conversation_id": "initial",
                "context": {},
                "agents": [
                    {
                        "name": "TriageAgent",
                        "description": "Routes requests to appropriate agents",
                        "handoffs": ["ConferenceAgent"],
                        "tools": [],
                        "input_guardrails": []
                    },
                    {
                        "name": "ConferenceAgent", 
                        "description": "Handles conference-related queries",
                        "handoffs": ["TriageAgent"],
                        "tools": ["get_conference_sessions", "get_all_speakers", "get_all_tracks", "get_all_rooms"],
                        "input_guardrails": []
                    }
                ],
                "events": [],
                "guardrails": [],
                "customer_info": {
                    "customer": {
                        "name": "Conference Attendee",
                        "registration_id": request.registration_id,
                        "is_conference_attendee": True,
                        "conference_name": "Aviation Tech Summit 2025"
                    },
                    "bookings": []
                }
            }
        
        # Create context
        ctx = await create_context(
            confirmation_number=request.confirmation_number,
            account_number=request.account_number,
            registration_id=request.registration_id,
            user_id=request.user_id,
            business_details=request.business_details,
            organization_id=request.organization_id,
        )
        
        # Route to appropriate agent
        selected_agent = route_request(request.message, ctx)
        logger.info(f"Routed to agent: {selected_agent.name}")
        
        # Execute the agent using Runner
        response = await runner.run(selected_agent, request.message, context=ctx)
        
        logger.info(f"Agent response received")
        
        # Format response properly
        response_text = response if isinstance(response, str) else str(response)
        
        return {
            "response": response_text,
            "agent": selected_agent.name,
            "current_agent": selected_agent.name,
            "conversation_id": f"conv_{request.registration_id or 'default'}",
            "context": {
                "registration_id": ctx.registration_id,
                "user_id": ctx.user_id,
                "passenger_name": getattr(ctx, 'passenger_name', None),
                "customer_email": getattr(ctx, 'customer_email', None)
            },
            "agents": [
                {
                    "name": "TriageAgent",
                    "description": "Routes requests to appropriate agents",
                    "handoffs": ["ConferenceAgent"],
                    "tools": [],
                    "input_guardrails": []
                },
                {
                    "name": "ConferenceAgent", 
                    "description": "Handles conference-related queries",
                    "handoffs": ["TriageAgent"],
                    "tools": ["get_conference_sessions", "get_all_speakers", "get_all_tracks", "get_all_rooms"],
                    "input_guardrails": []
                }
            ],
            "events": [
                {
                    "id": f"event_{len(response_text)}",
                    "type": "message",
                    "agent": selected_agent.name,
                    "content": f"Processed request: {request.message[:50]}...",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "metadata": {}
                }
            ],
            "guardrails": [
                {
                    "id": "relevance_check",
                    "name": "relevance_guardrail",
                    "input": request.message,
                    "reasoning": "Message is relevant to conference queries",
                    "passed": True,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ],
            "customer_info": {
                "customer": {
                    "name": getattr(ctx, 'passenger_name', None) or "Conference Attendee",
                    "registration_id": ctx.registration_id,
                    "email": getattr(ctx, 'customer_email', None),
                    "is_conference_attendee": True,
                    "conference_name": "Aviation Tech Summit 2025"
                },
                "bookings": []
            }
        }
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return {
            "error": str(e),
            "response": "I'm sorry, there was an error processing your request. Please try again.",
            "agent": "System",
            "current_agent": "System",
            "conversation_id": "error",
            "context": {},
            "agents": [],
            "events": [],
            "guardrails": [],
            "customer_info": None
        }

# User endpoint
@app.get("/user/{user_id}")
async def get_user(user_id: str):
    logger.debug(f"Received request for user_id: {user_id}")
    
    from database import db_client
    try:
        logger.debug(f"Querying Supabase for user_id: {user_id}")
        response = db_client.table("users").select("id, details").filter("details->>registration_id", "eq", str(user_id)).execute()
        users = response.data
        logger.debug(f"Supabase response: {users}")

        if users:
            user = users[0]
            registration_id = user["details"].get("registration_id")
            
            if registration_id is not None:
                return {
                    "user_id": user["id"], 
                    "registration_id": str(registration_id), 
                    "status": "found", 
                    "details": user["details"]
                }
            else:
                return {"error": "Registration ID missing in details"}, 404
        else:
            return {"error": "User not found"}, 404
    except Exception as e:
        logger.error(f"Error in /user/{user_id} endpoint: {e}", exc_info=True)
        return {"error": "Internal server error"}, 500