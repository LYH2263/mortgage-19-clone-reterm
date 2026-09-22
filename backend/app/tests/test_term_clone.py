import os, tempfile
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="mort-clone-test-"))

import pytest
from app import seed
from app.services.mortgage_service import CloneTermError, MortgageService
import app.services.mortgage_service as svc_mod

seed.init_db()  # 临时库落种子：#1 100万/3.5%/360期，#2 80万/6.8%/240期

def svc(): return MortgageService()

def compare_runs(s):
    return [r for r in s.history(1000) if r["kind"] == "term_clone_compare"]

def test_trial_compare_writes_nothing():
    with svc() as s:
        n_loans, n_runs = len(s.list_loans()), len(compare_runs(s))
        res = s.clone_term_compare(1, 240)
        assert res["persisted"] is False and res["run_id"] is None
        assert res["source"]["months"] == 360 and res["clone"]["months"] == 240
        assert res["clone"]["loan_id"] is None
        assert res["monthly_diff"] == round(res["clone"]["monthly_payment"] - res["source"]["monthly_payment"], 2)
        assert res["monthly_diff"] > 0  # 缩期月供更高
        assert len(s.list_loans()) == n_loans and len(compare_runs(s)) == n_runs

def test_same_months_rejected():
    with svc() as s:
        with pytest.raises(CloneTermError):
            s.clone_term_compare(1, 360)

def test_out_of_range_months_rejected():
    with svc() as s:
        for bad in (0, -12, 601):
            with pytest.raises(CloneTermError):
                s.clone_term_compare(1, bad)

def test_missing_source_returns_none():
    with svc() as s:
        assert s.clone_term_compare(9999, 120) is None

def test_persist_keep_clone():
    with svc() as s:
        res = s.clone_term_compare(1, 240, persist=True, keep_clone=True)
        cid = res["clone"]["loan_id"]
        assert cid and res["clone"]["kept"] is True
        clone = s.loan(cid)
        assert (clone["principal"], clone["annual_rate"], clone["months"]) == (1000000, 3.5, 240)
        src = s.loan(1)
        assert (src["principal"], src["annual_rate"], src["months"]) == (1000000, 3.5, 360)
        rec = s.run_record(res["run_id"])
        assert rec["kind"] == "term_clone_compare"
        assert rec["input"]["source_loan_id"] == 1 and rec["input"]["clone_loan_id"] == cid
        assert rec["result"]["source"]["monthly_payment"] == res["source"]["monthly_payment"]
        assert rec["result"]["clone"]["monthly_payment"] == res["clone"]["monthly_payment"]
        assert rec["result"]["monthly_diff"] == res["monthly_diff"]

def test_persist_without_keep_drops_clone_but_record_stays():
    with svc() as s:
        res = s.clone_term_compare(1, 180, persist=True, keep_clone=False)
        cid = res["clone"]["loan_id"]
        assert cid and res["clone"]["kept"] is False
        assert s.loan(cid) is None
        rec = s.run_record(res["run_id"])
        assert rec["result"]["clone"]["loan_id"] == cid
        assert rec["result"]["source"]["monthly_payment"] > 0
        assert rec["result"]["clone"]["monthly_payment"] > 0

def test_failed_clone_leaves_no_partial_loan(monkeypatch):
    with svc() as s:
        n_loans, n_runs = len(s.list_loans()), len(compare_runs(s))
        def boom(*a, **k): raise RuntimeError("disk full")
        monkeypatch.setattr(svc_mod.runs, "insert", boom)
        with pytest.raises(RuntimeError):
            s.clone_term_compare(1, 120, persist=True, keep_clone=True)
        assert len(s.list_loans()) == n_loans
        assert len(compare_runs(s)) == n_runs

def test_rate_change_does_not_rewrite_record():
    with svc() as s:
        res = s.clone_term_compare(2, 300, persist=True, keep_clone=False)
        before = s.run_record(res["run_id"])
        s.update_loan_rate(2, 9.9)
        after = s.run_record(res["run_id"])
        assert after["result"] == before["result"]
        assert after["result"]["source"]["annual_rate"] == 6.8
        assert s.loan(2)["annual_rate"] == 9.9
        s.update_loan_rate(2, 6.8)

def test_update_loan_rate_missing():
    with svc() as s:
        assert s.update_loan_rate(9999, 5.0) is None
