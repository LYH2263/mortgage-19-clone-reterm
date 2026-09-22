import json
import os
import tempfile

import pytest

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="mortgage-term-clone-")

from app import seed  # noqa: E402
from app.repositories import runs  # noqa: E402
from app.services.mortgage_service import MortgageService  # noqa: E402

seed.init_db()


def test_trial_clone_writes_nothing():
    with MortgageService() as s:
        before = len(s.list_loans())
        out = s.clone_term(1, 240)
        assert out["persisted"] is False
        assert out["run_id"] is None
        assert out["clone"]["loan_id"] is None
        assert out["clone"]["kept"] is False
        assert out["source"]["months"] == 360
        assert out["clone"]["months"] == 240
        assert out["clone"]["principal"] == out["source"]["principal"]
        assert out["clone"]["annual_rate"] == out["source"]["annual_rate"]
        assert out["monthly_payment_diff"] == round(out["clone"]["monthly_payment"] - out["source"]["monthly_payment"], 2)
        assert len(s.list_loans()) == before
        assert all(h["kind"] != "term_clone" for h in s.history(100))


def test_same_months_rejected():
    with MortgageService() as s:
        with pytest.raises(ValueError):
            s.clone_term(1, 360)


def test_missing_source_returns_none():
    with MortgageService() as s:
        assert s.clone_term(9999, 240) is None


def test_persist_records_and_drops_clone():
    with MortgageService() as s:
        before = len(s.list_loans())
        out = s.clone_term(1, 240, persist=True, keep_clone=False)
        assert out["run_id"]
        assert out["clone"]["loan_id"] is not None
        assert out["clone"]["kept"] is False
        assert len(s.list_loans()) == before  # 克隆档案未保留
        rec = [h for h in s.history(100) if h["id"] == out["run_id"]][0]
        assert rec["kind"] == "term_clone"
        assert rec["loan_id"] == 1
        payload = json.loads(rec["input_json"])
        assert payload["source_loan_id"] == 1
        assert payload["clone_loan_id"] == out["clone"]["loan_id"]
        result = json.loads(rec["result_json"])
        assert result["source"]["monthly_payment"] == out["source"]["monthly_payment"]
        assert result["clone"]["monthly_payment"] == out["clone"]["monthly_payment"]
        assert result["monthly_payment_diff"] == out["monthly_payment_diff"]


def test_persist_keep_clone():
    with MortgageService() as s:
        before = len(s.list_loans())
        out = s.clone_term(1, 180, persist=True, keep_clone=True)
        assert out["clone"]["kept"] is True
        assert len(s.list_loans()) == before + 1
        clone = s.loan(out["clone"]["loan_id"])
        assert clone["months"] == 180
        assert clone["principal"] == 1000000
        assert clone["annual_rate"] == 3.5
        assert s.loan(1)["months"] == 360  # 源档案不变
        # 改源档案利率后，已钉对照条仍为快照值
        s._c.execute("UPDATE loans SET annual_rate=9.9 WHERE id=1")
        s._c.commit()
        rec = [h for h in s.history(100) if h["id"] == out["run_id"]][0]
        result = json.loads(rec["result_json"])
        assert result["source"]["annual_rate"] == 3.5
        assert result["source"]["monthly_payment"] == out["source"]["monthly_payment"]
        s._c.execute("UPDATE loans SET annual_rate=3.5 WHERE id=1")
        s._c.commit()


def test_failure_leaves_no_half_clone(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("insert failed")

    monkeypatch.setattr(runs, "insert", boom)
    with MortgageService() as s:
        before = len(s.list_loans())
        with pytest.raises(RuntimeError):
            s.clone_term(1, 120, persist=True)
        assert len(s.list_loans()) == before
        assert all(x["months"] != 120 for x in s.list_loans())
