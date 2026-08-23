"""
單元測試 — crawler/fetch.py（完整覆蓋）

覆蓋範圍（對應 fetch.py 章節，日後拆檔時可隨之拆分）：
- ensure_dirs 目錄管理
- save_raw / save_stock（MOPS 資料儲存）
- save_twt48u / _merge_twt48u_records（TWT48U 資料儲存）
- get_current_year_quarter（年季工具）
- save_tpex_etf / _merge_tpex_etf_records（TPEx ETF 儲存）
- save_tpex_exright / _merge_tpex_exright_records（TPEx 除權除息儲存）
- save_mops_dividend / _merge_mops_dividend_records / _load_stock_codes_from_listings
- save_moneydj（MoneyDJ 儲存流程）
- save_mops_aggregated（MOPS 聚合輸出）
- fetch_twt48u / fetch_tpex_etf_dividend / fetch_tpex_exright_daily /
  fetch_moneydj_exright / fetch_mops_dividend / fetch_mops / fetch_listing（主流程，mock 爬蟲）
- main / cli（執行流程與 CLI 派發）

MoneyDJ 的純函式（_split_moneydj_events / _merge_moneydj_records /
_merge_same_day_dividend_events）見 test_fetch_moneydj.py。
"""
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

import crawler.fetch as fetch
from crawler.fetch import (
    _load_stock_codes_from_listings,
    _merge_mops_dividend_records,
    _merge_tpex_etf_records,
    _merge_tpex_exright_records,
    _merge_twt48u_records,
    get_current_year_quarter,
    save_moneydj,
    save_mops_aggregated,
    save_mops_dividend,
    save_raw,
    save_stock,
    save_tpex_etf,
    save_tpex_exright,
    save_twt48u,
)

# 供 mock 爬蟲的來源模組
import crawler.sources.moneydj_exright as moneydj_exright_mod
import crawler.sources.mops_dividend as mops_dividend_mod
import crawler.sources.tpex_etf_dividend as tpex_etf_dividend_mod
import crawler.sources.tpex_exright as tpex_exright_mod
import crawler.sources.tpex_listing as tpex_listing_mod
import crawler.sources.twse_listing as twse_listing_mod
import crawler.sources.twse_stock as twse_stock_mod
import crawler.sources.twse_twt48u as twse_twt48u_mod


# ------------------------------------------------------------------
# 測試環境 fixture
# ------------------------------------------------------------------

FIXED_NOW = datetime(2026, 8, 21, 12, 0, 0)


class FakeDatetime:
    """替換 fetch.datetime：固定 now() 回傳 2026-08-21（民國 115 年第 3 季）"""

    @classmethod
    def now(cls) -> datetime:
        return FIXED_NOW


@pytest.fixture
def fetch_env(tmp_path, monkeypatch):
    """
    把 fetch.py 所有 DATA_* 目錄導向 tmp_path，並固定 datetime.now()。
    回傳 fetch 模組供後續斷言 / mock。
    """
    dirs = {
        "DATA_DIR": tmp_path / "data",
        "DATA_TWT48U_DIR": tmp_path / "data" / "twses",
        "DATA_MOPS_DIR": tmp_path / "data" / "mops",
        "DATA_MOPS_DIVIDEND_DIR": tmp_path / "data" / "mops_dividend",
        "DATA_LISTINGS_DIR": tmp_path / "data" / "listings",
        "DATA_TPEX_ETF_DIR": tmp_path / "data" / "tpex_etf",
        "DATA_TPEX_EXRIGHT_DIR": tmp_path / "data" / "tpex_exright",
        "DATA_MONEYDJ_DIR": tmp_path / "data" / "moneydj",
    }
    for name, path in dirs.items():
        monkeypatch.setattr(fetch, name, path)
    monkeypatch.setattr(fetch, "datetime", FakeDatetime)
    # 對應實際流程（main → ensure_dirs → 儲存）：先建立目錄再測
    fetch.ensure_dirs()
    return fetch


