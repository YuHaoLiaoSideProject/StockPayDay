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
    load_securities,
    load_listings,
    merge_securities_and_announcements,
    load_moneydj,
    DEFAULT_SOURCE,
    SOURCE_REGISTRY,
    get_source,
    build_records,
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

    def test_merges_listings(self):
        """listings 中尚未在索引中的股票會被補充"""
        records = [
            {"code": "2330", "name": "台積電"},
        ]
        listings = [
            {"code": "2330", "name": "台積電"},  # 已存在，不重複
            {"code": "2317", "name": "鴻海"},    # 新增
            {"code": "0050", "name": "元大台灣50"},  # 新增
        ]

        index = generate_securities_index(records, listings)
        assert len(index) == 3
        codes = {i["code"] for i in index}
        assert codes == {"2330", "2317", "0050"}

    def test_listings_only(self):
        """無配息紀錄時，索引完全來自 listings"""
        listings = [
            {"code": "2330", "name": "台積電"},
            {"code": "2317", "name": "鴻海"},
        ]

        index = generate_securities_index([], listings)
        assert len(index) == 2
        codes = {i["code"] for i in index}
        assert codes == {"2330", "2317"}

    def test_sorted_by_code(self):
        """索引依代號排序"""
        records = [
            {"code": "9999", "name": "測試"},
            {"code": "0050", "name": "元大台灣50"},
            {"code": "2330", "name": "台積電"},
        ]

        index = generate_securities_index(records)
        codes = [i["code"] for i in index]
        assert codes == sorted(codes)


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

    def test_creates_empty_history_for_listing_only(self, tmp_path):
        """僅在 listings 的證券也產出檔案（history 為空陣列）"""
        records = [
            {"code": "2330", "name": "台積電", "ex_date": "2099-01-01",
             "cash_dividend": 3.5, "stock_dividend": 0},
        ]
        listings = [
            {"code": "2330", "name": "台積電"},   # 已有紀錄，不重複產空檔
            {"code": "4126", "name": "太醫"},      # 僅在清單 → 空歷史
        ]

        count = generate_securities_history(
            records, output_dir=tmp_path, listings=listings)
        assert count == 2
        assert (tmp_path / "2330.json").exists()

        with open(tmp_path / "4126.json") as f:
            data = json.load(f)
        assert data["code"] == "4126"
        assert data["name"] == "太醫"
        assert data["history"] == []

    def test_no_listings_backward_compatible(self, tmp_path):
        """未傳 listings 時行為不變（不產出清單-only 檔案）"""
        records = []

        count = generate_securities_history(records, output_dir=tmp_path)
        assert count == 0


class TestLoadSecurities:
    """測試基底證券歷史讀取（data/{stocks,etfs,preferred}）"""

    def _write_security(self, data_dir, subdir, code, history):
        sec_dir = data_dir / subdir
        sec_dir.mkdir(parents=True, exist_ok=True)
        (sec_dir / f"{code}.json").write_text(json.dumps({
            "code": code, "name": f"證券{code}", "type": subdir[:-1],
            "dividend_history": history,
        }, ensure_ascii=False), encoding="utf-8")

    def test_flattens_dividend_history(self, tmp_path, monkeypatch):
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
        self._write_security(tmp_path, "stocks", "2330", [
            {"year": 2026, "ex_date": "2026-07-25",
             "pay_date": "2026-08-15", "cash_dividend": 3.5,
             "stock_dividend": 0},
            {"year": 2025, "ex_date": "2025-07-18",
             "pay_date": "2025-08-08", "cash_dividend": 3.2,
             "stock_dividend": 0},
        ])

        records = load_securities()
        assert len(records) == 2
        assert records[0]["code"] == "2330"
        assert records[0]["type"] == "stock"
        assert records[0]["cash_dividend"] == 3.5

    def test_reads_all_subdirs_and_skips_missing(self, tmp_path, monkeypatch):
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
        self._write_security(tmp_path, "stocks", "2330", [
            {"year": 2026, "ex_date": "2026-07-25", "cash_dividend": 3.5}])
        self._write_security(tmp_path, "etfs", "0056", [
            {"year": 2026, "ex_date": "2026-07-20", "cash_dividend": 1.8}])
        # preferred 目錄不存在，應跳過不中斷

        records = load_securities()
        assert len(records) == 2
        types = {r["type"] for r in records}
        assert types == {"stock", "etf"}

    def test_skips_invalid_json(self, tmp_path, monkeypatch):
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
        stocks_dir = tmp_path / "stocks"
        stocks_dir.mkdir(parents=True)
        (stocks_dir / "bad.json").write_text("{not valid", encoding="utf-8")

        assert load_securities() == []


