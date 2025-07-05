# from fastapi import FastAPI, HTTPException, Depends, Request
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from dotenv import load_dotenv
# import logging
# from typing import List, Dict, Any, Optional
# from context import AirlineAgentContext
# from context_utils import create_initial_context, load_user_context, load_customer_context
# from main import (
#     triage_agent,
#     seat_booking_agent,
#     flight_status_agent,
#     cancellation_agent,
#     faq_agent,
#     schedule_agent,
#     networking_agent,
#     runner
# )
# from agents import FunctionTool

# # Load environment variables
# load_dotenv()

# # Configure logging
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# app = FastAPI()

# class ChatRequest(BaseModel):
#     message: str
#     user_id: Optional[str] = None
#     registration_id: Optional[str] = None
#     confirmation_number: Optional[str] = None
#     account_number: Optional[str] = None  # Added to support customer context

# class ChatResponse(BaseModel):
#     response: str
#     agent: str
#     context: Dict[str, Any]
#     tool_trigger: Optional[str] = None

# async def get_context(request: ChatRequest) -> AirlineAgentContext:
#     """Create or retrieve context for the chat request."""
#     try:
#         logger.debug(f"🔍 Creating context for user_id: {request.user_id}, registration_id: {request.registration_id}, account_number: {request.account_number}, confirmation_number: {request.confirmation_number}")
        
#         # Load context based on available identifiers
#         if request.registration_id:
#             context = await load_user_context(request.registration_id)
#         elif request.account_number:
#             context = await load_customer_context(request.account_number)
#         else:
#             context = create_initial_context()
        
#         # Set user_id and confirmation_number if provided
#         if request.user_id:
#             context.user_id = request.user_id
#         if request.confirmation_number:
#             context.confirmation_number = request.confirmation_number
        
#         logger.info(f"✅ Created context for user_id: {context.user_id}")
#         return context
#     except Exception as e:
#         logger.error(f"❌ Error creating context: {e}", exc_info=True)
#         return create_initial_context()  # Fallback to empty context

# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(request: ChatRequest, context: AirlineAgentContext = Depends(get_context)):
#     """Handle chat requests and route to appropriate agent."""
#     try:
#         logger.info(f"Received chat request: {request.message}")
#         input_item = {"content": request.message, "role": "user"}

#         response = await runner.run(
#             input_item=input_item,
#             context=context,
#             agent=triage_agent
#         )

#         if isinstance(response, dict) and "tool_call" in response:
#             tool_name = response.get("tool_call", {}).get("name")
#             logger.debug(f"Tool call detected: {tool_name}")
#             if tool_name in ["display_seat_map", "display_business_form"]:
#                 return JSONResponse(
#                     content={
#                         "response": response.get("output", ""),
#                         "agent": response.get("agent_name", "Unknown"),
#                         "context": context.dict(),
#                         "tool_trigger": tool_name
#                     }
#                 )

#         if isinstance(response, FunctionTool):
#             logger.debug(f"Invoking FunctionTool: {response.__class__.__name__}")
#             tool_response = await response.invoke(context)
#             return JSONResponse(
#                 content={
#                     "response": tool_response,
#                     "agent": response.__class__.__name__,
#                     "context": context.dict(),
#                     "tool_trigger": None
#                 }
#             )

#         output = response.get("output", "I'm sorry, I couldn't process your request.")
#         agent_name = response.get("agent_name", "Triage Agent")
#         logger.info(f"Returning response from {agent_name}: {output[:100]}...")
#         return ChatResponse(
#             response=output,
#             agent=agent_name,
#             context=context.dict(),
#             tool_trigger=None
#         )
#     except Exception as e:
#         logger.error(f"Error processing chat request: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# @app.get("/health")
# async def health_check():
#     """Health check endpoint."""
#     logger.info("Health check requested")
#     return {"status": "healthy"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)










from fastapi import FastAPI
from main import (
    app,
    ChatRequest,
    create_context,
    conference_agent,
    triage_agent,
    route_request,
    runner
)

# Note: The app is already defined in main.py, so no additional routes are needed here
# This file primarily serves to import and run the FastAPI app