def _read_json(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------
# ensure_dirs
# ------------------------------------------------------------------

class TestEnsureDirs:
    def test_creates_all_directories(self, fetch_env, tmp_path):
        """ensure_dirs 建立所有資料目錄"""
        fetch.ensure_dirs()

        expected = [
            tmp_path / "data" / "raw",
            tmp_path / "data" / "stocks",
            tmp_path / "data" / "etfs",
            tmp_path / "data" / "preferred",
            tmp_path / "data" / "twses",
            tmp_path / "data" / "mops",
            tmp_path / "data" / "mops_dividend",
            tmp_path / "data" / "listings",
            tmp_path / "data" / "tpex_etf",
            tmp_path / "data" / "tpex_exright",
            tmp_path / "data" / "moneydj",
        ]
        for path in expected:
            assert path.is_dir(), f"缺少目錄: {path}"


# ------------------------------------------------------------------
# save_raw
# ------------------------------------------------------------------

class TestSaveRaw:
    def test_saves_to_dated_raw_dir(self, fetch_env, tmp_path):
        """存到 data/raw/{date}/{filename}.json 並回傳 Path"""
        path = save_raw([{"code": "2330"}], "sample")

        expected = tmp_path / "data" / "raw" / "2026-08-21" / "sample.json"
        assert path == expected
        assert path.exists()
        assert _read_json(path) == [{"code": "2330"}]

    def test_keeps_existing_extension(self, fetch_env, tmp_path):
        """檔名已含 .json 時不重複附加"""
        path = save_raw([], "sample.json")
        assert path.name == "sample.json"
        assert path.exists()

    def test_appends_extension_when_missing(self, fetch_env, tmp_path):
        """檔名不含 .json 時自動補上"""
        path = save_raw([], "sample")
        assert path.name == "sample.json"

    def test_ensure_ascii_false_keeps_chinese(self, fetch_env, tmp_path):
        """中文以 UTF-8 原樣儲存（ensure_ascii=False）"""
        path = save_raw([{"name": "台積電"}], "sample")
        content = path.read_text(encoding="utf-8")
        assert "台積電" in content


# ------------------------------------------------------------------
# save_stock
# ------------------------------------------------------------------

class TestSaveStock:
    def test_save_new_stock(self, fetch_env, tmp_path):
        """新股票：寫入 data/stocks/{code}.json 並加上 last_updated"""
        stock = {
            "code": "2330",
            "name": "台積電",
            "dividend_history": [
                {"year": 114, "quarter": 2, "cash_dividend": 3.5},
            ],
        }
        path = save_stock(stock)

        assert path == tmp_path / "data" / "stocks" / "2330.json"
        saved = _read_json(path)
        assert saved["code"] == "2330"
        assert saved["name"] == "台積電"
        assert saved["last_updated"] == "2026-08-21"
        assert len(saved["dividend_history"]) == 1

    def test_merges_existing_history(self, fetch_env, tmp_path):
        """更新時與既有歷史合併（不同年季都保留）"""
        path = tmp_path / "data" / "stocks" / "2330.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "code": "2330", "name": "台積電",
            "dividend_history": [
                {"year": 113, "quarter": 4, "cash_dividend": 2.0},
            ],
        }), encoding="utf-8")

        save_stock({
            "code": "2330", "name": "台積電",
            "dividend_history": [
                {"year": 114, "quarter": 2, "cash_dividend": 3.5},
            ],
        })

        saved = _read_json(path)
        quarters = {(h["year"], h["quarter"]) for h in saved["dividend_history"]}
        assert quarters == {(113, 4), (114, 2)}

    def test_dedupes_by_year_quarter_new_wins(self, fetch_env, tmp_path):
        """同 (year, quarter) 以新資料覆蓋、不重複"""
        path = tmp_path / "data" / "stocks" / "2330.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "code": "2330", "name": "台積電",
            "dividend_history": [
                {"year": 114, "quarter": 2, "cash_dividend": 2.0},
            ],
        }), encoding="utf-8")

        save_stock({
            "code": "2330", "name": "台積電",
            "dividend_history": [
                {"year": 114, "quarter": 2, "cash_dividend": 3.5},
            ],
        })

        saved = _read_json(path)
        assert len(saved["dividend_history"]) == 1
        assert saved["dividend_history"][0]["cash_dividend"] == 3.5

    def test_sorted_new_to_old(self, fetch_env, tmp_path):
        """合併後依 (year, quarter) 新到舊排序"""
        save_stock({
            "code": "2330", "name": "台積電",
            "dividend_history": [
                {"year": 113, "quarter": 2, "cash_dividend": 1.0},
                {"year": 114, "quarter": 1, "cash_dividend": 2.0},
                {"year": 114, "quarter": 2, "cash_dividend": 3.0},
            ],
        })

        saved = _read_json(tmp_path / "data" / "stocks" / "2330.json")
        history = saved["dividend_history"]
        assert [(h["year"], h["quarter"]) for h in history] == [
            (114, 2), (114, 1), (113, 2),
        ]

    def test_subfolder_variants(self, fetch_env, tmp_path):
        """subfolder=etfs / preferred 分別寫入對應目錄"""
        for sub in ("etfs", "preferred"):
            save_stock({
                "code": "00679B", "name": "元大美債20年",
                "dividend_history": [],
            }, sub)
            assert (tmp_path / "data" / sub / "00679B.json").exists()

    def test_missing_code_raises(self, fetch_env):
        """缺少 code 應拋 KeyError（檔案合約需含 code）"""
        with pytest.raises(KeyError):
            save_stock({"name": "無代號", "dividend_history": []})


# ------------------------------------------------------------------
# TWT48U 資料儲存
# ------------------------------------------------------------------

class TestMergeTWT48URecords:
    def test_dedupes_by_code_exdate_new_wins(self):
        """以 (code, ex_date) 去重，新資料覆蓋舊資料"""
        old = [{"code": "2330", "ex_date": "2026-08-27", "cash_dividend": 3.0}]
        new = [{"code": "2330", "ex_date": "2026-08-27", "cash_dividend": 3.5}]
        merged = _merge_twt48u_records(old, new)
        assert len(merged) == 1
        assert merged[0]["cash_dividend"] == 3.5

    def test_sorted_by_ex_date(self):
        """依 ex_date 排序輸出"""
        a = {"code": "2330", "ex_date": "2026-09-01"}
        b = {"code": "0050", "ex_date": "2026-08-01"}
        merged = _merge_twt48u_records([a], [b])
        assert merged[0]["ex_date"] == "2026-08-01"
        assert merged[1]["ex_date"] == "2026-09-01"

    def test_empty_old(self):
        """無舊資料時直接回傳新資料"""
        new = [{"code": "2330", "ex_date": "2026-08-27"}]
        assert _merge_twt48u_records([], new) == new


class TestSaveTWT48U:
    def test_groups_by_month_and_writes_files(self, fetch_env, tmp_path):
        """依 ex_date 分月寫檔，回傳 {月份: 路徑}"""
        records = [
            {"code": "2330", "ex_date": "2026-08-27", "cash_dividend": 3.5},
            {"code": "2330", "ex_date": "2026-09-10", "cash_dividend": 3.5},
            {"code": "0050", "ex_date": "2026-09-15", "cash_dividend": 1.5},
        ]
        saved = save_twt48u(records)

        assert set(saved) == {"2026-08", "2026-09"}
        assert saved["2026-08"] == tmp_path / "data" / "twses" / "2026-08.json"
        assert saved["2026-09"] == tmp_path / "data" / "twses" / "2026-09.json"

        aug = _read_json(saved["2026-08"])
        assert aug["last_updated"] == "2026-08-21"
        assert len(aug["records"]) == 1

        sep = _read_json(saved["2026-09"])
        assert len(sep["records"]) == 2

    def test_merges_with_existing_file(self, fetch_env, tmp_path):
        """已存在的月分檔案會合併去重（新覆蓋舊）"""
        month_file = tmp_path / "data" / "twses" / "2026-08.json"
        month_file.parent.mkdir(parents=True, exist_ok=True)
        month_file.write_text(json.dumps({
            "last_updated": "2026-08-20",
            "records": [
                {"code": "2330", "ex_date": "2026-08-27", "cash_dividend": 3.0},
            ],
        }), encoding="utf-8")

        save_twt48u([
            {"code": "2330", "ex_date": "2026-08-27", "cash_dividend": 3.5},
        ])

        saved = _read_json(month_file)
        assert len(saved["records"]) == 1
        assert saved["records"][0]["cash_dividend"] == 3.5

    def test_empty_records_returns_empty_dict(self, fetch_env):
        """無紀錄時不寫任何檔案"""
        assert save_twt48u([]) == {}


# ------------------------------------------------------------------
# 年季工具
# ------------------------------------------------------------------