class TestMergeSecuritiesAndAnnouncements:
    """測試基底歷史與最新公告合併"""

    def test_base_history_preserved_with_type(self):
        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "ex_date": "2025-07-18", "pay_date": "2025-08-08",
            "cash_dividend": 3.2, "stock_dividend": 0,
        }]

        merged = merge_securities_and_announcements(securities, [])
        assert len(merged) == 1
        assert merged[0]["type"] == "stock"

    def test_announcement_updates_pay_date_keeps_type(self):
        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "ex_date": "2026-07-25", "pay_date": "",
            "cash_dividend": 3.5, "stock_dividend": 0,
        }]
        announcements = [{
            "code": "2330", "name": "台積電", "type": "息",
            "ex_date": "2026-07-25", "pay_date": "2026-08-15",
            "cash_dividend": 3.5, "stock_dividend": 0,
        }]

        merged = merge_securities_and_announcements(securities, announcements)
        assert len(merged) == 1
        assert merged[0]["pay_date"] == "2026-08-15"
        # 基底 type（stock/etf/preferred）優先於公告的「息/權」標記
        assert merged[0]["type"] == "stock"

    def test_announcement_only_record_added(self):
        announcements = [{
            "code": "00940", "name": "復華台灣科技優息", "type": "etf",
            "ex_date": "2099-01-01", "pay_date": "",
            "cash_dividend": 0.05, "stock_dividend": 0,
        }]

        merged = merge_securities_and_announcements([], announcements)
        assert len(merged) == 1
        assert merged[0]["code"] == "00940"

    def test_skips_empty_ex_date(self):
        securities = [{"code": "2330", "name": "台積電", "type": "stock",
                       "ex_date": "", "cash_dividend": 3.5}]
        merged = merge_securities_and_announcements(securities, [])
        assert merged == []


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


