"""
單元測試 — generate_api 模組

覆蓋：
- generate_upcoming 日期篩選、所有類型、排序、空結果
- generate_securities_index 完整性、去重
- generate_securities_history 檔案結構、排序
- save_api_file 寫入正確性
- merge_twses_and_mops 合併邏輯
"""
import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from processor.generate_api import (
    generate_upcoming,
    generate_securities_index,
    generate_securities_history,
    save_api_file,
    merge_twses_and_mops,
)


class TestGenerateUpcoming:
    """測試 upcoming.json 產生"""

    def test_filters_future_dividends(self):
        """只包含今天及未來的配息"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        records = [
            {"code": "2330", "name": "台積電", "ex_date": yesterday,
             "type": "息", "cash_dividend": 3.0, "stock_dividend": 0},
            {"code": "2330", "name": "台積電", "ex_date": tomorrow,
             "type": "息", "cash_dividend": 3.5, "stock_dividend": 0},
        ]

        upcoming = generate_upcoming(records, today=today)
        assert len(upcoming) == 1
        assert upcoming[0]["ex_date"] == tomorrow
        assert upcoming[0]["cash_dividend"] == 3.5

    def test_includes_today(self):
        """包含今天（ex_date == today）"""
        today = datetime.now().strftime("%Y-%m-%d")
        records = [
            {"code": "0056", "name": "元大高股息", "ex_date": today,
             "type": "息", "cash_dividend": 1.8, "stock_dividend": 0},
        ]

        upcoming = generate_upcoming(records, today=today)
        assert len(upcoming) == 1
        assert upcoming[0]["ex_date"] == today

    def test_includes_all_types(self):
        """包含所有除權息類型（息、權、權息）"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2099-01-01",
             "type": "息", "cash_dividend": 3.5, "stock_dividend": 0},
            {"code": "2317", "name": "鴻海", "ex_date": "2099-01-01",
             "type": "權", "cash_dividend": 0, "stock_dividend": 0.1},
            {"code": "2454", "name": "聯發科", "ex_date": "2099-01-01",
             "type": "權息", "cash_dividend": 5.0, "stock_dividend": 0.05},
        ]

        upcoming = generate_upcoming(records, today="2026-07-21")
        assert len(upcoming) == 3
        types = {u["type"] for u in upcoming}
        assert types == {"息", "權", "權息"}

    def test_sorted_by_ex_date(self):
        """依 ex_date 升冪排序"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2099-03-01",
             "type": "息", "cash_dividend": 3.5, "stock_dividend": 0},
            {"code": "2317", "name": "鴻海", "ex_date": "2099-01-01",
             "type": "息", "cash_dividend": 4.0, "stock_dividend": 0},
        ]

        upcoming = generate_upcoming(records, today="2026-07-21")
        assert upcoming[0]["ex_date"] == "2099-01-01"
        assert upcoming[1]["ex_date"] == "2099-03-01"

    def test_empty_when_all_past(self):
        """所有配息都在過去時回傳空列表"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2020-07-25",
             "type": "息", "cash_dividend": 3.0, "stock_dividend": 0},
        ]

        upcoming = generate_upcoming(records, today="2026-07-21")
        assert len(upcoming) == 0

    def test_empty_records_list(self):
        """空紀錄列表回傳空結果"""
        upcoming = generate_upcoming([], today="2026-07-21")
        assert upcoming == []

    def test_missing_fields_defaults(self):
        """缺少欄位時使用預設值"""
        records = [
            {"code": "1111", "name": "測試股", "ex_date": "2099-01-01"},
        ]

        upcoming = generate_upcoming(records, today="2026-07-21")
        assert len(upcoming) == 1
        assert upcoming[0]["type"] == "息"
        assert upcoming[0]["cash_dividend"] == 0
        assert upcoming[0]["stock_dividend"] == 0

    def test_includes_stock_dividend(self):
        """包含 stock_dividend 欄位"""
        records = [
            {"code": "1583", "name": "程泰", "ex_date": "2099-01-01",
             "type": "權息", "cash_dividend": 0.1, "stock_dividend": 0.09},
        ]

        upcoming = generate_upcoming(records, today="2026-07-21")
        assert len(upcoming) == 1
        assert upcoming[0]["stock_dividend"] == 0.09

    def test_includes_pay_date(self):
        """包含 pay_date 欄位（來自 MOPS 合併）"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2099-07-25",
             "type": "息", "cash_dividend": 3.5, "stock_dividend": 0,
             "pay_date": "2099-08-15"},
        ]

        upcoming = generate_upcoming(records, today="2026-07-21")
        assert len(upcoming) == 1
        assert upcoming[0]["pay_date"] == "2099-08-15"

    def test_pay_date_defaults_to_empty(self):
        """無 pay_date 時使用空字串"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2099-01-01",
             "type": "息", "cash_dividend": 3.5, "stock_dividend": 0},
        ]

        upcoming = generate_upcoming(records, today="2026-07-21")
        assert upcoming[0]["pay_date"] == ""