class TestGetCurrentYearQuarter:
    def test_fixed_now_returns_115_q3(self, fetch_env):
        """固定時間 2026-08-21 → 民國 115 年第 3 季"""
        assert get_current_year_quarter() == (115, 3)

    def test_varied_dates(self, fetch_env, monkeypatch):
        """不同月份對應不同季度"""

        def fake_date(year, month, day):
            monkeypatch.setattr(
                fetch, "datetime",
                type("FakeDT", (), {"now": staticmethod(
                    lambda: datetime(year, month, day))}),
            )
            return get_current_year_quarter()

        assert fake_date(2025, 1, 1) == (114, 1)
        assert fake_date(2025, 12, 31) == (114, 4)
        assert fake_date(2026, 5, 1) == (115, 2)


# ------------------------------------------------------------------
# TPEx ETF 儲存
# ------------------------------------------------------------------

class TestMergeTPExETFRecords:
    def test_dedupes_by_code_exdate_new_wins(self):
        """以 (code, ex_date) 去重，新資料覆蓋舊資料"""
        old = [{"code": "00687B", "ex_date": "2026-08-27", "cash_dividend": 0.2}]
        new = [{"code": "00687B", "ex_date": "2026-08-27", "cash_dividend": 0.3}]
        merged = _merge_tpex_etf_records(old, new)
        assert len(merged) == 1
        assert merged[0]["cash_dividend"] == 0.3

    def test_sorted_by_ex_date(self):
        """依 ex_date 排序輸出"""
        merged = _merge_tpex_etf_records(
            [{"code": "A", "ex_date": "2026-09-01"}],
            [{"code": "B", "ex_date": "2026-08-01"}],
        )
        assert [r["code"] for r in merged] == ["B", "A"]


class TestSaveTPExETF:
    def test_writes_year_file_with_merge(self, fetch_env, tmp_path):
        """寫入 {year}.json 並合併既有資料"""
        year_file = tmp_path / "data" / "tpex_etf" / "115.json"
        year_file.parent.mkdir(parents=True, exist_ok=True)
        year_file.write_text(json.dumps({
            "last_updated": "2026-08-20",
            "records": [{"code": "00687B", "ex_date": "2026-08-27", "cash_dividend": 0.2}],
        }), encoding="utf-8")

        path = save_tpex_etf(
            [{"code": "00687B", "ex_date": "2026-08-27", "cash_dividend": 0.3}],
            115,
        )

        assert path == year_file
        saved = _read_json(year_file)
        assert saved["last_updated"] == "2026-08-21"
        assert len(saved["records"]) == 1
        assert saved["records"][0]["cash_dividend"] == 0.3


# ------------------------------------------------------------------
# TPEx 除權除息儲存
# ------------------------------------------------------------------

class TestMergeTPExExRightRecords:
    def test_dedupes_by_code_exdate_new_wins(self):
        """以 (code, ex_date) 去重，新資料覆蓋舊資料"""
        old = [{"code": "4126", "ex_date": "2026-08-27", "cash_dividend": 2.0}]
        new = [{"code": "4126", "ex_date": "2026-08-27", "cash_dividend": 2.2}]
        merged = _merge_tpex_exright_records(old, new)
        assert len(merged) == 1
        assert merged[0]["cash_dividend"] == 2.2

    def test_sorted_by_ex_date(self):
        """依 ex_date 排序輸出"""
        merged = _merge_tpex_exright_records(
            [{"code": "A", "ex_date": "2026-09-01"}],
            [{"code": "B", "ex_date": "2026-08-01"}],
        )
        assert [r["code"] for r in merged] == ["B", "A"]


class TestSaveTPExExRight:
    def test_groups_by_month(self, fetch_env, tmp_path):
        """依 ex_date 分月寫檔並回傳 {月份: 路徑}"""
        records = [
            {"code": "4126", "ex_date": "2026-08-27", "type": "除息"},
            {"code": "4126", "ex_date": "2026-09-03", "type": "除息"},
        ]
        saved = save_tpex_exright(records)

        assert set(saved) == {"2026-08", "2026-09"}
        aug = _read_json(saved["2026-08"])
        assert aug["last_updated"] == "2026-08-21"
        assert len(aug["records"]) == 1

    def test_merges_with_existing_file(self, fetch_env, tmp_path):
        """既有月分檔案合併去重（新覆蓋舊）"""
        month_file = tmp_path / "data" / "tpex_exright" / "2026-08.json"
        month_file.parent.mkdir(parents=True, exist_ok=True)
        month_file.write_text(json.dumps({
            "records": [{"code": "4126", "ex_date": "2026-08-27", "type": "除息"}],
        }), encoding="utf-8")

        save_tpex_exright([
            {"code": "4126", "ex_date": "2026-08-27", "type": "除權息"},
        ])

        saved = _read_json(month_file)
        assert len(saved["records"]) == 1
        assert saved["records"][0]["type"] == "除權息"


# ------------------------------------------------------------------
# MOPS Dividend 儲存
# ------------------------------------------------------------------

class TestMergeMOPSDividendRecords:
    def test_dedupes_by_code_exdate_new_wins(self):
        """以 (code, ex_date) 去重，新資料覆蓋舊資料"""
        old = [{"code": "2330", "ex_date": "2025-07-25", "cash_dividend": 3.0}]
        new = [{"code": "2330", "ex_date": "2025-07-25", "cash_dividend": 3.5}]
        merged = _merge_mops_dividend_records(old, new)
        assert len(merged) == 1
        assert merged[0]["cash_dividend"] == 3.5

    def test_missing_ex_date_uses_empty(self):
        """缺少 ex_date 時以空字串當 key（不會 KeyError）"""
        old = [{"code": "2330"}]
        new = [{"code": "2330", "note": "無除息日"}]
        merged = _merge_mops_dividend_records(old, new)
        assert len(merged) == 1
        assert "note" in merged[0]

    def test_sorted_by_ex_date_with_missing_first(self):
        """依 ex_date 排序，空字串排最前"""
        merged = _merge_mops_dividend_records(
            [{"code": "A", "ex_date": "2025-09-01"}],
            [{"code": "B"}, {"code": "C", "ex_date": "2025-08-01"}],
        )
        assert [r["code"] for r in merged] == ["B", "C", "A"]


