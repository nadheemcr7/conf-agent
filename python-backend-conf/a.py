from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import List, Dict, Any, Optional
from context import AirlineAgentContext
from main import (
    triage_agent,
    seat_booking_agent,
    flight_status_agent,
    cancellation_agent,
    faq_agent,
    schedule_agent,
    networking_agent,
    runner
)
from agents import FunctionTool

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    registration_id: Optional[str] = None
    confirmation_number: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent: str
    context: Dict[str, Any]

async def get_context(request: ChatRequest) -> AirlineAgentContext:
    """Create or retrieve context for the chat request."""
    context = AirlineAgentContext(
        user_id=request.user_id,
        registration_id=request.registration_id,
        confirmation_number=request.confirmation_number
    )
    logger.info(f"Created context for user_id: {request.user_id}")
    return context

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, context: AirlineAgentContext = Depends(get_context)):
    """Handle chat requests and route to appropriate agent."""
    try:
        logger.info(f"Received chat request: {request.message}")
        # Create a response input item (adjust based on your agents module)
        input_item = {"content": request.message, "role": "user"}

        # Run the agent through the runner
        response = await runner.run(
            input_item=input_item,
            context=context,
            agent=triage_agent  # Start with triage agent
        )

        # Handle tool responses (e.g., DISPLAY_SEAT_MAP, DISPLAY_BUSINESS_FORM)
        if isinstance(response, dict) and "tool_call" in response:
            tool_name = response.get("tool_call", {}).get("name")
            if tool_name in ["display_seat_map", "display_business_form"]:
                return JSONResponse(
                    content={
                        "response": response.get("output", ""),
                        "agent": response.get("agent_name", "Unknown"),
                        "context": context.dict(),
                        "tool_trigger": tool_name
                    }
                )

        # Handle FunctionTool responses
        if isinstance(response, FunctionTool):
            tool_response = await response.invoke(context)
            return JSONResponse(
                content={
                    "response": tool_response,
                    "agent": response.__class__.__name__,
                    "context": context.dict()
                }
            )

        # Standard response
        return ChatResponse(
            response=response.get("output", "I'm sorry, I couldn't process your request."),
            agent=response.get("agent_name", "Triage Agent"),
            context=context.dict()
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)