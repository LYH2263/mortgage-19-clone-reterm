from pydantic import BaseModel, Field
from app.services.mortgage_service import MAX_MONTHS

class TermCloneRequest(BaseModel):
    new_months: int = Field(gt=0, le=MAX_MONTHS)
    persist: bool = False
    keep_clone: bool = False

class LoanRateUpdate(BaseModel):
    annual_rate: float = Field(ge=0)