class TestSaveMOPSDividend:
    def test_writes_quarter_file_with_meta(self, fetch_env, tmp_path):
        """寫入 {year}Q{quarter}.json，含 year/quarter/last_updated 中繼資料"""
        records = [
            {"code": "2330", "ex_date": "2025-07-25", "cash_dividend": 3.5},
        ]
        path = save_mops_dividend(records, 114, 2)

        expected = tmp_path / "data" / "mops_dividend" / "114Q2.json"
        assert path == expected
        saved = _read_json(expected)
        assert saved["year"] == 114
        assert saved["quarter"] == 2
        assert saved["last_updated"] == "2026-08-21"
        assert saved["records"][0]["code"] == "2330"

    def test_merges_with_existing_file(self, fetch_env, tmp_path):
        """既有季度檔案合併去重（新覆蓋舊）"""
        q_file = tmp_path / "data" / "mops_dividend" / "114Q2.json"
        q_file.parent.mkdir(parents=True, exist_ok=True)
        q_file.write_text(json.dumps({
            "year": 114, "quarter": 2,
            "records": [{"code": "2330", "ex_date": "2025-07-25", "cash_dividend": 3.0}],
        }), encoding="utf-8")

        save_mops_dividend(
            [{"code": "2330", "ex_date": "2025-07-25", "cash_dividend": 3.5}],
            114, 2,
        )

        saved = _read_json(q_file)
        assert len(saved["records"]) == 1
        assert saved["records"][0]["cash_dividend"] == 3.5


class TestLoadStockCodesFromListings:
    def test_missing_dir_returns_empty(self, fetch_env, monkeypatch, tmp_path):
        """listings 目錄不存在 → 空列表"""
        missing = tmp_path / "no-such-listing-dir"
        monkeypatch.setattr(fetch, "DATA_LISTINGS_DIR", missing)
        assert _load_stock_codes_from_listings() == []

    def test_collects_dedupes_sorts(self, fetch_env, tmp_path):
        """跨檔案收集 code、去重、排序"""
        listing_dir = tmp_path / "data" / "listings"
        listing_dir.mkdir(parents=True, exist_ok=True)
        (listing_dir / "2026-08.json").write_text(json.dumps({
            "records": [{"code": "2330"}, {"code": "0050"}, {"code": ""}],
        }), encoding="utf-8")
        (listing_dir / "2026-08-tpex.json").write_text(json.dumps({
            "records": [{"code": "0050"}, {"code": "4126"}],
        }), encoding="utf-8")

        codes = _load_stock_codes_from_listings()
        assert codes == ["0050", "2330", "4126"]

    def test_skips_invalid_json_with_warning(self, fetch_env, tmp_path, caplog):
        """無法解析的 JSON 檔跳過並記錄 warning"""
        listing_dir = tmp_path / "data" / "listings"
        listing_dir.mkdir(parents=True, exist_ok=True)
        bad_file = listing_dir / "bad.json"
        bad_file.write_text("{invalid json", encoding="utf-8")
        (listing_dir / "ok.json").write_text(json.dumps({
            "records": [{"code": "2330"}],
        }), encoding="utf-8")

        with caplog.at_level(logging.WARNING):
            codes = _load_stock_codes_from_listings()

        assert codes == ["2330"]
        assert any("bad.json" in r.message for r in caplog.records)


# ------------------------------------------------------------------
# MoneyDJ 儲存流程
# ------------------------------------------------------------------

class TestSaveMoneyDJ:
    def _record(self, **kw):
        base = {
            "code": "2330", "name": "台積電",
            "ex_date": "2026-08-01", "ex_rights_date": "",
            "earnings_dividend": 3.5, "reserve_dividend": 0.0,
            "cash_dividend": 3.5, "pay_date": "2026-09-10",
            "earnings_stock": 0.0, "reserve_stock": 0.0,
            "stock_dividend": 0.0,
        }
        base.update(kw)
        return base

    def test_splits_and_groups_by_month(self, fetch_env, tmp_path):
        """拆分事件後依月份寫檔，輸出含 source=moneydj"""
        records = [
            self._record(code="2330", ex_date="2026-08-01"),
            self._record(code="0050", ex_date="2026-08-05"),
            self._record(code="4126", ex_date="2026-09-03"),
        ]
        saved = save_moneydj(records)

        assert set(saved) == {"2026-08", "2026-09"}
        aug = _read_json(saved["2026-08"])
        assert aug["source"] == "moneydj"
        assert aug["last_updated"] == "2026-08-21"
        assert len(aug["records"]) == 2
        assert all(r["type"] == "息" for r in aug["records"])

    def test_same_day_cash_and_stock_combined(self, fetch_env, tmp_path):
        """同日除息+除權 → 權息單筆"""
        rec = self._record(
            ex_date="2026-08-28", ex_rights_date="2026-08-28",
            stock_dividend=1.6, earnings_stock=1.6,
        )
        saved = save_moneydj([rec])
        records = _read_json(saved["2026-08"])["records"]
        assert len(records) == 1
        assert records[0]["type"] == "權息"
        assert records[0]["cash_dividend"] == 3.5
        assert records[0]["stock_dividend"] == 1.6

    def test_merges_with_existing_file(self, fetch_env, tmp_path):
        """既有檔案以 (code, ex_date, type) 去重合併"""
        month_file = tmp_path / "data" / "moneydj" / "2026-08.json"
        month_file.parent.mkdir(parents=True, exist_ok=True)
        month_file.write_text(json.dumps({
            "source": "moneydj",
            "records": [{
                "code": "2330", "name": "台積電", "ex_date": "2026-08-01",
                "type": "息", "earnings_dividend": 3.0,
                "reserve_dividend": 0.0, "cash_dividend": 3.0,
                "pay_date": "", "earnings_stock": 0.0,
                "reserve_stock": 0.0, "stock_dividend": 0.0,
            }],
        }), encoding="utf-8")

        save_moneydj([self._record()])

        saved = _read_json(month_file)
        assert len(saved["records"]) == 1
        assert saved["records"][0]["cash_dividend"] == 3.5


# ------------------------------------------------------------------
# MOPS 聚合輸出
# ------------------------------------------------------------------

