from pydantic import BaseModel, Field
class TermCloneRequest(BaseModel):
    new_months: int = Field(gt=0, le=600)
    persist: bool = False
    keep_clone: bool = False
