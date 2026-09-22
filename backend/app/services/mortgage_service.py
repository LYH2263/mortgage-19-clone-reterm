from app.db import connect
from app.engines.amortization import equal_payment_schedule
from app.repositories import loans, runs, settings

class MortgageService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_loans(self): return loans.list_all(self._c)
    def loan(self, lid): return loans.get(self._c, lid)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def schedule(self, principal, annual_rate, months, loan_id, persist, preview_rows=12):
        full = equal_payment_schedule(principal, annual_rate, months)
        out = {k: full[k] for k in ("monthly_payment", "total_interest", "total_payment")}
        out["preview"] = full["rows"][:preview_rows]
        out["row_count"] = len(full["rows"])
        rid = None
        if persist:
            rid = runs.insert(self._c, "schedule", {"principal": principal, "annual_rate": annual_rate, "months": months}, out, loan_id)
        return {"run_id": rid, **out}
    def dashboard(self):
        items = loans.list_all(self._c)
        return {"loan_count": len(items), "clean": len([x for x in items if "种子" not in x["name"]]), "dirty": len([x for x in items if "种子" in x["name"]])}
    def clone_term(self, loan_id, new_months, persist=False, keep_clone=False):
        src = loans.get(self._c, loan_id)
        if not src: return None
        if int(new_months) == src["months"]: raise ValueError("same_months")
        src_calc = equal_payment_schedule(src["principal"], src["annual_rate"], src["months"])
        cln_calc = equal_payment_schedule(src["principal"], src["annual_rate"], new_months)
        source_side = {"loan_id": src["id"], "name": src["name"], "principal": src["principal"], "annual_rate": src["annual_rate"],
            "months": src["months"], "monthly_payment": src_calc["monthly_payment"], "total_interest": src_calc["total_interest"]}
        clone_side = {"loan_id": None, "kept": False, "name": f'{src["name"]}·换期{new_months}期', "principal": src["principal"],
            "annual_rate": src["annual_rate"], "months": new_months,
            "monthly_payment": cln_calc["monthly_payment"], "total_interest": cln_calc["total_interest"]}
        diff = round(cln_calc["monthly_payment"] - src_calc["monthly_payment"], 2)
        run_id = None
        if persist:
            try:
                self._c.execute("BEGIN")
                clone_side["loan_id"] = loans.insert(self._c, clone_side["name"], src["principal"], src["annual_rate"], new_months)
                clone_side["kept"] = bool(keep_clone)
                payload = {"source_loan_id": src["id"], "clone_loan_id": clone_side["loan_id"], "new_months": new_months, "keep_clone": bool(keep_clone)}
                result = {"source": source_side, "clone": clone_side, "monthly_payment_diff": diff}
                run_id = runs.insert(self._c, "term_clone", payload, result, src["id"], commit=False)
                if not keep_clone: loans.delete(self._c, clone_side["loan_id"])
                self._c.commit()
            except Exception:
                self._c.rollback()
                raise
        return {"run_id": run_id, "persisted": bool(persist), "source": source_side, "clone": clone_side, "monthly_payment_diff": diff}