class TestSaveMOPSAggregated:
    def test_filters_by_year_quarter(self, fetch_env, tmp_path):
        """只輸出與 (year, quarter) 相符的歷史紀錄"""
        stocks = [{
            "code": "2330", "name": "台積電",
            "dividend_history": [
                {"year": 113, "quarter": 4, "ex_date": "2024-10-01",
                 "pay_date": "2024-11-01", "cash_dividend": 2.0, "stock_dividend": 0.0},
                {"year": 114, "quarter": 2, "ex_date": "2025-07-25",
                 "pay_date": "2025-08-15", "cash_dividend": 3.5, "stock_dividend": 0.0},
            ],
        }]
        path = save_mops_aggregated(stocks, 114, 2)

        expected = tmp_path / "data" / "mops" / "114Q2.json"
        assert path == expected
        saved = _read_json(expected)
        assert saved["year"] == 114
        assert saved["quarter"] == 2
        assert len(saved["records"]) == 1
        assert saved["records"][0] == {
            "code": "2330", "name": "台積電",
            "ex_date": "2025-07-25", "pay_date": "2025-08-15",
            "cash_dividend": 3.5, "stock_dividend": 0.0,
        }

    def test_no_matching_entries_writes_empty_records(self, fetch_env, tmp_path):
        """無相符紀錄時仍寫檔但 records 為空"""
        stocks = [{
            "code": "2330", "name": "台積電",
            "dividend_history": [
                {"year": 113, "quarter": 4, "ex_date": "2024-10-01",
                 "pay_date": "", "cash_dividend": 2.0, "stock_dividend": 0.0},
            ],
        }]
        save_mops_aggregated(stocks, 114, 2)
        saved = _read_json(tmp_path / "data" / "mops" / "114Q2.json")
        assert saved["records"] == []


# ------------------------------------------------------------------
# 主流程（mock 爬蟲）
# ------------------------------------------------------------------

def _mock_crawler_class(fetch_result=None, **kwargs):
    """建立回傳固定結果的 mock 爬蟲類別，並斷言建構參數"""
    crawler_cls = MagicMock()
    crawler_cls.return_value.fetch.return_value = fetch_result
    return crawler_cls


class TestFetchTWT48U:
    def test_success_saves_records(self, fetch_env, tmp_path, caplog, monkeypatch):
        """成功：紀錄依月份儲存"""
        records = [{"code": "2330", "ex_date": "2026-08-27", "cash_dividend": 3.5}]
        crawler_cls = _mock_crawler_class(records)
        monkeypatch.setattr(twse_twt48u_mod, "TWT48UCrawler", crawler_cls)

        with caplog.at_level(logging.INFO):
            fetch.fetch_twt48u()

        crawler_cls.assert_called_once_with(max_retries=3, delay=2.0)
        saved = _read_json(tmp_path / "data" / "twses" / "2026-08.json")
        assert len(saved["records"]) == 1
        assert "TWT48U 完成" in " ".join(r.message for r in caplog.records)

    def test_empty_records_warns(self, fetch_env, caplog, monkeypatch):
        """空資料：警告且不寫檔"""
        monkeypatch.setattr(twse_twt48u_mod, "TWT48UCrawler", _mock_crawler_class([]))
        with caplog.at_level(logging.WARNING):
            fetch.fetch_twt48u()
        assert any("無資料" in r.message for r in caplog.records)

    def test_exception_logs_error(self, fetch_env, caplog, monkeypatch):
        """爬蟲拋例外：記錄錯誤並返回"""
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch.side_effect = Exception("boom")
        monkeypatch.setattr(twse_twt48u_mod, "TWT48UCrawler", crawler_cls)
        with caplog.at_level(logging.ERROR):
            fetch.fetch_twt48u()
        assert any("boom" in r.message for r in caplog.records)


class TestFetchTPExETFDividend:
    def test_success_saves_by_year(self, fetch_env, tmp_path, caplog, monkeypatch):
        """成功：以當前民國年（115）儲存"""
        records = [{"code": "00687B", "ex_date": "2026-08-27", "cash_dividend": 0.3}]
        crawler_cls = _mock_crawler_class(records)
        monkeypatch.setattr(tpex_etf_dividend_mod, "TPExETFDividendCrawler", crawler_cls)

        with caplog.at_level(logging.INFO):
            fetch.fetch_tpex_etf_dividend()

        crawler_cls.assert_called_once_with(max_retries=3, delay=2.0)
        saved = _read_json(tmp_path / "data" / "tpex_etf" / "115.json")
        assert len(saved["records"]) == 1

    def test_empty_warns(self, fetch_env, caplog, monkeypatch):
        monkeypatch.setattr(tpex_etf_dividend_mod, "TPExETFDividendCrawler", _mock_crawler_class([]))
        with caplog.at_level(logging.WARNING):
            fetch.fetch_tpex_etf_dividend()
        assert any("無資料" in r.message for r in caplog.records)

    def test_exception_logs_error(self, fetch_env, caplog, monkeypatch):
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch.side_effect = Exception("boom")
        monkeypatch.setattr(tpex_etf_dividend_mod, "TPExETFDividendCrawler", crawler_cls)
        with caplog.at_level(logging.ERROR):
            fetch.fetch_tpex_etf_dividend()
        assert any("boom" in r.message for r in caplog.records)


class TestFetchTPExExRightDaily:
    def test_success_saves_monthly(self, fetch_env, tmp_path, monkeypatch):
        records = [{"code": "4126", "ex_date": "2026-08-27", "type": "除息"}]
        crawler_cls = _mock_crawler_class(records)
        monkeypatch.setattr(tpex_exright_mod, "TPExExRightCrawler", crawler_cls)

        fetch.fetch_tpex_exright_daily()

        crawler_cls.assert_called_once_with(max_retries=3, delay=2.0)
        saved = _read_json(tmp_path / "data" / "tpex_exright" / "2026-08.json")
        assert len(saved["records"]) == 1

    def test_empty_warns(self, fetch_env, caplog, monkeypatch):
        monkeypatch.setattr(tpex_exright_mod, "TPExExRightCrawler", _mock_crawler_class([]))
        with caplog.at_level(logging.WARNING):
            fetch.fetch_tpex_exright_daily()
        assert any("無資料" in r.message for r in caplog.records)

    def test_exception_logs_error(self, fetch_env, caplog, monkeypatch):
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch.side_effect = Exception("boom")
        monkeypatch.setattr(tpex_exright_mod, "TPExExRightCrawler", crawler_cls)
        with caplog.at_level(logging.ERROR):
            fetch.fetch_tpex_exright_daily()
        assert any("boom" in r.message for r in caplog.records)


