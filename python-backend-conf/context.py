from pydantic import BaseModel
from typing import Optional, List

class CustomerBooking(BaseModel):
    id: Optional[int] = None
    confirmation_number: Optional[str] = None
    customer_id: Optional[int] = None
    flight_id: Optional[int] = None
    flight_number: Optional[str] = None
    seat_number: Optional[str] = None
    booking_status: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    account_number: Optional[str] = None

    class Config:
        extra = "forbid"  # Strict schema

class UserDetails(BaseModel):
    user_id: Optional[str] = None
    registration_id: Optional[str] = None
    organization_id: Optional[str] = None
    user_name: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    registered_email: Optional[str] = None

    class Config:
        extra = "forbid"  # Strict schema

class BusinessDetails(BaseModel):
    companyName: str
    industrySector: str
    location: str
    positionTitle: str
    user_name: str
    email: str
    subSector: Optional[str] = None
    establishmentYear: Optional[str] = None
    legalStructure: Optional[str] = None
    briefDescription: Optional[str] = None
    productsOrServices: Optional[str] = None
    website: Optional[str] = None
    annualTurnoverRange: Optional[str] = None
    directEmployment: Optional[str] = None
    indirectEmployment: Optional[str] = None

    class Config:
        extra = "forbid"  # Strict schema

class AirlineAgentContext(BaseModel):
    # User identification
    confirmation_number: Optional[str] = None
    account_number: Optional[str] = None
    registration_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    
    # Customer details
    passenger_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_email: Optional[str] = None
    
    # Flight/booking details
    flight_number: Optional[str] = None
    flight_id: Optional[int] = None
    seat_number: Optional[str] = None
    booking_id: Optional[int] = None
    
    # Related data
    customer_bookings: List[CustomerBooking] = []
    user_details: Optional[UserDetails] = None
    business_details: Optional[BusinessDetails] = None

    class Config:
        extra = "forbid"  # Strict schema for agents library