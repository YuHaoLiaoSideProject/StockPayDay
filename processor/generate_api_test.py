"""
單元測試 — generate_api 模組

覆蓋：
- generate_upcoming 日期篩選、所有類型、排序、空結果
- generate_securities_index 完整性
- generate_securities_history 檔案結構、排序
- save_api_file 寫入正確性
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
    load_all_securities,
)


class TestGenerateUpcoming:
    """測試 upcoming.json 產生"""

    def test_filters_future_dividends(self):
        """只包含今天及未來的配息"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "dividend_history": [
                {"year": 2026, "ex_date": yesterday, "cash_dividend": 3.0},
                {"year": 2027, "ex_date": tomorrow, "cash_dividend": 3.5},
            ],
        }]

        upcoming = generate_upcoming(securities, today=today)
        assert len(upcoming) == 1
        assert upcoming[0]["ex_date"] == tomorrow
        assert upcoming[0]["dividend"] == 3.5

    def test_includes_today(self):
        """包含今天（ex_date == today）"""
        today = datetime.now().strftime("%Y-%m-%d")
        securities = [{
            "code": "0056", "name": "元大高股息", "type": "etf",
            "dividend_history": [
                {"year": 2026, "ex_date": today, "cash_dividend": 1.8},
            ],
        }]

        upcoming = generate_upcoming(securities, today=today)
        assert len(upcoming) == 1
        assert upcoming[0]["ex_date"] == today

    def test_includes_all_security_types(self):
        """包含所有證券類型（stock, etf, preferred）"""
        securities = [
            {"code": "2330", "name": "台積電", "type": "stock",
             "dividend_history": [{"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 3.5}]},
            {"code": "0050", "name": "元大台灣50", "type": "etf",
             "dividend_history": [{"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 1.8}]},
            {"code": "7654", "name": "某特別股", "type": "preferred",
             "dividend_history": [{"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 0.95}]},
        ]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert len(upcoming) == 3
        types = {u["type"] for u in upcoming}
        assert types == {"stock", "etf", "preferred"}

    def test_sorted_by_ex_date(self):
        """依 ex_date 升冪排序"""
        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "dividend_history": [
                {"year": 2027, "ex_date": "2099-03-01", "cash_dividend": 3.5},
                {"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 3.0},
            ],
        }]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert upcoming[0]["ex_date"] == "2099-01-01"
        assert upcoming[1]["ex_date"] == "2099-03-01"

    def test_empty_when_all_past(self):
        """所有配息都在過去時回傳空列表"""
        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "dividend_history": [
                {"year": 2020, "ex_date": "2020-07-25", "cash_dividend": 3.0},
            ],
        }]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert len(upcoming) == 0

    def test_empty_securities_list(self):
        """空證券列表回傳空結果"""
        upcoming = generate_upcoming([], today="2026-07-21")
        assert upcoming == []

    def test_no_dividend_history(self):
        """證券無 dividend_history 時不納入"""
        securities = [{
            "code": "9999", "name": "無配息股", "type": "stock",
            "dividend_history": [],
        }]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert len(upcoming) == 0

    def test_missing_fields_defaults(self):
        """缺少 pay_date 等欄位時使用預設值"""
        securities = [{
            "code": "1111", "name": "測試股", "type": "stock",
            "dividend_history": [
                {"year": 2026, "ex_date": "2099-01-01"},
            ],
        }]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert len(upcoming) == 1
        assert upcoming[0]["pay_date"] == ""
        assert upcoming[0]["dividend"] == 0


class TestGenerateSecuritiesIndex:
    """測試 securities-index.json 產生"""

    def test_includes_all_securities(self):
        """包含所有證券的 code 和 name"""
        securities = [
            {"code": "2330", "name": "台積電"},
            {"code": "2317", "name": "鴻海"},
            {"code": "0050", "name": "元大台灣50"},
        ]

        index = generate_securities_index(securities)
        assert len(index) == 3
        codes = {i["code"] for i in index}
        assert codes == {"2330", "2317", "0050"}

    def test_empty_list(self):
        """空列表回傳空索引"""
        index = generate_securities_index([])
        assert index == []

    def test_structure(self):
        """每筆只包含 code 和 name"""
        securities = [{"code": "2330", "name": "台積電", "type": "stock"}]
        index = generate_securities_index(securities)
        assert len(index[0]) == 2
        assert "code" in index[0]
        assert "name" in index[0]


class TestGenerateSecuritiesHistory:
    """測試單股歷史檔案產生"""

    def test_creates_one_file_per_security(self, tmp_path):
        """每支證券一個 JSON 檔案"""
        securities = [{
            "code": "2330",
            "name": "台積電",
            "dividend_history": [
                {"year": 2026, "ex_date": "2026-07-25", "cash_dividend": 3.5},
                {"year": 2025, "ex_date": "2025-07-18", "cash_dividend": 3.2},
            ],
        }]

        generate_securities_history(securities, output_dir=tmp_path)
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
        securities = [{
            "code": "0050",
            "name": "元大台灣50",
            "dividend_history": [
                {"year": 2024, "ex_date": "2024-06-12", "cash_dividend": 1.5},
                {"year": 2026, "ex_date": "2026-07-20", "cash_dividend": 1.8},
                {"year": 2025, "ex_date": "2025-07-15", "cash_dividend": 1.6},
            ],
        }]

        generate_securities_history(securities, output_dir=tmp_path)
        with open(tmp_path / "0050.json") as f:
            data = json.load(f)
        years = [h["year"] for h in data["history"]]
        assert years == [2026, 2025, 2024]

    def test_multiple_securities(self, tmp_path):
        """多支證券各自產生獨立檔案"""
        securities = [
            {"code": "2330", "name": "台積電",
             "dividend_history": [{"year": 2026, "ex_date": "2026-07-25", "cash_dividend": 3.5}]},
            {"code": "2317", "name": "鴻海",
             "dividend_history": [{"year": 2026, "ex_date": "2026-08-15", "cash_dividend": 4.0}]},
        ]

        generate_securities_history(securities, output_dir=tmp_path)
        assert (tmp_path / "2330.json").exists()
        assert (tmp_path / "2317.json").exists()

    def test_empty_history(self, tmp_path):
        """無歷史資料時 history 為空陣列"""
        securities = [{
            "code": "9999", "name": "無資料股",
            "dividend_history": [],
        }]

        generate_securities_history(securities, output_dir=tmp_path)
        with open(tmp_path / "9999.json") as f:
            data = json.load(f)
        assert data["history"] == []


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
