from pydantic import BaseModel

class CustomerBooking(BaseModel):
    confirmation_number: str
    account_number: str

class UserDetails(BaseModel):
    user_id: str
    registration_id: str
    organization_id: str | None = None

class BusinessDetails(BaseModel):
    companyName: str
    industrySector: str
    location: str
    positionTitle: str
    user_name: str
    email: str

class AirlineAgentContext(BaseModel):
    confirmation_number: str | None = None
    account_number: str | None = None
    registration_id: str | None = None
    user_id: str | None = None
    business_details: BusinessDetails | None = None
    organization_id: str | None = None

    class Config:
        extra = "forbid"  # Prevent extra fields