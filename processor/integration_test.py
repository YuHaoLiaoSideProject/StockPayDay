"""
整合測試 — 完整處理器流程

測試 data/ → processor → api/ 的端到端流程。
資料來源可切換：預設 moneydj；既有測試沿用原組合邏輯（twses-mops）。
"""
import pytest
import json
import time
from pathlib import Path
from processor.generate_api import main as run_processor


def _write_twses(data_dir: Path, records: list) -> None:
    """輔助：寫入 TWT48U 格式的測試資料"""
    twses_dir = data_dir / "twses"
    twses_dir.mkdir(parents=True, exist_ok=True)
    (twses_dir / "test.json").write_text(
        json.dumps({"records": records}, ensure_ascii=False)
    )


def _write_moneydj(data_dir: Path, month: str, records: list) -> None:
    """輔助：寫入 MoneyDJ 格式的測試資料（data/moneydj/{month}.json）"""
    moneydj_dir = data_dir / "moneydj"
    moneydj_dir.mkdir(parents=True, exist_ok=True)
    (moneydj_dir / f"{month}.json").write_text(
        json.dumps({
            "last_updated": "2026-08-23",
            "source": "moneydj",
            "records": records,
        }, ensure_ascii=False)
    )


def _load_all_dividends(api_dir: Path) -> list:
    """輔助：讀取所有 dividends/*.json（排除 index.json）並合併為一維列表"""
    dividends_dir = api_dir / "dividends"
    if not dividends_dir.exists():
        return []
    all_records = []
    for f in sorted(dividends_dir.glob("*.json")):
        if f.name == "index.json":
            continue
        with open(f) as fh:
            all_records.extend(json.load(fh))
    return all_records