class TestFetchMoneyDJExRight:
    def _record(self, **kw):
        base = {
            "code": "2330", "name": "台積電",
            "ex_date": "2026-08-01", "ex_rights_date": "",
            "earnings_dividend": 3.5, "reserve_dividend": 0.0,
            "cash_dividend": 3.5, "pay_date": "2026-09-10",
            "earnings_stock": 0.0, "reserve_stock": 0.0,
            "stock_dividend": 0.0,
        }
        base.update(kw)
        return base

    def test_success_saves_monthly_files(self, fetch_env, tmp_path, monkeypatch):
        records = [self._record()]
        crawler_cls = _mock_crawler_class(records)
        monkeypatch.setattr(moneydj_exright_mod, "MoneyDJExRightCrawler", crawler_cls)

        fetch.fetch_moneydj_exright()

        crawler_cls.assert_called_once_with(max_retries=3, delay=2.0)
        saved = _read_json(tmp_path / "data" / "moneydj" / "2026-08.json")
        assert saved["source"] == "moneydj"
        assert saved["records"][0]["type"] == "息"

    def test_empty_warns(self, fetch_env, caplog, monkeypatch):
        monkeypatch.setattr(moneydj_exright_mod, "MoneyDJExRightCrawler", _mock_crawler_class([]))
        with caplog.at_level(logging.WARNING):
            fetch.fetch_moneydj_exright()
        assert any("無資料" in r.message for r in caplog.records)

    def test_exception_logs_error(self, fetch_env, caplog, monkeypatch):
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch.side_effect = Exception("boom")
        monkeypatch.setattr(moneydj_exright_mod, "MoneyDJExRightCrawler", crawler_cls)
        with caplog.at_level(logging.ERROR):
            fetch.fetch_moneydj_exright()
        assert any("boom" in r.message for r in caplog.records)


class TestFetchMOPSDividend:
    def _write_listings(self, tmp_path, codes):
        listing_dir = tmp_path / "data" / "listings"
        listing_dir.mkdir(parents=True, exist_ok=True)
        (listing_dir / "2026-08.json").write_text(json.dumps({
            "records": [{"code": c} for c in codes],
        }), encoding="utf-8")

    def test_success_passes_codes_and_saves(self, fetch_env, tmp_path, monkeypatch):
        self._write_listings(tmp_path, ["0050", "2330"])
        records = [{"code": "2330", "ex_date": "2025-07-25", "cash_dividend": 3.5}]

        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch_stock_dividends.return_value = records
        monkeypatch.setattr(mops_dividend_mod, "MOPSDividendCrawler", crawler_cls)

        fetch.fetch_mops_dividend(114, 2)

        crawler_cls.assert_called_once_with(max_retries=3, delay=2.0)
        crawler_cls.return_value.fetch_stock_dividends.assert_called_once_with(
            ["0050", "2330"], 114, 2)
        saved = _read_json(tmp_path / "data" / "mops_dividend" / "114Q2.json")
        assert len(saved["records"]) == 1

    def test_no_listings_skips_crawler(self, fetch_env, caplog, monkeypatch):
        """找不到股票清單：警告並提早返回，不呼叫爬蟲"""
        crawler_cls = MagicMock()
        monkeypatch.setattr(mops_dividend_mod, "MOPSDividendCrawler", crawler_cls)

        with caplog.at_level(logging.WARNING):
            fetch.fetch_mops_dividend(114, 2)

        crawler_cls.assert_not_called()
        assert any("找不到股票清單" in r.message for r in caplog.records)

    def test_empty_records_warns(self, fetch_env, tmp_path, caplog, monkeypatch):
        self._write_listings(tmp_path, ["2330"])
        monkeypatch.setattr(
            mops_dividend_mod, "MOPSDividendCrawler",
            MagicMock(return_value=MagicMock(fetch_stock_dividends=Mock(return_value=[]))),
        )
        with caplog.at_level(logging.WARNING):
            fetch.fetch_mops_dividend(114, 2)
        assert any("無資料" in r.message for r in caplog.records)

    def test_exception_logs_error(self, fetch_env, tmp_path, caplog, monkeypatch):
        self._write_listings(tmp_path, ["2330"])
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch_stock_dividends.side_effect = Exception("boom")
        monkeypatch.setattr(mops_dividend_mod, "MOPSDividendCrawler", crawler_cls)
        with caplog.at_level(logging.ERROR):
            fetch.fetch_mops_dividend(114, 2)
        assert any("boom" in r.message for r in caplog.records)


class TestFetchListing:
    def test_both_sources_saved(self, fetch_env, tmp_path, monkeypatch):
        """TWSE + TPEx 清單分別寫入兩個檔案"""
        twse_cls = _mock_crawler_class([{"code": "2330", "name": "台積電"}])
        tpex_cls = _mock_crawler_class([{"code": "4126", "name": "太醫"}])
        monkeypatch.setattr(twse_listing_mod, "TWSEListingCrawler", twse_cls)
        monkeypatch.setattr(tpex_listing_mod, "TPExListingCrawler", tpex_cls)

        fetch.fetch_listing()

        twse_cls.assert_called_once_with(max_retries=3, delay=2.0)
        tpex_cls.assert_called_once_with(max_retries=3, delay=2.0)

        twse_file = tmp_path / "data" / "listings" / "2026-08.json"
        tpex_file = tmp_path / "data" / "listings" / "2026-08-tpex.json"
        assert _read_json(twse_file) == {
            "last_updated": "2026-08-21",
            "source": "TWSE",
            "records": [{"code": "2330", "name": "台積電"}],
        }
        assert _read_json(tpex_file)["source"] == "TPEx"

    def test_twse_fails_tpex_saved(self, fetch_env, tmp_path, caplog, monkeypatch):
        """TWSE 失敗不影響 TPEx 檔案寫出"""
        twse_cls = MagicMock()
        twse_cls.return_value.fetch.side_effect = Exception("twse down")
        tpex_cls = _mock_crawler_class([{"code": "4126", "name": "太醫"}])
        monkeypatch.setattr(twse_listing_mod, "TWSEListingCrawler", twse_cls)
        monkeypatch.setattr(tpex_listing_mod, "TPExListingCrawler", tpex_cls)

        with caplog.at_level(logging.WARNING):
            fetch.fetch_listing()

        assert not (tmp_path / "data" / "listings" / "2026-08.json").exists()
        assert (tmp_path / "data" / "listings" / "2026-08-tpex.json").exists()
        assert any("TWSE 清單爬蟲失敗" in r.message for r in caplog.records)
        assert any("TWSE 清單無資料" in r.message for r in caplog.records)

    def test_both_fail_no_files(self, fetch_env, tmp_path, caplog, monkeypatch):
        """兩邊都失敗：不寫任何檔案"""
        twse_cls = MagicMock()
        twse_cls.return_value.fetch.side_effect = Exception("twse down")
        tpex_cls = MagicMock()
        tpex_cls.return_value.fetch.side_effect = Exception("tpex down")
        monkeypatch.setattr(twse_listing_mod, "TWSEListingCrawler", twse_cls)
        monkeypatch.setattr(tpex_listing_mod, "TPExListingCrawler", tpex_cls)

        with caplog.at_level(logging.WARNING):
            fetch.fetch_listing()

        assert not list((tmp_path / "data" / "listings").glob("*.json"))


