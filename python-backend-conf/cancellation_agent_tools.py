from typing import Dict, Any
import logging
from context import AirlineAgentContext
from database import db_client
from agents import function_tool

logger = logging.getLogger(__name__)

@function_tool(
    name_override="cancel_flight",
    description_override="Cancel a flight booking and update the booking status."
)
async def cancel_flight(confirmation_number: str, context: AirlineAgentContext) -> str:
    """Cancel a flight booking and update the booking status."""
    try:
        booking = await db_client.query(
            table_name="bookings",
            filters={"confirmation_number": confirmation_number},
            single=True
        )
        if not booking:
            logger.warning(f"❌ No booking found for confirmation number: {confirmation_number}")
            return f"No booking found for confirmation number {confirmation_number}"
        
        updated = await db_client.query(
            table_name="bookings",
            operation="update",
            filters={"confirmation_number": confirmation_number, "booking_status": "Cancelled"}
        )
        if updated:
            logger.info(f"✅ Successfully cancelled booking {confirmation_number}")
            return f"Booking {confirmation_number} has been cancelled."
        else:
            logger.warning(f"❌ Failed to cancel booking {confirmation_number}")
            return f"Failed to cancel booking {confirmation_number}"
    except Exception as e:
        logger.error(f"❌ Error cancelling booking: {e}", exc_info=True)
        return f"Error cancelling booking: {str(e)}"