class TestGenerateSecuritiesIndex:
    """測試 securities-index.json 產生"""

    def test_includes_all_securities(self):
        """包含所有證券的 code 和 name"""
        records = [
            {"code": "2330", "name": "台積電"},
            {"code": "2317", "name": "鴻海"},
            {"code": "0050", "name": "元大台灣50"},
        ]

        index = generate_securities_index(records)
        assert len(index) == 3
        codes = {i["code"] for i in index}
        assert codes == {"2330", "2317", "0050"}

    def test_empty_list(self):
        """空列表回傳空索引"""
        index = generate_securities_index([])
        assert index == []

    def test_structure(self):
        """每筆只包含 code 和 name"""
        records = [{"code": "2330", "name": "台積電"}]
        index = generate_securities_index(records)
        assert len(index[0]) == 2
        assert "code" in index[0]
        assert "name" in index[0]

    def test_deduplication(self):
        """重複的 code 只保留一筆"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25"},
            {"code": "2330", "name": "台積電", "ex_date": "2025-07-18"},
        ]

        index = generate_securities_index(records)
        assert len(index) == 1
        assert index[0]["code"] == "2330"


class TestGenerateSecuritiesHistory:
    """測試單股歷史檔案產生"""

    def test_creates_one_file_per_security(self, tmp_path):
        """每支證券一個 JSON 檔案"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25",
             "cash_dividend": 3.5, "stock_dividend": 0},
            {"code": "2330", "name": "台積電", "ex_date": "2025-07-18",
             "cash_dividend": 3.2, "stock_dividend": 0},
        ]

        count = generate_securities_history(records, output_dir=tmp_path)
        assert count == 1

        filepath = tmp_path / "2330.json"
        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)
        assert data["code"] == "2330"
        assert data["name"] == "台積電"
        assert len(data["history"]) == 2
        # 應依年份降冪
        assert data["history"][0]["year"] == 2026
        assert data["history"][1]["year"] == 2025

    def test_history_sorted_descending(self, tmp_path):
        """歷史依年份降冪排序"""
        records = [
            {"code": "0050", "name": "元大台灣50", "ex_date": "2024-06-12",
             "cash_dividend": 1.5, "stock_dividend": 0},
            {"code": "0050", "name": "元大台灣50", "ex_date": "2026-07-20",
             "cash_dividend": 1.8, "stock_dividend": 0},
            {"code": "0050", "name": "元大台灣50", "ex_date": "2025-07-15",
             "cash_dividend": 1.6, "stock_dividend": 0},
        ]

        generate_securities_history(records, output_dir=tmp_path)
        with open(tmp_path / "0050.json") as f:
            data = json.load(f)
        years = [h["year"] for h in data["history"]]
        assert years == [2026, 2025, 2024]

    def test_multiple_securities(self, tmp_path):
        """多支證券各自產生獨立檔案"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25",
             "cash_dividend": 3.5, "stock_dividend": 0},
            {"code": "2317", "name": "鴻海", "ex_date": "2026-08-15",
             "cash_dividend": 4.0, "stock_dividend": 0},
        ]

        generate_securities_history(records, output_dir=tmp_path)
        assert (tmp_path / "2330.json").exists()
        assert (tmp_path / "2317.json").exists()

    def test_empty_history(self, tmp_path):
        """無歷史資料時 history 為空陣列"""
        records = [
            {"code": "9999", "name": "無資料股", "ex_date": "",
             "cash_dividend": 0, "stock_dividend": 0},
        ]

        generate_securities_history(records, output_dir=tmp_path)
        with open(tmp_path / "9999.json") as f:
            data = json.load(f)
        assert data["history"] == []

    def test_includes_stock_dividend(self, tmp_path):
        """歷史包含 stock_dividend"""
        records = [
            {"code": "1583", "name": "程泰", "ex_date": "2026-08-26",
             "cash_dividend": 0.1, "stock_dividend": 0.09},
        ]

        generate_securities_history(records, output_dir=tmp_path)
        with open(tmp_path / "1583.json") as f:
            data = json.load(f)
        assert data["history"][0]["stock_dividend"] == 0.09


class TestMergeTwsesAndMops:
    """測試 TWT48U 和 MOPS 資料合併"""

    def test_merge_adds_pay_date(self):
        """MOPS 資料補充 pay_date"""
        twses = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25",
             "type": "息", "cash_dividend": 3.5, "stock_dividend": 0},
        ]
        mops = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25",
             "pay_date": "2026-08-15", "cash_dividend": 3.5},
        ]

        merged = merge_twses_and_mops(twses, mops)
        assert len(merged) == 1
        assert merged[0]["pay_date"] == "2026-08-15"

    def test_merge_without_mops(self):
        """沒有 MOPS 資料時不影響 TWT48U"""
        twses = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25",
             "type": "息", "cash_dividend": 3.5, "stock_dividend": 0},
        ]

        merged = merge_twses_and_mops(twses, [])
        assert len(merged) == 1
        assert "pay_date" not in merged[0]

    def test_merge_empty(self):
        """兩邊都空時回傳空列表"""
        merged = merge_twses_and_mops([], [])
        assert merged == []


class TestSaveApiFile:
    """測試 JSON 檔案寫入"""

    def test_writes_valid_json(self, tmp_path):
        """寫入的檔案可正確解析"""
        data = [{"code": "2330", "name": "台積電"}]
        filepath = save_api_file(data, "test.json", output_dir=tmp_path)
        assert filepath.exists()

        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_returns_path(self, tmp_path):
        """回傳正確的檔案路徑"""
        data = {"key": "value"}
        filepath = save_api_file(data, "check.json", output_dir=tmp_path)
        assert filepath.name == "check.json"
        assert filepath.parent == tmp_path

    def test_creates_directory(self, tmp_path):
        """自動建立不存在的目錄"""
        nested_dir = tmp_path / "nested" / "dir"
        data = [1, 2, 3]
        filepath = save_api_file(data, "deep.json", output_dir=nested_dir)
        assert filepath.exists()