class TestFetchMOPS:
    """舊 MOPS 主流程（TWSEStockCrawler）"""

    def _stocks_with_history(self):
        return [
            {
                "code": "2330", "name": "台積電",
                "dividend_history": [
                    {"year": 114, "quarter": 2, "ex_date": "2025-07-25",
                     "pay_date": "2025-08-15", "cash_dividend": 3.5,
                     "stock_dividend": 0.0},
                ],
            },
        ]

    def test_success_saves_raw_stock_aggregated(self, fetch_env, tmp_path, monkeypatch):
        """成功：原始資料、個股基底、聚合資料三種都已儲存"""
        raw_data = [{"code": "2330", "cash_dividend": 3.5}]
        stocks = self._stocks_with_history()
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch_stock_dividends.return_value = (raw_data, stocks)
        monkeypatch.setattr(twse_stock_mod, "TWSEStockCrawler", crawler_cls)

        fetch.fetch_mops(114, 2)

        crawler_cls.assert_called_once_with(max_retries=3, delay=2.0)
        crawler_cls.return_value.fetch_stock_dividends.assert_called_once_with(114, 2)

        # raw
        raw_path = tmp_path / "data" / "raw" / "2026-08-21" / "twse_dividend_114Q2.json"
        assert _read_json(raw_path) == raw_data
        # stock
        stock_path = tmp_path / "data" / "stocks" / "2330.json"
        saved_stock = _read_json(stock_path)
        assert saved_stock["last_updated"] == "2026-08-21"
        assert len(saved_stock["dividend_history"]) == 1
        # aggregated
        agg = _read_json(tmp_path / "data" / "mops" / "114Q2.json")
        assert agg["records"][0]["ex_date"] == "2025-07-25"

    def test_empty_raw_data_warns(self, fetch_env, tmp_path, caplog, monkeypatch):
        """raw_data 為空：警告並提早返回，不儲存"""
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch_stock_dividends.return_value = ([], [])
        monkeypatch.setattr(twse_stock_mod, "TWSEStockCrawler", crawler_cls)

        with caplog.at_level(logging.WARNING):
            fetch.fetch_mops(114, 2)

        assert any("本次抓取無資料" in r.message for r in caplog.records)
        assert not (tmp_path / "data" / "mops" / "114Q2.json").exists()

    def test_stock_save_failure_isolated(self, fetch_env, tmp_path, caplog, monkeypatch):
        """單一個股儲存失敗不中斷其餘個股與聚合輸出"""
        good_stock = self._stocks_with_history()[0]
        bad_stock = {"name": "缺 code", "dividend_history": []}  # save_stock 會 KeyError
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch_stock_dividends.return_value = (
            [{"code": "2330"}], [good_stock, bad_stock],
        )
        monkeypatch.setattr(twse_stock_mod, "TWSEStockCrawler", crawler_cls)

        with caplog.at_level(logging.ERROR):
            fetch.fetch_mops(114, 2)

        assert (tmp_path / "data" / "stocks" / "2330.json").exists()
        assert (tmp_path / "data" / "mops" / "114Q2.json").exists()
        assert any("儲存個股" in r.message and "失敗" in r.message
                   for r in caplog.records)

    def test_aggregate_save_failure_logged(self, fetch_env, tmp_path, caplog, monkeypatch):
        """聚合資料儲存失敗：記錄錯誤（個股儲存不受影響）"""
        stocks = self._stocks_with_history()
        crawler_cls = MagicMock()
        crawler_cls.return_value.fetch_stock_dividends.return_value = (["raw"], stocks)
        monkeypatch.setattr(twse_stock_mod, "TWSEStockCrawler", crawler_cls)
        monkeypatch.setattr(
            fetch, "save_mops_aggregated", Mock(side_effect=Exception("agg boom")))

        with caplog.at_level(logging.ERROR):
            fetch.fetch_mops(114, 2)

        assert (tmp_path / "data" / "stocks" / "2330.json").exists()
        assert any("儲存 MOPS 聚合資料失敗" in r.message for r in caplog.records)


# ------------------------------------------------------------------
# main 執行流程
# ------------------------------------------------------------------

