"""
單元測試 — crawler/fetch.py 的 MoneyDJ 除權除息儲存邏輯

覆蓋：
- _split_moneydj_events 事件拆分（息 / 權 / 權息 / 不同日拆兩筆）
- _merge_same_day_dividend_events 同日 息+權 併成權息
- _merge_moneydj_records 去重、舊資料修正、排序
"""
import json
import pytest
from crawler.fetch import (
    _split_moneydj_events,
    _merge_same_day_dividend_events,
    _merge_moneydj_records,
)


def _div(**kw):
    """輔助：建立一筆 息 事件"""
    base = {
        "code": "5287", "name": "數字", "ex_date": "2026-08-27",
        "type": "息", "earnings_dividend": 6.15, "reserve_dividend": 0.0,
        "cash_dividend": 6.15, "pay_date": "2026-10-02",
        "earnings_stock": 0.0, "reserve_stock": 0.0, "stock_dividend": 0.0,
    }
    base.update(kw)
    return base


def _right(**kw):
    """輔助：建立一筆 權 事件"""
    base = {
        "code": "5287", "name": "數字", "ex_date": "2026-08-27",
        "type": "權", "earnings_dividend": 0.0, "reserve_dividend": 0.0,
        "cash_dividend": 0.0, "pay_date": "",
        "earnings_stock": 0.9, "reserve_stock": 0.0, "stock_dividend": 0.9,
    }
    base.update(kw)
    return base


class TestSplitMoneydjEvents:
    """測試事件拆分"""

    def test_same_day_cash_and_stock_single_right_dividend(self):
        """同日除息+除權 → 單筆 權息（含現金與股票股利）"""
        records = [{
            "code": "5283", "name": "禾聯碩",
            "ex_date": "2026-08-28", "ex_rights_date": "2026-08-28",
            "earnings_dividend": 0.2, "reserve_dividend": 0.0,
            "cash_dividend": 0.2, "pay_date": "2026-10-02",
            "earnings_stock": 1.6, "reserve_stock": 0.0,
            "stock_dividend": 1.6,
        }]

        events = _split_moneydj_events(records)
        assert len(events) == 1
        assert events[0]["type"] == "權息"
        assert events[0]["cash_dividend"] == 0.2
        assert events[0]["stock_dividend"] == 1.6
        assert events[0]["pay_date"] == "2026-10-02"

    def test_different_days_split_two_events(self):
        """不同日除息+除權 → 拆成 息、權 兩筆"""
        records = [{
            "code": "2330", "name": "台積電",
            "ex_date": "2026-07-15", "ex_rights_date": "2026-07-16",
            "earnings_dividend": 3.5, "reserve_dividend": 0.0,
            "cash_dividend": 3.5, "pay_date": "2026-08-10",
            "earnings_stock": 0.1, "reserve_stock": 0.0,
            "stock_dividend": 0.1,
        }]

        events = _split_moneydj_events(records)
        assert len(events) == 2
        div_evt = next(e for e in events if e["type"] == "息")
        right_evt = next(e for e in events if e["type"] == "權")
        assert div_evt["ex_date"] == "2026-07-15"
        assert div_evt["cash_dividend"] == 3.5
        assert div_evt["stock_dividend"] == 0.0  # 息不含股票股利
        assert right_evt["ex_date"] == "2026-07-16"
        assert right_evt["stock_dividend"] == 0.1
        assert right_evt["cash_dividend"] == 0.0

    def test_cash_only(self):
        """僅除息 → type=息"""
        records = [{
            "code": "00679B", "name": "元大美債20年",
            "ex_date": "2026-08-21", "ex_rights_date": "",
            "earnings_dividend": 0.28, "reserve_dividend": 0.0,
            "cash_dividend": 0.28, "pay_date": "2026-09-11",
            "earnings_stock": 0.0, "reserve_stock": 0.0,
            "stock_dividend": 0.0,
        }]

        events = _split_moneydj_events(records)
        assert len(events) == 1
        assert events[0]["type"] == "息"

    def test_stock_only(self):
        """僅除權 → type=權"""
        records = [{
            "code": "1234", "name": "測試股",
            "ex_date": "", "ex_rights_date": "2026-09-01",
            "earnings_dividend": 0.0, "reserve_dividend": 0.0,
            "cash_dividend": 0.0, "pay_date": "",
            "earnings_stock": 0.5, "reserve_stock": 0.0,
            "stock_dividend": 0.5,
        }]

        events = _split_moneydj_events(records)
        assert len(events) == 1
        assert events[0]["type"] == "權"
        assert events[0]["ex_date"] == "2026-09-01"

    def test_no_date_produces_no_event(self):
        """除息日與除權日皆空 → 不產生事件"""
        records = [{
            "code": "9999", "name": "無日期",
            "ex_date": "", "ex_rights_date": "",
            "earnings_dividend": 0.0, "reserve_dividend": 0.0,
            "cash_dividend": 0.0, "pay_date": "",
            "earnings_stock": 0.0, "reserve_stock": 0.0,
            "stock_dividend": 0.0,
        }]

        assert _split_moneydj_events(records) == []


