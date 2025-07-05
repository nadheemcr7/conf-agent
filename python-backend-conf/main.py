from context import AirlineAgentContext
from context_utils import create_initial_context, load_user_context, load_customer_context
from fastapi import FastAPI
from pydantic import BaseModel
import logging
import os
from agents import Agent, Runner, function_tool
from common_tools import get_booking_details
from cancellation_agent_tools import cancel_flight
from seat_booking_agent_tools import update_seat, display_seat_map
from flight_status_agent_tools import flight_status_tool
from schedule_agent_tools import get_conference_sessions, get_all_speakers, get_all_tracks, get_all_rooms
from networking_agent_tools import search_businesses, get_user_businesses, display_business_form, add_business
from semantic_mappings import SEMANTIC_MAPPINGS
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["*"],  # Adjust to specific origins (e.g., ["http://localhost:3000"]) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define agent tools
# CUSTOMER_SERVICE_TOOLS = [
#     get_booking_details,
#     cancel_flight,
#     update_seat,
#     display_seat_map,
#     flight_status_tool,
# ]

CONFERENCE_TOOLS = [
    get_conference_sessions,
    get_all_speakers,
    get_all_tracks,
    get_all_rooms,
]

# NETWORKING_TOOLS = [
#     search_businesses,
#     get_user_businesses,
#     display_business_form,
#     add_business,
# ]

# Define agents
# customer_service_agent = Agent(
#     name="CustomerServiceAgent",
#     instructions=(
#         "You are a customer service agent for an airline. Your role is to assist users with flight-related requests, "
#         "such as retrieving booking details, canceling flights, updating seats, or checking flight status. Always verify "
#         "user information using the provided context (e.g., confirmation_number, account_number). If the user provides "
#         "insufficient information, request clarification. Use the provided tools to fetch or update data and respond in a "
#         "professional, concise manner."
#     ),
#     tools=CUSTOMER_SERVICE_TOOLS,
#     model="groq/llama3-8b-8192"
# )

conference_agent = Agent(
    name="ConferenceAgent",
    instructions=(
        "You are a conference assistant for the Aviation Tech Summit 2025. Your role is to help users find conference sessions, "
        "speakers, tracks, or rooms based on their queries. Use the registration_id from the context to personalize responses. "
        "If the user is not registered, suggest registration. Use the provided tools to fetch data and respond clearly."
    ),
    tools=CONFERENCE_TOOLS,
    model="groq/llama3-8b-8192"
)

# networking_agent = Agent(
#     name="NetworkingAgent",
#     instructions=(
#         "You are a networking assistant for the Aviation Tech Summit 2025. Your role is to help users find businesses, "
#         "manage their business profiles, or register new businesses. Use the user_id and organization_id from the context "
#         "to personalize responses. If the user provides business details, validate and process them using the provided tools. "
#         "Respond professionally and concisely."
#     ),
#     tools=NETWORKING_TOOLS,
#     model="groq/llama3-8b-8192"
# )

triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "You are a triage agent that routes user requests to the appropriate specialized agent. Analyze the user's message "
        "and context to determine the intent. Use semantic mappings to identify relevant keywords or phrases. Route to:"
        # "- CustomerServiceAgent for flight-related requests (e.g., booking, cancellation, seat changes, flight status)."
        "- ConferenceAgent for conference-related requests (e.g., sessions, speakers, tracks, rooms)."
        # "- NetworkingAgent for business or networking-related requests (e.g., business search, profile management)."
        "If the intent is unclear, ask for clarification. Do not execute tools directly; delegate to the appropriate agent."
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
    logger.debug(f"Creating context with confirmation_number={confirmation_number}, "
                 f"account_number={account_number}, registration_id={registration_id}, "
                 f"user_id={user_id}, organization_id={organization_id}")
    
    ctx = await create_initial_context()
    
    # Load user context if registration_id is provided
    if registration_id:
        ctx = await load_user_context(registration_id)
    
    # Load customer context if account_number is provided
    if account_number:
        ctx = await load_customer_context(account_number)
    
    # Update context with additional fields
    if confirmation_number:
        ctx.confirmation_number = confirmation_number
    if user_id:
        ctx.user_id = user_id
    if organization_id:
        ctx.organization_id = organization_id
    
    logger.info(f"Context created: {ctx}")
    return ctx

# Initialize Runner without arguments
runner = Runner()

# Define semantic routing logic
def route_request(message: str, ctx: AirlineAgentContext) -> Agent:
    """Route the request to the appropriate agent based on the message content."""
    message_lower = message.lower()
    
    for intent, mappings in SEMANTIC_MAPPINGS.items():
        for keyword in mappings.get("keywords", []):
            if keyword.lower() in message_lower:
                logger.debug(f"Matched intent '{intent}' with keyword '{keyword}'")
                # if intent == "customer_service":
                #     return customer_service_agent
                if intent == "conference":
                    return conference_agent
                # elif intent == "networking":
                #     return networking_agent
    
    logger.debug("No specific intent matched, defaulting to triage_agent")
    return triage_agent

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle user chat requests and route to appropriate agent."""
    try:
        logger.debug(f"Received chat request: {request}")
        
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
        
        logger.info(f"Agent response: {response}")
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return {"error": str(e)}, 500

# Updated: User endpoint to fetch user based on registration_id in details column
@app.get("/user/{user_id}")
async def get_user(user_id: str):
    logger.debug(f"Received request for user_id: {user_id}")
    ctx = await create_initial_context()  # Start with initial context

    from database import db_client  # Import db_client here or at the top level
    try:
        logger.debug(f"Attempting to query Supabase for user_id: {user_id}")
        response = db_client.table("users").select("id, details").filter("details->>registration_id", "eq", str(user_id)).execute()
        users = response.data
        logger.debug(f"Supabase raw response data: {users}")

        if users:
            user = users[0]
            logger.debug(f"Found user: {user}")
            registration_id = user["details"].get("registration_id")
            logger.debug(f"Extracted registration_id: {registration_id}")

            if registration_id is not None:
                registration_id_str = str(registration_id)
                logger.debug(f"Calling load_user_context with registration_id_str: {registration_id_str}")
                try:
                    ctx = await load_user_context(registration_id_str)
                    logger.debug(f"load_user_context completed. ctx.user_id: {ctx.user_id}")
                    if ctx.user_id:
                        return {"user_id": user["id"], "registration_id": registration_id_str, "status": "found", "details": user["details"]}
                    else:
                        logger.warning(f"load_user_context did not set user_id in context for registration_id: {registration_id_str}")
                        return {"error": "User context could not be loaded fully"}, 404
                except Exception as load_err:
                    logger.error(f"Error within load_user_context for registration_id {registration_id_str}: {load_err}", exc_info=True)
                    return {"error": "Failed to load user context"}, 500
            else:
                logger.warning(f"Registration ID is missing in user details for user: {user['id']}")
                return {"error": "User found but registration_id missing in details"}, 404
        else:
            logger.info(f"No user found for registration_id: {user_id}")
            return {"error": "User not found or registration_id missing"}, 404
    except Exception as e:
        logger.error(f"Error querying Supabase or general error in /user/{user_id} endpoint: {e}", exc_info=True)
        return {"error": "Internal server error"}, 500