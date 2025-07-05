from context import AirlineAgentContext
from database import db_client
import logging

logger = logging.getLogger(__name__)

async def create_initial_context() -> AirlineAgentContext:
    """Create an initial empty AirlineAgentContext."""
    return AirlineAgentContext()

async def load_user_context(registration_id: str) -> AirlineAgentContext:
    """Load user context from Supabase based on registration_id."""
    logger.debug(f"Loading context for registration_id: {registration_id}")
    ctx = await create_initial_context()
    
    if not registration_id:
        return ctx
    
    try:
        response = db_client.table("users").select("id, details").filter("details->>registration_id", "eq", registration_id).execute()
        users = response.data
        if users:
            user = users[0]
            ctx.user_id = user["id"]
            ctx.registration_id = user["details"].get("registration_id", registration_id)
        logger.info(f"Loaded context: {ctx}")
        return ctx
    except Exception as e:
        logger.error(f"Error loading user context: {e}", exc_info=True)
        return ctx

async def load_customer_context(account_number: str) -> AirlineAgentContext:
    """Load customer context from Supabase based on account_number."""
    logger.debug(f"Loading context for account_number: {account_number}")
    ctx = await create_initial_context()
    
    if not account_number:
        return ctx
    
    try:
        response = db_client.table("users").select("id, confirmation_number, account_number").eq("account_number", account_number).execute()
        users = response.data
        if users:
            user = users[0]
            ctx.user_id = user["id"]
            ctx.confirmation_number = user.get("confirmation_number")
            ctx.account_number = user.get("account_number")
        logger.info(f"Loaded context: {ctx}")
        return ctx
    except Exception as e:
        logger.error(f"Error loading customer context: {e}", exc_info=True)
        return ctx