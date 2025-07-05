from rapidfuzz import fuzz
from typing import Optional

# Intent mappings for agent routing
SEMANTIC_MAPPINGS = {
    "customer_service": {
        "keywords": [
            "flight", "booking", "cancel", "seat", "status", "check-in",
            "reservation", "ticket", "change", "delay", "departure", "arrival"
        ]
    },
    "conference": {
        "keywords": [
            "session", "speaker", "track", "room", "schedule", "conference",
            "talk", "presentation", "event", "agenda", "summit"
        ]
    },
    "networking": {
        "keywords": [
            "business", "company", "networking", "profile", "industry",
            "fintech", "tech", "startup", "register business"
        ]
    }
}

# Fields that support fuzzy matching in database queries
FUZZY_FIELDS = {
    "customers": ["name", "email"],
    "users": ["user_name", "email", "registered_email"],
    "bookings": ["confirmation_number", "seat_number"],
    "flights": ["flight_number", "origin", "destination"],
    "ib_businesses": ["companyName", "industrySector", "subSector", "location"]
}

# Canonical key mappings for field name normalization
KEY_MAPPINGS = {
    "email": "email",
    "registered_email": "email",
    "user_name": "name",
    "username": "name",
    "company": "companyName",
    "industry": "industrySector",
    "subsector": "subSector",
    "city": "location",
    "confirmation": "confirmation_number",
    "flight": "flight_number",
    "seat": "seat_number"
}

# Canonical value mappings for fuzzy matching
VALUE_MAPPINGS = {
    "location": {
        "new york": "NYC",
        "ny": "NYC",
        "los angeles": "LAX",
        "la": "LAX",
        "san francisco": "SFO",
        "sf": "SFO"
    },
    "industrySector": {
        "fin tech": "Fintech",
        "finance": "Fintech",
        "technology": "Tech",
        "tech": "Tech",
        "aviation": "Aviation",
        "aerospace": "Aviation"
    }
}

def get_canonical_key(key: str) -> str:
    """Normalize field names to canonical keys."""
    return KEY_MAPPINGS.get(key.lower(), key)

def get_canonical_value(field: str, value: str, threshold: float = 80.0) -> Optional[str]:
    """Normalize field values using fuzzy matching if applicable."""
    if field not in FUZZY_FIELDS.get("customers", []) + FUZZY_FIELDS.get("users", []) + \
                    FUZZY_FIELDS.get("bookings", []) + FUZZY_FIELDS.get("flights", []) + \
                    FUZZY_FIELDS.get("ib_businesses", []):
        return value
    
    canonical_field = get_canonical_key(field)
    if canonical_field in VALUE_MAPPINGS:
        for canonical, normalized in VALUE_MAPPINGS[canonical_field].items():
            if fuzz.ratio(value.lower(), canonical.lower()) >= threshold:
                return normalized
    return value