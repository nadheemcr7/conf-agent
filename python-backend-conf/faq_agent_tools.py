from agents import function_tool

@function_tool(
    name_override="faq_lookup_tool", 
    description_override="Comprehensive airline information lookup covering policies, services, aircraft details, and general travel information."
)
async def faq_lookup_tool(question: str) -> str:
    """Lookup comprehensive airline information including policies, services, and travel details."""
    q = question.lower()
    
    if any(word in q for word in ["bag", "baggage", "luggage", "carry", "checked"]):
        return (
            "**Comprehensive Baggage Information:**\n\n"
            "**Carry-on Baggage:**\n"
            "- Dimensions: Maximum 22\" x 14\" x 9\" (56cm x 36cm x 23cm)\n"
            "- Weight: Up to 50 pounds (22.7 kg)\n"
            "- Quantity: One carry-on bag per passenger\n"
            "- Additional: One personal item (purse, laptop bag, small backpack)\n\n"
            "**Checked Baggage:**\n"
            "- First bag: Included in most fares\n"
            "- Additional bags: Fees apply ($50-$150 depending on route)\n"
            "- Weight limit: 50 pounds (22.7 kg) per bag\n"
            "- Overweight fees: $100-$200 for bags 51-70 lbs\n\n"
            "**Restricted Items:**\n"
            "- Liquids over 3.4oz in carry-on\n"
            "- Sharp objects, tools over 7 inches\n"
            "- Flammable materials, batteries over 100Wh\n"
            "- Full list available on our website under 'Travel Guidelines'"
        )
    elif any(word in q for word in ["seats", "plane", "aircraft", "how many", "configuration", "layout"]):
        return (
            "**Aircraft Configuration & Seating:**\n\n"
            "**Total Capacity:** 120 passengers\n\n"
            "**Class Distribution:**\n"
            "- **Business Class:** 22 seats (Rows 1-4)\n"
            "  - Premium service, priority boarding\n"
            "  - Extra legroom, wider seats\n"
            "  - Complimentary meals and beverages\n\n"
            "- **Economy Plus:** 20 seats (Rows 5-8)\n"
            "  - Extra legroom (4-6 inches more)\n"
            "  - Priority boarding after Business\n"
            "  - Available for upgrade fee\n\n"
            "- **Economy Class:** 78 seats (Rows 9-24)\n"
            "  - Standard seating configuration\n"
            "  - 3-3 layout with center aisle\n\n"
            "**Special Seating:**\n"
            "- **Exit Rows:** Rows 4 and 16 (extra legroom, restrictions apply)\n"
            "- **Window Seats:** A and F positions\n"
            "- **Aisle Seats:** C and D positions\n"
            "- **Middle Seats:** B and E positions"
        )
    else:
        return (
            "I have comprehensive information about:\n\n"
            "• **Baggage policies** - carry-on and checked bag rules\n"
            "• **Aircraft information** - seating, configuration, capacity\n"
            "• **WiFi and connectivity** - free internet service details\n"
            "• **Check-in procedures** - online and airport options\n"
            "• **Cancellation policies** - refunds and change fees\n"
            "• **Dining services** - meals and beverage options\n"
            "• **Travel assistance** - special services and support\n\n"
            "Please ask me about any of these topics, or rephrase your question for more specific information. "
            "For booking-specific questions, I can transfer you to the appropriate specialist."
        )