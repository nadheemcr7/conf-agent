from typing import Optional, List
import logging
from context import AirlineAgentContext, UserDetails, BusinessDetails
from database import db_client
from agents import function_tool

logger = logging.getLogger(__name__)

@function_tool(
    name_override="search_businesses",
    description_override="Search for businesses with semantic and fuzzy matching."
)
async def search_businesses(
    industry_sector: Optional[str] = None,
    location: Optional[str] = None,
    company_name: Optional[str] = None,
    sub_sector: Optional[str] = None,
    user_name: Optional[str] = None,
    context: Optional[AirlineAgentContext] = None
) -> str:
    """Search for businesses with semantic and fuzzy matching."""
    try:
        filters = {}
        if industry_sector:
            filters["industrySector"] = industry_sector
        if location:
            filters["location"] = location
        if company_name:
            filters["companyName"] = company_name
        if sub_sector:
            filters["subSector"] = sub_sector
        if user_name:
            filters["user_name"] = user_name
        
        businesses = await db_client.query(
            table_name="ib_businesses",
            select_fields="*, users!inner(*)",
            filters=filters
        )
        
        if not businesses:
            logger.warning("❌ No businesses found matching criteria")
            return "No businesses found matching the provided criteria."
        
        result = f"Found {len(businesses)} businesses:\n"
        for i, business in enumerate(businesses[:3], 1):
            details = business.get("details", {})
            user_info = business.get("users", {})
            result += (
                f"{i}. {details.get('companyName', 'Unknown')} "
                f"({details.get('industrySector', 'Unknown')}) - "
                f"{user_info.get('user_name', 'Unknown')}\n"
            )
        if len(businesses) > 3:
            result += f"...and {len(businesses) - 3} more."
        
        logger.info(f"✅ Found {len(businesses)} businesses matching criteria")
        return result
    except Exception as e:
        logger.error(f"❌ Error searching businesses: {e}", exc_info=True)
        return f"Error searching businesses: {str(e)}"

@function_tool(
    name_override="get_user_businesses",
    description_override="Get businesses for a user."
)
async def get_user_businesses(user_id: str, context: AirlineAgentContext) -> str:
    """Get businesses for a user."""
    try:
        businesses = await db_client.query(
            table_name="ib_businesses",
            filters={"user_id": user_id}
        )
        
        if not businesses:
            logger.warning(f"❌ No businesses found for user_id: {user_id}")
            return f"No businesses found for user {user_id}."
        
        result = f"Businesses for user {user_id}:\n"
        for i, business in enumerate(businesses, 1):
            details = business.get("details", {})
            result += (
                f"{i}. {details.get('companyName', 'Unknown')} "
                f"({details.get('industrySector', 'Unknown')})\n"
            )
        
        logger.info(f"✅ Found {len(businesses)} businesses for user_id: {user_id}")
        return result
    except Exception as e:
        logger.error(f"❌ Error fetching businesses for user {user_id}: {e}", exc_info=True)
        return f"Error fetching businesses: {str(e)}"

@function_tool(
    name_override="add_business",
    description_override="Add a new business for the user."
)
async def add_business(business_details: BusinessDetails, organization_id: str, context: AirlineAgentContext) -> str:
    """Add a new business for the user."""
    try:
        required_fields = ["companyName", "industrySector", "location", "positionTitle"]
        missing_fields = [field for field in required_fields if getattr(business_details, field, None) is None]
        if missing_fields:
            logger.warning(f"❌ Missing required fields: {missing_fields}")
            return f"Missing required fields: {', '.join(missing_fields)}"
        
        success = await db_client.query(
            table_name="ib_businesses",
            operation="insert",
            filters={
                "user_id": context.user_id,
                "details": business_details.dict(exclude_none=True),
                "organization_id": organization_id,
                "is_active": True
            }
        )
        
        if success:
            # Update context.user_details if needed
            if context.user_details:
                context.user_details = UserDetails(
                    user_name=business_details.user_name,
                    registered_email=business_details.email,
                    registration_id=context.registration_id,
                    firstName=context.user_details.firstName,
                    lastName=context.user_details.lastName,
                    email=context.user_details.email
                )
            else:
                context.user_details = UserDetails(
                    user_name=business_details.user_name,
                    registered_email=business_details.email,
                    registration_id=context.registration_id
                )
            logger.info(f"✅ Successfully added business {business_details.companyName}")
            return f"Successfully added business {business_details.companyName}."
        else:
            logger.warning("❌ Failed to add business")
            return "Failed to add business."
    except Exception as e:
        logger.error(f"❌ Error adding business: {e}", exc_info=True)
        return f"Error adding business: {str(e)}"

@function_tool(
    name_override="display_business_form",
    description_override="Display the business registration form."
)
async def display_business_form(context: AirlineAgentContext) -> dict:
    """Display the business registration form (placeholder implementation)."""
    try:
        form = {
            "fields": [
                {"name": "companyName", "type": "text", "required": True},
                {"name": "industrySector", "type": "text", "required": True},
                {"name": "subSector", "type": "text", "required": False},
                {"name": "location", "type": "text", "required": True},
                {"name": "positionTitle", "type": "text", "required": True}
            ]
        }
        logger.info(f"✅ Retrieved business form for user_id: {context.user_id}")
        return form
    except Exception as e:
        logger.error(f"❌ Error displaying business form: {e}", exc_info=True)
        return {"error": f"Error displaying business form: {str(e)}"}