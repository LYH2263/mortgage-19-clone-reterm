from fastapi import APIRouter, HTTPException
from app.schemas.term_clone import TermCloneRequest
from app.services.mortgage_service import MortgageService
router = APIRouter()
@router.get("/loans")
def list_loans():
    with MortgageService() as s: return {"items": s.list_loans()}
@router.get("/loans/{loan_id}")
def get_loan(loan_id: int):
    with MortgageService() as s:
        row = s.loan(loan_id)
        if not row: raise HTTPException(404)
        return row
@router.post("/loans/{loan_id}/term-clone")
def clone_term(loan_id: int, body: TermCloneRequest):
    with MortgageService() as s:
        try:
            out = s.clone_term(loan_id, body.new_months, body.persist, body.keep_clone)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        if out is None: raise HTTPException(404)
        return out