class TestMergeSameDayDividendEvents:
    """測試同日 息+權 併成權息"""

    def test_merge_div_and_right_same_day(self):
        """同日的 息 + 權 → 單筆權息（現金取自息、股票取自權）"""
        merged = _merge_same_day_dividend_events([_div(), _right()])

        assert len(merged) == 1
        rec = merged[0]
        assert rec["type"] == "權息"
        assert rec["code"] == "5287"
        assert rec["ex_date"] == "2026-08-27"
        assert rec["cash_dividend"] == 6.15
        assert rec["stock_dividend"] == 0.9
        assert rec["pay_date"] == "2026-10-02"

    def test_keep_existing_complete_right_dividend(self):
        """已有權息時，部分重複的 息/權 捨棄（修正殘留資料）"""
        complete = {
            "code": "5283", "name": "禾聯碩", "ex_date": "2026-08-28",
            "type": "權息", "cash_dividend": 0.2, "stock_dividend": 1.6,
            "pay_date": "2026-10-02",
        }
        partial = {
            "code": "5283", "name": "禾聯碩", "ex_date": "2026-08-28",
            "type": "權", "cash_dividend": 0.0, "stock_dividend": 1.6,
            "pay_date": "",
        }

        merged = _merge_same_day_dividend_events([complete, partial])
        assert len(merged) == 1
        assert merged[0]["type"] == "權息"
        assert merged[0]["cash_dividend"] == 0.2
        assert merged[0]["stock_dividend"] == 1.6

    def test_different_dates_untouched(self):
        """不同日的 息、權 不併合"""
        div = _div(ex_date="2026-07-15")
        right = _right(ex_date="2026-07-16")

        merged = _merge_same_day_dividend_events([div, right])
        assert len(merged) == 2
        assert {r["type"] for r in merged} == {"息", "權"}

    def test_single_events_untouched(self):
        """一般單一事件原樣保留"""
        div = _div()
        other = _div(code="2330", name="台積電")

        merged = _merge_same_day_dividend_events([div, other])
        assert len(merged) == 2


class TestMergeMoneydjRecords:
    """測試整檔合併（去重 + 同日併權息 + 排序）"""

    def test_dedupes_by_code_exdate_type(self):
        """以 (code, ex_date, type) 去重，新資料覆蓋舊資料"""
        old = [_div(cash_dividend=5.0)]
        new = [_div(cash_dividend=6.15)]

        merged = _merge_moneydj_records(old, new)
        assert len(merged) == 1
        assert merged[0]["cash_dividend"] == 6.15

    def test_fixes_old_data_pair(self):
        """舊檔案中的 息+權 殘留資料在下次合併時被修正為權息"""
        old = [_div(), _right()]
        merged = _merge_moneydj_records(old, [])

        assert len(merged) == 1
        assert merged[0]["type"] == "權息"
        assert merged[0]["cash_dividend"] == 6.15
        assert merged[0]["stock_dividend"] == 0.9

    def test_new_row_merged_with_old_counterpart(self):
        """新爬到的 息 與舊的 權 併成權息"""
        old = [_right()]
        new = [_div()]

        merged = _merge_moneydj_records(old, new)
        assert len(merged) == 1
        assert merged[0]["type"] == "權息"

    def test_sorted_by_ex_date_then_code(self):
        """依 ex_date、code 排序輸出"""
        a = _div(code="2330", name="台積電", ex_date="2026-09-01")
        b = _div(code="0050", name="元大台灣50", ex_date="2026-08-01")

        merged = _merge_moneydj_records([a, b], [])
        assert merged[0]["ex_date"] == "2026-08-01"
        assert merged[1]["ex_date"] == "2026-09-01"