class TestLoadListings:
    """測試證券清單讀取（data/listings/）"""

    def test_reads_listings_files(self, tmp_path, monkeypatch):
        """讀取 listings 目錄下的所有 JSON 檔案"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        listings_dir = tmp_path / "listings"
        listings_dir.mkdir(parents=True)
        (listings_dir / "2026-08.json").write_text(json.dumps({
            "last_updated": "2026-08-22",
            "source": "TWSE",
            "records": [
                {"code": "2330", "name": "台積電", "market": "TWSE"},
                {"code": "2317", "name": "鴻海", "market": "TWSE"},
            ],
        }, ensure_ascii=False), encoding="utf-8")

        listings = load_listings()
        assert len(listings) == 2
        assert listings[0]["code"] == "2330"

    def test_empty_when_no_listings_dir(self, tmp_path, monkeypatch):
        """listings 目錄不存在時回傳空列表"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        listings = load_listings()
        assert listings == []

    def test_skips_invalid_json(self, tmp_path, monkeypatch):
        """跳過無法解析的 JSON 檔案"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        listings_dir = tmp_path / "listings"
        listings_dir.mkdir(parents=True)
        (listings_dir / "bad.json").write_text("{not valid", encoding="utf-8")

        listings = load_listings()
        assert listings == []


class TestLoadMoneydj:
    """測試 MoneyDJ 讀取（data/moneydj/）"""

    def test_reads_all_files(self, tmp_path, monkeypatch):
        """讀取所有月份檔案並攤平紀錄"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        moneydj_dir = tmp_path / "moneydj"
        moneydj_dir.mkdir(parents=True)
        (moneydj_dir / "2026-08.json").write_text(json.dumps({
            "last_updated": "2026-08-23",
            "source": "moneydj",
            "records": [
                {"code": "00679B", "name": "元大美債20年",
                 "ex_date": "2026-08-21", "type": "息",
                 "pay_date": "2026-09-11", "cash_dividend": 0.28,
                 "stock_dividend": 0.0},
            ],
        }, ensure_ascii=False), encoding="utf-8")
        (moneydj_dir / "2026-09.json").write_text(json.dumps({
            "records": [
                {"code": "2330", "name": "台積電",
                 "ex_date": "2026-09-15", "type": "息",
                 "pay_date": "", "cash_dividend": 3.5,
                 "stock_dividend": 0.0},
            ],
        }, ensure_ascii=False), encoding="utf-8")

        records = load_moneydj()
        assert len(records) == 2
        assert records[0]["code"] == "00679B"
        assert records[1]["code"] == "2330"

    def test_dedupes_across_files(self, tmp_path, monkeypatch):
        """跨月份以 (code, ex_date, type) 去重"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        moneydj_dir = tmp_path / "moneydj"
        moneydj_dir.mkdir(parents=True)
        rec = {"code": "0056", "name": "元大高股息",
               "ex_date": "2026-08-20", "type": "息",
               "pay_date": "2026-09-10", "cash_dividend": 1.8,
               "stock_dividend": 0.0}
        (moneydj_dir / "2026-07.json").write_text(
            json.dumps({"records": [rec]}, ensure_ascii=False), encoding="utf-8")
        (moneydj_dir / "2026-08.json").write_text(
            json.dumps({"records": [rec]}, ensure_ascii=False), encoding="utf-8")

        records = load_moneydj()
        assert len(records) == 1

    def test_empty_when_no_dir(self, tmp_path, monkeypatch):
        """目錄不存在時回傳空列表"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        assert load_moneydj() == []

    def test_skips_invalid_json(self, tmp_path, monkeypatch):
        """跳過無法解析的 JSON 檔案"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        moneydj_dir = tmp_path / "moneydj"
        moneydj_dir.mkdir(parents=True)
        (moneydj_dir / "bad.json").write_text("{not valid", encoding="utf-8")

        assert load_moneydj() == []


class TestSourceRegistry:
    """測試可切換資料來源"""

    def test_default_source_is_moneydj(self):
        """預設來源為 moneydj"""
        assert DEFAULT_SOURCE == "moneydj"
        assert "moneydj" in SOURCE_REGISTRY

    def test_registry_contains_all_sources(self):
        """註冊表包含所有可用來源"""
        expected = {
            "moneydj", "twses-mops", "twses",
            "mops", "tpex-etf", "mops-legacy",
        }
        assert set(SOURCE_REGISTRY) == expected

    def test_get_source_known(self):
        """取得已知來源"""
        src = get_source("twses-mops")
        assert src.name == "twses-mops"
        assert src.label
        assert callable(src.build_announcements)

    def test_get_source_unknown_raises(self):
        """未知名稱拋出 ValueError"""
        import pytest
        with pytest.raises(ValueError):
            get_source("no-such-source")

    def test_build_records_with_moneydj(self, tmp_path, monkeypatch):
        """build_records 以指定來源產出合併紀錄"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        moneydj_dir = tmp_path / "moneydj"
        moneydj_dir.mkdir(parents=True)
        (moneydj_dir / "2026-08.json").write_text(json.dumps({
            "records": [
                {"code": "2330", "name": "台積電",
                 "ex_date": "2099-01-01", "type": "息",
                 "pay_date": "2099-02-01", "cash_dividend": 3.5,
                 "stock_dividend": 0.0},
            ],
        }, ensure_ascii=False), encoding="utf-8")

        records = build_records(get_source("moneydj"))
        assert len(records) == 1
        assert records[0]["code"] == "2330"
        assert records[0]["pay_date"] == "2099-02-01"

    def test_build_records_twses_mops_preserves_original(self, tmp_path, monkeypatch):
        """twses-mops 來源保持原組合邏輯（TWT48U 補 pay_date）"""
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

        twses_dir = tmp_path / "twses"
        mops_dir = tmp_path / "mops_dividend"
        twses_dir.mkdir(parents=True)
        mops_dir.mkdir(parents=True)
        (twses_dir / "t.json").write_text(json.dumps({"records": [
            {"code": "2330", "name": "台積電",
             "ex_date": "2099-07-25", "type": "息",
             "cash_dividend": 3.5, "stock_dividend": 0},
        ]}, ensure_ascii=False), encoding="utf-8")
        (mops_dir / "m.json").write_text(json.dumps({"records": [
            {"code": "2330", "name": "台積電",
             "ex_date": "2099-07-25", "pay_date": "2099-08-15",
             "cash_dividend": 3.5},
        ]}, ensure_ascii=False), encoding="utf-8")

        records = build_records(get_source("twses-mops"))
        assert len(records) == 1
        assert records[0]["pay_date"] == "2099-08-15"


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
