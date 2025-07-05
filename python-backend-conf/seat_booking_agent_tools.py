from typing import Dict, Any
import logging
from context import AirlineAgentContext, CustomerBooking
from database import db_client
from agents import function_tool
from common_tools import get_booking_details

logger = logging.getLogger(__name__)

@function_tool(
    name_override="update_seat",
    description_override="Update the seat number for a booking."
)
async def update_seat(confirmation_number: str, new_seat: str, context: AirlineAgentContext) -> str:
    """Update the seat number for a booking."""
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
            filters={"confirmation_number": confirmation_number, "seat_number": new_seat}
        )
        
        if updated:
            context.seat_number = new_seat
            # Update customer_bookings if booking exists in context
            for booking in context.customer_bookings:
                if booking.confirmation_number == confirmation_number:
                    booking.seat_number = new_seat
            logger.info(f"✅ Successfully updated seat to {new_seat} for confirmation {confirmation_number}")
            return f"Seat updated to {new_seat} for confirmation number {confirmation_number}"
        else:
            logger.warning(f"❌ Failed to update seat for confirmation {confirmation_number}")
            return f"Failed to update seat for confirmation {confirmation_number}"
    except Exception as e:
        logger.error(f"❌ Error updating seat for {confirmation_number}: {e}", exc_info=True)
        return f"Error updating seat: {str(e)}"

@function_tool(
    name_override="display_seat_map",
    description_override="Display the seat map for a flight."
)
async def display_seat_map(confirmation_number: str, context: AirlineAgentContext) -> Dict[str, Any]:
    """Display the seat map for a flight (placeholder implementation)."""
    try:
        booking = await db_client.query(
            table_name="bookings",
            select_fields="*, flights:flight_id(*)",
            filters={"confirmation_number": confirmation_number},
            single=True
        )
        if not booking:
            logger.warning(f"❌ No booking found for confirmation number: {confirmation_number}")
            return {"error": f"No booking found for confirmation number {confirmation_number}"}
        
        # Placeholder seat map logic
        seat_map = {"flight_number": booking.get("flights", {}).get("flight_number"), "seats": ["1A", "1B", "2A", "2B"]}
        logger.info(f"✅ Retrieved seat map for {confirmation_number}")
        return seat_map
    except Exception as e:
        logger.error(f"❌ Error displaying seat map: {e}", exc_info=True)
        return {"error": f"Error displaying seat map: {str(e)}"}