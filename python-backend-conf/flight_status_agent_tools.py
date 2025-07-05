from typing import Dict, Any
import logging
from context import AirlineAgentContext
from database import db_client
from agents import function_tool

logger = logging.getLogger(__name__)

@function_tool(
    name_override="flight_status_tool",
    description_override="Get flight status information."
)
async def flight_status_tool(flight_number: str, context: AirlineAgentContext) -> str:
    """Get flight status information."""
    try:
        flight = await db_client.query(
            table_name="flights",
            filters={"flight_number": flight_number},
            single=True
        )
        if not flight:
            logger.warning(f"❌ No flight found for flight_number: {flight_number}")
            return f"No flight found for flight number {flight_number}"
        logger.info(f"✅ Found flight status for {flight_number}")
        return (
            f"Flight {flight_number} Status:\n"
            f"Status: {flight.get('current_status')}\n"
            f"Gate: {flight.get('gate')}\n"
            f"Terminal: {flight.get('terminal')}\n"
            f"Delay: {flight.get('delay_minutes', 0)} minutes"
        )
    except Exception as e:
        logger.error(f"❌ Error fetching flight status: {e}", exc_info=True)
        return f"Error fetching flight status: {str(e)}"