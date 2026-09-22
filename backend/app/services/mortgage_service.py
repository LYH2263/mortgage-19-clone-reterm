import json
from app.db import connect
from app.engines.amortization import equal_payment_schedule
from app.repositories import loans, runs, settings

MAX_MONTHS = 600
COMPARE_KIND = "term_clone_compare"

class CloneTermError(ValueError): pass

class MortgageService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_loans(self): return loans.list_all(self._c)
    def loan(self, lid): return loans.get(self._c, lid)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def run_record(self, rid):
        row = runs.get(self._c, rid)
        if not row: return None
        row["input"] = json.loads(row.pop("input_json"))
        row["result"] = json.loads(row.pop("result_json"))
        return row
    def schedule(self, principal, annual_rate, months, loan_id, persist, preview_rows=12):
        full = equal_payment_schedule(principal, annual_rate, months)
        out = {k: full[k] for k in ("monthly_payment", "total_interest", "total_payment")}
        out["preview"] = full["rows"][:preview_rows]
        out["row_count"] = len(full["rows"])
        rid = None
        if persist:
            rid = runs.insert(self._c, "schedule", {"principal": principal, "annual_rate": annual_rate, "months": months}, out, loan_id)
        return {"run_id": rid, **out}
    def clone_term_compare(self, source_loan_id, new_months, persist=False, keep_clone=False):
        src = loans.get(self._c, source_loan_id)
        if not src: return None
        try: nm = int(new_months)
        except (TypeError, ValueError): raise CloneTermError("新期数须为整数")
        if nm < 1 or nm > MAX_MONTHS: raise CloneTermError(f"新期数须落在 1~{MAX_MONTHS} 内")
        if nm == src["months"]: raise CloneTermError("新期数不得与源期数相同")
        src_sch = equal_payment_schedule(src["principal"], src["annual_rate"], src["months"])
        clone_sch = equal_payment_schedule(src["principal"], src["annual_rate"], nm)
        clone_name = f"{src['name']}·换期{nm}期"
        source_side = {"loan_id": src["id"], "name": src["name"], "principal": src["principal"],
            "annual_rate": src["annual_rate"], "months": src["months"],
            "monthly_payment": src_sch["monthly_payment"], "total_interest": src_sch["total_interest"]}
        clone_side = {"loan_id": None, "kept": False, "name": clone_name, "principal": src["principal"],
            "annual_rate": src["annual_rate"], "months": nm,
            "monthly_payment": clone_sch["monthly_payment"], "total_interest": clone_sch["total_interest"]}
        compare = {"source": source_side, "clone": clone_side,
            "monthly_diff": round(clone_sch["monthly_payment"] - src_sch["monthly_payment"], 2)}
        rid = None
        if persist:
            try:
                clone_id = loans.insert(self._c, clone_name, src["principal"], src["annual_rate"], nm)
                clone_side["loan_id"] = clone_id
                clone_side["kept"] = bool(keep_clone)
                payload = {"source_loan_id": src["id"], "clone_loan_id": clone_id,
                    "new_months": nm, "keep_clone": bool(keep_clone)}
                rid = runs.insert(self._c, COMPARE_KIND, payload, compare, src["id"], commit=False)
                if not keep_clone: loans.delete(self._c, clone_id)
                self._c.commit()
            except Exception:
                self._c.rollback()
                raise
        return {"run_id": rid, "persisted": bool(persist), **compare}
    def update_loan_rate(self, lid, annual_rate):
        if not loans.get(self._c, lid): return None
        loans.update_annual_rate(self._c, lid, annual_rate)
        self._c.commit()
        return loans.get(self._c, lid)
    def dashboard(self):
        items = loans.list_all(self._c)
        return {"loan_count": len(items), "clean": len([x for x in items if "种子" not in x["name"]]), "dirty": len([x for x in items if "种子" in x["name"]])}
