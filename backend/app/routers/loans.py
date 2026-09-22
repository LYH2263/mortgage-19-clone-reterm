from fastapi import APIRouter, HTTPException
from app.schemas.loans import LoanRateUpdate, TermCloneRequest
from app.services.mortgage_service import CloneTermError, MortgageService
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
def term_clone(loan_id: int, body: TermCloneRequest):
    with MortgageService() as s:
        try:
            res = s.clone_term_compare(loan_id, body.new_months, body.persist, body.keep_clone)
        except CloneTermError as e:
            raise HTTPException(422, str(e))
        if res is None: raise HTTPException(404)
        return res
@router.patch("/loans/{loan_id}")
def update_loan(loan_id: int, body: LoanRateUpdate):
    with MortgageService() as s:
        row = s.update_loan_rate(loan_id, body.annual_rate)
        if not row: raise HTTPException(404)
        return row
