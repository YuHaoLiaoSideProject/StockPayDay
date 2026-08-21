"""
整合測試 — 完整處理器流程

測試 data/ → processor → api/ 的端到端流程
"""
import pytest
import json
import time
from pathlib import Path
from processor.generate_api import main as run_processor


class TestProcessorIntegration:
    """處理器整合測試"""

    def test_full_process(self, tmp_path, monkeypatch):
        """完整處理流程：api/ 產出所有檔案"""
        # 準備 data/ 目錄結構
        data_dir = tmp_path / "data"
        for subdir in ["stocks", "etfs", "preferred"]:
            (data_dir / subdir).mkdir(parents=True)

        # 寫入測試資料
        test_stock = {
            "code": "2330", "name": "台積電", "type": "stock",
            "dividend_history": [
                {"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 3.5},
            ],
        }
        (data_dir / "stocks" / "2330.json").write_text(json.dumps(test_stock))

        test_etf = {
            "code": "0050", "name": "元大台灣50", "type": "etf",
            "dividend_history": [
                {"year": 2026, "ex_date": "2099-06-15", "cash_dividend": 1.8},
            ],
        }
        (data_dir / "etfs" / "0050.json").write_text(json.dumps(test_etf))

        # monkeypatch 路徑
        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        # 執行處理器
        run_processor()

        # 驗證 api/ 檔案
        api_dir = tmp_path / "api"
        assert (api_dir / "upcoming.json").exists()
        assert (api_dir / "securities-index.json").exists()
        assert (api_dir / "securities").exists()
        assert (api_dir / "securities" / "2330.json").exists()
        assert (api_dir / "securities" / "0050.json").exists()

    def test_json_format_valid(self, tmp_path, monkeypatch):
        """所有產出的 JSON 檔案格式正確"""
        data_dir = tmp_path / "data"
        stocks_dir = data_dir / "stocks"
        stocks_dir.mkdir(parents=True)

        test_data = {
            "code": "0050", "name": "元大台灣50", "type": "etf",
            "dividend_history": [
                {"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 1.8},
            ],
        }
        (stocks_dir / "0050.json").write_text(json.dumps(test_data))

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        run_processor()

        # 驗證每個 JSON 都可解析
        api_dir = tmp_path / "api"
        for json_file in api_dir.rglob("*.json"):
            with open(json_file) as f:
                data = json.load(f)  # 不拋出異常即為成功

        # 驗證 upcoming.json 結構
        with open(api_dir / "upcoming.json") as f:
            upcoming = json.load(f)
        assert isinstance(upcoming, list)
        assert len(upcoming) == 1
        item = upcoming[0]
        assert "code" in item
        assert "name" in item
        assert "type" in item
        assert "ex_date" in item
        assert "pay_date" in item
        assert "dividend" in item

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
        """處理時間 < 30 秒"""
        data_dir = tmp_path / "data"
        stocks_dir = data_dir / "stocks"
        stocks_dir.mkdir(parents=True)

        # 產生 100 支測試證券
        for i in range(100):
            test_data = {
                "code": f"{i:04d}",
                "name": f"測試證券{i}",
                "dividend_history": [
                    {"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 1.0 + i * 0.1},
                ],
            }
            (stocks_dir / f"{i:04d}.json").write_text(json.dumps(test_data))

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        start = time.time()
        run_processor()
        elapsed = time.time() - start

        assert elapsed < 30, f"處理時間 {elapsed:.1f}s 超過 30 秒上限"

    def test_empty_data_no_crash(self, tmp_path, monkeypatch):
        """data/ 目錄為空時不崩潰"""
        data_dir = tmp_path / "data"
        for subdir in ["stocks", "etfs", "preferred"]:
            (data_dir / subdir).mkdir(parents=True)

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        # 不應拋出異常
        run_processor()

    def test_missing_subdir_no_crash(self, tmp_path, monkeypatch):
        """部分子目錄不存在時不崩潰"""
        data_dir = tmp_path / "data"
        # 只建立 stocks，不建立 etfs 和 preferred
        (data_dir / "stocks").mkdir(parents=True)

        test_data = {
            "code": "1234", "name": "測試股", "type": "stock",
            "dividend_history": [
                {"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 2.0},
            ],
        }
        (data_dir / "stocks" / "1234.json").write_text(json.dumps(test_data))

        import processor.generate_api as mod
        monkeypatch.setattr(mod, "DATA_DIR", data_dir)
        monkeypatch.setattr(mod, "API_DIR", tmp_path / "api")

        run_processor()

        # 應正常產出
        api_dir = tmp_path / "api"
        assert (api_dir / "upcoming.json").exists()