class TestProcessorIntegration:
    """處理器整合測試"""

    def test_full_process(self, tmp_path, monkeypatch):
        """完整處理流程（twses-mops 來源）：api/ 產出所有檔案"""
        data_dir = tmp_path / "data"
        _write_twses(data_dir, [
            {
                "code": "2330", "name": "台積電",
                "ex_date": "2099-01-01", "type": "息",
                "cash_dividend": 3.5, "stock_dividend": 0,
            },
            {
                "code": "0050", "name": "元大台灣50",
                "ex_date": "2099-06-15", "type": "息",
                "cash_dividend": 1.8, "stock_dividend": 0,
            },
        ])

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        run_processor("twses-mops")

        api_dir = tmp_path / "api"
        assert (api_dir / "dividends").exists()
        assert (api_dir / "securities-index.json").exists()
        assert (api_dir / "securities").exists()
        assert (api_dir / "securities" / "2330.json").exists()
        assert (api_dir / "securities" / "0050.json").exists()

    def test_json_format_valid(self, tmp_path, monkeypatch):
        """所有產出的 JSON 檔案格式正確（twses-mops 來源）"""
        data_dir = tmp_path / "data"
        _write_twses(data_dir, [
            {
                "code": "0050", "name": "元大台灣50",
                "ex_date": "2099-01-01", "type": "息",
                "cash_dividend": 1.8, "stock_dividend": 0,
            },
        ])

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        run_processor("twses-mops")

        api_dir = tmp_path / "api"
        for json_file in api_dir.rglob("*.json"):
            with open(json_file) as f:
                data = json.load(f)  # 不拋出異常即為成功

        # 驗證 dividends/*.json 結構
        dividends = _load_all_dividends(api_dir)
        assert len(dividends) == 1
        item = dividends[0]
        assert "code" in item
        assert "name" in item
        assert "type" in item
        assert "ex_date" in item
        assert "pay_date" in item
        assert "cash_dividend" in item
        assert "stock_dividend" in item

        # 驗證 securities-index.json 結構
        with open(api_dir / "securities-index.json") as f:
            index = json.load(f)
        assert isinstance(index, list)
        assert len(index) == 1
        assert "code" in index[0]
        assert "name" in index[0]

        # 驗證 securities/{code}.json 結構
        with open(api_dir / "securities" / "0050.json") as f:
            hist = json.load(f)
        assert hist["code"] == "0050"
        assert "history" in hist
        assert isinstance(hist["history"], list)

    def test_processing_time(self, tmp_path, monkeypatch):
        """處理時間 < 30 秒（twses-mops 來源）"""
        data_dir = tmp_path / "data"
        twses_dir = data_dir / "twses"
        twses_dir.mkdir(parents=True)

        # 產生 100 支測試證券
        records = []
        for i in range(100):
            records.append({
                "code": f"{i:04d}", "name": f"測試證券{i}",
                "ex_date": "2099-01-01", "type": "息",
                "cash_dividend": round(1.0 + i * 0.1, 1), "stock_dividend": 0,
            })
        (twses_dir / "test.json").write_text(
            json.dumps({"records": records}, ensure_ascii=False)
        )

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        start = time.time()
        run_processor("twses-mops")
        elapsed = time.time() - start

        assert elapsed < 30, f"處理時間 {elapsed:.1f}s 超過 30 秒上限"

    def test_empty_data_no_crash(self, tmp_path, monkeypatch):
        """data/ 目錄為空時不崩潰（twses-mops 來源）"""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        # 不應拋出異常
        run_processor("twses-mops")

    def test_missing_subdir_no_crash(self, tmp_path, monkeypatch):
        """部分子目錄不存在時不崩潰（twses-mops 來源）"""
        data_dir = tmp_path / "data"
        # 只建立 twses，不建立 mops
        _write_twses(data_dir, [
            {
                "code": "1234", "name": "測試股",
                "ex_date": "2099-01-01", "type": "息",
                "cash_dividend": 2.0, "stock_dividend": 0,
            },
        ])

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        run_processor("twses-mops")

        api_dir = tmp_path / "api"
        assert (api_dir / "dividends").exists()

    def test_mops_merge_populates_pay_date(self, tmp_path, monkeypatch):
        """MOPS（新 API）資料補充 pay_date 至 dividends（twses-mops 來源）"""
        data_dir = tmp_path / "data"
        twses_dir = data_dir / "twses"
        mops_dir = data_dir / "mops_dividend"
        twses_dir.mkdir(parents=True)
        mops_dir.mkdir(parents=True)

        (twses_dir / "test.json").write_text(json.dumps({"records": [
            {
                "code": "2330", "name": "台積電",
                "ex_date": "2099-07-25", "type": "息",
                "cash_dividend": 3.5, "stock_dividend": 0,
            },
        ]}, ensure_ascii=False))

        (mops_dir / "test.json").write_text(json.dumps({"records": [
            {
                "code": "2330", "name": "台積電",
                "ex_date": "2099-07-25", "pay_date": "2099-08-15",
                "cash_dividend": 3.5,
            },
        ]}, ensure_ascii=False))

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        run_processor("twses-mops")

        dividends = _load_all_dividends(tmp_path / "api")
        assert len(dividends) == 1
        assert dividends[0]["pay_date"] == "2099-08-15"

    def test_moneydj_default_source(self, tmp_path, monkeypatch):
        """預設來源 moneydj：data/moneydj 產生 dividends"""
        data_dir = tmp_path / "data"
        _write_moneydj(data_dir, "2026-08", [
            {
                "code": "00679B", "name": "元大美債20年",
                "ex_date": "2099-09-11", "type": "息",
                "pay_date": "2099-09-11",
                "cash_dividend": 0.28, "stock_dividend": 0.0,
            },
        ])

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        # 不帶來源參數 → 使用預設 moneydj
        run_processor()

        api_dir = tmp_path / "api"
        assert (api_dir / "dividends").exists()
        dividends = _load_all_dividends(api_dir)
        assert len(dividends) == 1
        assert dividends[0]["code"] == "00679B"
        assert dividends[0]["pay_date"] == "2099-09-11"
        assert dividends[0]["cash_dividend"] == 0.28

    def test_moneydj_source_switch(self, tmp_path, monkeypatch):
        """顯式切換到 twses-mops 來源：moneydj 資料不被使用"""
        data_dir = tmp_path / "data"
        _write_twses(data_dir, [
            {
                "code": "2330", "name": "台積電",
                "ex_date": "2099-01-01", "type": "息",
                "cash_dividend": 3.5, "stock_dividend": 0,
            },
        ])
        _write_moneydj(data_dir, "2026-08", [
            {
                "code": "00679B", "name": "元大美債20年",
                "ex_date": "2099-09-11", "type": "息",
                "pay_date": "2099-09-11",
                "cash_dividend": 0.28, "stock_dividend": 0.0,
            },
        ])

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        run_processor("twses-mops")

        dividends = _load_all_dividends(tmp_path / "api")
        codes = [d["code"] for d in dividends]
        assert "2330" in codes
        assert "00679B" not in codes

    def test_unknown_source_raises(self):
        """未知來源名稱拋出 ValueError"""
        import processor.generate_api as mod
        with pytest.raises(ValueError):
            run_processor("not-a-source")
