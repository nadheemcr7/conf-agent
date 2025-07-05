from typing import Dict, Any, Optional
import logging
from context import AirlineAgentContext, CustomerBooking
from database import db_client
from agents import function_tool

logger = logging.getLogger(__name__)

@function_tool(
    name_override="get_booking_details",
    description_override="Get booking details by confirmation number and update context."
)
async def get_booking_details(confirmation_number: str, context: AirlineAgentContext) -> str:
    """Get booking details by confirmation number and update context."""
    try:
        booking = await db_client.query(
            table_name="bookings",
            select_fields="*, customers:customer_id(*), flights:flight_id(*)",
            filters={"confirmation_number": confirmation_number},
            single=True
        )
        
        if not booking:
            logger.warning(f"❌ No booking found for confirmation number: {confirmation_number}")
            return f"No booking found for confirmation number {confirmation_number}"
        
        logger.debug(f"✅ Found booking: {booking}")
        
        # Update context
        context.passenger_name = booking.get("customers", {}).get("name")
        context.customer_id = booking.get("customer_id")
        context.account_number = booking.get("customers", {}).get("account_number")
        context.customer_email = booking.get("customers", {}).get("email")
        context.flight_number = booking.get("flights", {}).get("flight_number")
        context.flight_id = booking.get("flight_id")
        context.seat_number = booking.get("seat_number")
        context.booking_id = booking.get("id")
        
        # Update customer_bookings
        context.customer_bookings = [
            CustomerBooking(
                id=booking.get("id"),
                confirmation_number=booking.get("confirmation_number"),
                customer_id=booking.get("customer_id"),
                flight_id=booking.get("flight_id"),
                flight_number=booking.get("flights", {}).get("flight_number"),
                seat_number=booking.get("seat_number"),
                booking_status=booking.get("booking_status"),
                origin=booking.get("flights", {}).get("origin"),
                destination=booking.get("flights", {}).get("destination"),
                customer_name=booking.get("customers", {}).get("name"),
                customer_email=booking.get("customers", {}).get("email"),
                account_number=booking.get("customers", {}).get("account_number")
            )
        ]
        
        return (
            f"Booking Details for Confirmation {confirmation_number}:\n"
            f"Passenger: {context.passenger_name}\n"
            f"Flight: {context.flight_number}\n"
            f"Seat: {context.seat_number}\n"
            f"Status: {booking.get('booking_status')}\n"
            f"Origin: {booking.get('flights', {}).get('origin')}\n"
            f"Destination: {booking.get('flights', {}).get('destination')}"
        )
    except Exception as e:
        logger.error(f"❌ Error fetching booking details for {confirmation_number}: {e}", exc_info=True)
        return f"Error fetching booking details: {str(e)}"