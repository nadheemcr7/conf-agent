from __future__ import annotations as _annotations
import logging
from typing import Optional, List, Dict, Any
from context import AirlineAgentContext
from database import db_client
from agents import (
    Agent,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    function_tool,
    handoff,
    GuardrailFunctionOutput,
    input_guardrail,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Import tools
from common_tools import get_booking_details
from seat_booking_agent_tools import update_seat, display_seat_map
from flight_status_agent_tools import flight_status_tool
from cancellation_agent_tools import cancel_flight
from faq_agent_tools import faq_lookup_tool
from schedule_agent_tools import get_conference_sessions, get_all_speakers, get_all_tracks, get_all_rooms
from networking_agent_tools import search_businesses, get_user_businesses, display_business_form, add_business

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Placeholder guardrail implementations (replace with actual ones)
@input_guardrail
async def relevance_guardrail(input: TResponseInputItem) -> GuardrailFunctionOutput:
    """Check if the input is relevant to airline or conference queries."""
    logger.debug(f"Applying relevance guardrail to input: {input.content}")
    relevant_keywords = [
        "flight", "seat", "booking", "cancel", "status", "baggage", "luggage",
        "conference", "session", "speaker", "track", "room", "networking", "business"
    ]
    is_relevant = any(keyword in input.content.lower() for keyword in relevant_keywords)
    if is_relevant:
        return GuardrailFunctionOutput(should_proceed=True)
    return GuardrailFunctionOutput(
        should_proceed=False,
        message="I can only assist with airline-related or Aviation Tech Summit 2025 queries. Please ask about flights, bookings, or conference details."
    )

@input_guardrail
async def jailbreak_guardrail(input: TResponseInputItem) -> GuardrailFunctionOutput:
    """Check for attempts to bypass system instructions."""
    logger.debug(f"Applying jailbreak guardrail to input: {input.content}")
    suspicious_phrases = ["ignore instructions", "bypass", "system prompt", "hack"]
    if any(phrase in input.content.lower() for phrase in suspicious_phrases):
        return GuardrailFunctionOutput(
            should_proceed=False,
            message="I'm sorry, but I can't process that request. Please ask a valid question about airline services or the Aviation Tech Summit 2025."
        )
    return GuardrailFunctionOutput(should_proceed=True)

# Agent instructions (replace with your actual instructions)
def seat_booking_instructions() -> str:
    return (
        "You are the Seat Booking Agent. Your role is to assist users with changing seats or viewing seat maps for their bookings. "
        "Use the provided tools to update seats or display the seat map. "
        "Always verify the confirmation number and ensure the user is authorized. "
        "If the query is unrelated to seat changes, hand off to the Triage Agent."
    )

def flight_status_instructions() -> str:
    return (
        "You are the Flight Status Agent. Your role is to provide real-time flight status information, including delays, gate assignments, and departure times. "
        "Use the flight status tool or booking details tool as needed. "
        "If the query is unrelated to flight status, hand off to the Triage Agent."
    )

def cancellation_instructions() -> str:
    return (
        "You are the Cancellation Agent. Your role is to assist users with cancelling their flight bookings. "
        "Use the cancel flight tool after verifying booking details. "
        "Ensure the confirmation number is valid and the user is authorized. "
        "If the query is unrelated to cancellations, hand off to the Triage Agent."
    )

def faq_instructions() -> str:
    return (
        "You are the FAQ Agent. Your role is to answer general questions about airline policies, services, and aircraft details. "
        "Use the FAQ lookup tool to provide accurate information. "
        "If the query is specific to bookings or conference details, hand off to the Triage Agent."
    )

def schedule_instructions() -> str:
    return (
        "You are the Schedule Agent for the Aviation Tech Summit 2025. Your role is to provide detailed conference schedule information, including sessions, speakers, tracks, and rooms. "
        "Use the provided tools to retrieve and format schedule data. "
        "If the query is unrelated to the conference, hand off to the Triage Agent."
    )

def networking_instructions() -> str:
    return (
        "You are the Networking Agent for the Aviation Tech Summit 2025. Your role is to facilitate business networking by searching for businesses, retrieving user business profiles, or adding new businesses. "
        "Use the provided tools to manage business data. "
        "If the query is unrelated to networking, hand off to the Triage Agent."
    )

def triage_instructions() -> str:
    return (
        "You are the Triage Agent for an airline customer service and Aviation Tech Summit 2025 chatbot. "
        "Your role is to route user queries to the appropriate specialist agent based on keywords. "
        "Do not answer questions directly unless they are greetings or simple queries. "
        "Use the following routing logic:\n"
        "- 'seat', 'change seat', 'seat map' → Seat Booking Agent\n"
        "- 'flight status', 'delay', 'gate' → Flight Status Agent\n"
        "- 'cancel', 'cancellation' → Cancellation Agent\n"
        "- 'baggage', 'luggage', 'policy', 'aircraft' → FAQ Agent\n"
        "- 'conference', 'session', 'speaker', 'track', 'room' → Schedule Agent\n"
        "- 'business', 'networking', 'company' → Networking Agent\n"
        "If the query is unclear or unrelated, respond with a clarification request or a general response. "
        "Always check guardrails before proceeding."
    )

# Define specialist agents first
seat_booking_agent = Agent[AirlineAgentContext](
    name="Seat Booking Agent",
    model="grok/llama3-8b-8192",
    handoff_description="A specialist agent for seat changes and seat map viewing.",
    instructions=seat_booking_instructions,
    tools=[update_seat, display_seat_map, get_booking_details],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
    handoffs=[None],  # Will update with triage_agent after its definition
)

flight_status_agent = Agent[AirlineAgentContext](
    name="Flight Status Agent",
    model="grok/llama3-8b-8192",
    handoff_description="A specialist agent for real-time flight status and departure information.",
    instructions=flight_status_instructions,
    tools=[flight_status_tool, get_booking_details],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
    handoffs=[None],  # Will update with triage_agent after its definition
)

cancellation_agent = Agent[AirlineAgentContext](
    name="Cancellation Agent",
    model="grok/llama3-8b-8192",
    handoff_description="A specialist agent for cancelling flight bookings.",
    instructions=cancellation_instructions,
    tools=[cancel_flight, get_booking_details],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
    handoffs=[None],  # Will update with triage_agent after its definition
)

faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    model="grok/llama3-8b-8192",
    handoff_description="A specialist agent for answering frequently asked questions about airline services.",
    instructions=faq_instructions,
    tools=[faq_lookup_tool],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
    handoffs=[None],  # Will update with triage_agent after its definition
)

