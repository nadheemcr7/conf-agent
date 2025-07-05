from context import AirlineAgentContext
from database import db_client
import logging

logger = logging.getLogger(__name__)

async def create_initial_context() -> AirlineAgentContext:
    """Create an initial empty AirlineAgentContext."""
    return AirlineAgentContext()

async def load_user_context(registration_id: str) -> AirlineAgentContext:
    """Load user context from database."""
    ctx = await create_initial_context()
    ctx.registration_id = registration_id
    
    try:
        # Try to load user data
        response = db_client.table("users").select("id, details").filter("details->>registration_id", "eq", registration_id).execute()
        
        if response.data:
            user = response.data[0]
            ctx.user_id = user["id"]
            if user.get("details"):
                details = user["details"]
                ctx.passenger_name = details.get("user_name") or f"{details.get('firstName', '')} {details.get('lastName', '')}".strip()
                ctx.customer_email = details.get("email")
        
        logger.info(f"Loaded context for registration_id: {registration_id}")
        return ctx
        
    except Exception as e:
        logger.warning(f"Could not load user context: {e}")
        return ctx