class TestMain:
    def _patch_all_fetchers(self, fetch_env, monkeypatch):
        """mock 所有 fetch_* 並回傳 dict"""
        mocks = {}
        for name in ("fetch_twt48u", "fetch_tpex_etf_dividend",
                     "fetch_tpex_exright_daily", "fetch_moneydj_exright",
                     "fetch_listing", "fetch_mops_dividend"):
            m = Mock()
            mocks[name] = m
            monkeypatch.setattr(fetch, name, m)
        return mocks

    def test_all_sources_with_explicit_year_quarter(self, fetch_env, monkeypatch):
        """all_sources + 指定年季：依序執行所有來源"""
        mocks = self._patch_all_fetchers(fetch_env, monkeypatch)
        fetch.main(114, 2, all_sources=True)

        for name, m in mocks.items():
            if name == "fetch_mops_dividend":
                m.assert_called_once_with(114, 2)
            else:
                m.assert_called_once_with()

    def test_all_sources_auto_detect_year_quarter(self, fetch_env, monkeypatch):
        """all_sources + 未指定年季：自動偵測（假時間 → 115, 3）"""
        mocks = self._patch_all_fetchers(fetch_env, monkeypatch)
        fetch.main(all_sources=True)

        mocks["fetch_mops_dividend"].assert_called_once_with(115, 3)

    def test_listing_only(self, fetch_env, monkeypatch):
        mocks = self._patch_all_fetchers(fetch_env, monkeypatch)
        fetch.main(listing_only=True)
        mocks["fetch_listing"].assert_called_once_with()
        for name in ("fetch_twt48u", "fetch_tpex_etf_dividend",
                     "fetch_tpex_exright_daily", "fetch_moneydj_exright",
                     "fetch_mops_dividend"):
            mocks[name].assert_not_called()

    def test_twt48u_only(self, fetch_env, monkeypatch):
        mocks = self._patch_all_fetchers(fetch_env, monkeypatch)
        fetch.main(twt48u_only=True)
        mocks["fetch_twt48u"].assert_called_once_with()
        for name in ("fetch_tpex_etf_dividend", "fetch_tpex_exright_daily",
                     "fetch_moneydj_exright", "fetch_listing",
                     "fetch_mops_dividend"):
            mocks[name].assert_not_called()

    def test_mops_only_explicit(self, fetch_env, monkeypatch):
        mocks = self._patch_all_fetchers(fetch_env, monkeypatch)
        fetch.main(114, 2, mops_only=True)
        mocks["fetch_mops_dividend"].assert_called_once_with(114, 2)
        for name in ("fetch_twt48u", "fetch_tpex_etf_dividend",
                     "fetch_tpex_exright_daily", "fetch_moneydj_exright",
                     "fetch_listing"):
            mocks[name].assert_not_called()

    def test_mops_only_auto_detect(self, fetch_env, monkeypatch):
        mocks = self._patch_all_fetchers(fetch_env, monkeypatch)
        fetch.main(mops_only=True)
        mocks["fetch_mops_dividend"].assert_called_once_with(115, 3)

    def test_default_moneydj_and_listing(self, fetch_env, monkeypatch):
        mocks = self._patch_all_fetchers(fetch_env, monkeypatch)
        fetch.main()

        mocks["fetch_moneydj_exright"].assert_called_once_with()
        mocks["fetch_listing"].assert_called_once_with()
        for name in ("fetch_twt48u", "fetch_tpex_etf_dividend",
                     "fetch_tpex_exright_daily", "fetch_mops_dividend"):
            mocks[name].assert_not_called()

    def test_ensure_dirs_called(self, fetch_env, tmp_path, monkeypatch):
        """main 會先呼叫 ensure_dirs"""
        self._patch_all_fetchers(fetch_env, monkeypatch)
        # 移除 fixture 以外的預建目錄，驗證 main 會重建
        import shutil
        shutil.rmtree(tmp_path / "data" / "stocks")
        fetch.main()
        assert (tmp_path / "data" / "stocks").is_dir()


# ------------------------------------------------------------------
# CLI 派發
# ------------------------------------------------------------------

class TestCli:
    def _patch_cli_deps(self, fetch_env, monkeypatch):
        """mock cli 依賴的函式"""
        main_mock = Mock()
        tpex_etf_mock = Mock()
        moneydj_mock = Mock()
        ensure_dirs_mock = Mock()
        monkeypatch.setattr(fetch, "main", main_mock)
        monkeypatch.setattr(fetch, "fetch_tpex_etf_dividend", tpex_etf_mock)
        monkeypatch.setattr(fetch, "fetch_moneydj_exright", moneydj_mock)
        monkeypatch.setattr(fetch, "ensure_dirs", ensure_dirs_mock)
        return main_mock, tpex_etf_mock, moneydj_mock, ensure_dirs_mock

    def test_no_args_default(self, fetch_env, monkeypatch):
        main_mock, tpex_etf_mock, moneydj_mock, _ = self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli([])
        main_mock.assert_called_once_with(
            year=None, quarter=None,
            twt48u_only=False, mops_only=False,
            listing_only=False, all_sources=False,
        )
        tpex_etf_mock.assert_not_called()
        moneydj_mock.assert_not_called()

    def test_year_quarter_positional(self, fetch_env, monkeypatch):
        main_mock, _, _, _ = self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli(["114", "2"])
        main_mock.assert_called_once_with(
            year=114, quarter=2,
            twt48u_only=False, mops_only=False,
            listing_only=False, all_sources=False,
        )

    def test_twt48u_flag(self, fetch_env, monkeypatch):
        main_mock, _, _, _ = self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli(["--twt48u"])
        main_mock.assert_called_once_with(
            year=None, quarter=None,
            twt48u_only=True, mops_only=False,
            listing_only=False, all_sources=False,
        )

    def test_mops_flag_with_year_quarter(self, fetch_env, monkeypatch):
        main_mock, _, _, _ = self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli(["--mops", "114", "2"])
        main_mock.assert_called_once_with(
            year=114, quarter=2,
            twt48u_only=False, mops_only=True,
            listing_only=False, all_sources=False,
        )

    def test_listing_flag(self, fetch_env, monkeypatch):
        main_mock, _, _, _ = self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli(["--listing"])
        main_mock.assert_called_once_with(
            year=None, quarter=None,
            twt48u_only=False, mops_only=False,
            listing_only=True, all_sources=False,
        )

    def test_all_flag(self, fetch_env, monkeypatch):
        main_mock, _, _, _ = self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli(["--all"])
        main_mock.assert_called_once_with(
            year=None, quarter=None,
            twt48u_only=False, mops_only=False,
            listing_only=False, all_sources=True,
        )

    def test_tpex_etf_flag_direct_dispatch(self, fetch_env, monkeypatch):
        """--tpex-etf 直接呼叫 fetch_tpex_etf_dividend，不經過 main"""
        main_mock, tpex_etf_mock, moneydj_mock, ensure_dirs_mock = \
            self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli(["--tpex-etf"])
        ensure_dirs_mock.assert_called_once_with()
        tpex_etf_mock.assert_called_once_with()
        moneydj_mock.assert_not_called()
        main_mock.assert_not_called()

    def test_moneydj_flag_direct_dispatch(self, fetch_env, monkeypatch):
        """--moneydj 直接呼叫 fetch_moneydj_exright，不經過 main"""
        main_mock, tpex_etf_mock, moneydj_mock, ensure_dirs_mock = \
            self._patch_cli_deps(fetch_env, monkeypatch)
        fetch.cli(["--moneydj"])
        ensure_dirs_mock.assert_called_once_with()
        moneydj_mock.assert_called_once_with()
        tpex_etf_mock.assert_not_called()
        main_mock.assert_not_called()

    def test_year_without_quarter_exits(self, fetch_env, monkeypatch):
        self._patch_cli_deps(fetch_env, monkeypatch)
        with pytest.raises(SystemExit) as exc:
            fetch.cli(["114"])
        assert exc.value.code == 2

    def test_invalid_quarter_exits(self, fetch_env, monkeypatch):
        self._patch_cli_deps(fetch_env, monkeypatch)
        with pytest.raises(SystemExit) as exc:
            fetch.cli(["--mops", "114", "5"])
        assert exc.value.code == 2