schedule_agent = Agent[AirlineAgentContext](
    name="Schedule Agent",
    model="grok/llama3-8b-8192",
    handoff_description="A specialist agent for conference schedule information.",
    instructions=schedule_instructions,
    tools=[get_conference_sessions, get_all_speakers, get_all_tracks, get_all_rooms],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
    handoffs=[None],  # Will update with triage_agent after its definition
)

networking_agent = Agent[AirlineAgentContext](
    name="Networking Agent",
    model="grok/llama3-8b-8192",
    handoff_description="A specialist agent for business networking and company information.",
    instructions=networking_instructions,
    tools=[search_businesses, get_user_businesses, display_business_form, add_business],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
    handoffs=[None],  # Will update with triage_agent after its definition
)

# Define triage agent after specialist agents
triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    model="grok/llama3-8b-8192",
    instructions=triage_instructions,
    tools=[],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
    handoffs=[
        seat_booking_agent,
        flight_status_agent,
        cancellation_agent,
        faq_agent,
        schedule_agent,
        networking_agent
    ],
)

# Update specialist agents' handoffs to include triage_agent
seat_booking_agent.handoffs = [triage_agent]
flight_status_agent.handoffs = [triage_agent]
cancellation_agent.handoffs = [triage_agent]
faq_agent.handoffs = [triage_agent]
schedule_agent.handoffs = [triage_agent]
networking_agent.handoffs = [triage_agent]

# Context creation function
async def create_context() -> AirlineAgentContext:
    """Create and initialize the AirlineAgentContext."""
    context = AirlineAgentContext()
    logger.info("Created new AirlineAgentContext")
    return context

# Runner setup
runner = Runner(  # Removed [AirlineAgentContext] to fix previous TypeError
    default_agent=triage_agent,
    context_factory=create_context,
)

# Main entry point
async def main():
    """Main entry point for the chatbot."""
    logger.info("Starting chatbot runner")
    try:
        await runner.run()
    except Exception as e:
        logger.error(f"Runner failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())