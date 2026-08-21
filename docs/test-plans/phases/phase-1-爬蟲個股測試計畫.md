# 測試計畫：Phase 1 爬蟲（個股）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 1 — 爬蟲（個股） |
| **測試類型** | 單元測試、整合測試 |
| **工具** | pytest |
| **BDD 對應** | 個股配息資料抓取 |

---

## 1. 測試項目

### 1.1 單元測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| parse_dividend_record | 正確解析配息紀錄 | test_twse_stock.py |
| parse_dividend_record 欄位缺失 | 缺失欄位預設值 | test_twse_stock.py |
| save_stock 新增 | 正確寫入新檔案 | test_fetch.py |
| save_stock 更新 | 正確合併歷史資料 | test_fetch.py |
| save_raw | 正確儲存原始資料 | test_fetch.py |

### 1.2 整合測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| fetch_stock_dividends | 回傳正確格式資料 | test_integration.py |
| 完整爬蟲流程 | data/stocks/ 有檔案 | test_integration.py |
| 資料格式驗證 | 包含所有必要欄位 | test_integration.py |

---

## 2. 測試案例

### 2.1 單元測試

```python
# crawler/test_twse_stock.py
import pytest
from sources.twse_stock import TWSEStockCrawler, parse_dividend_record

class TestParseDividendRecord:
    """配息紀錄解析測試"""
    
    def test_parse_normal_record(self):
        """測試正常配息紀錄解析"""
        raw = {
            "stock_code": "2330",
            "stock_name": "台積電",
            "year": 2026,
            "quarter": 2,
            "announce_date": "2026-06-01",
            "ex_date": "2026-07-25",
            "pay_date": "2026-08-15",
            "cash_dividend": 3.5,
            "stock_dividend": 0
        }
        result = parse_dividend_record(raw)
        
        assert result["code"] == "2330"
        assert result["name"] == "台積電"
        assert result["year"] == 2026
        assert result["ex_date"] == "2026-07-25"
        assert result["cash_dividend"] == 3.5
    
    def test_parse_missing_optional_fields(self):
        """測試可選欄位缺失"""
        raw = {
            "stock_code": "2330",
            "stock_name": "台積電"
        }
        result = parse_dividend_record(raw)
        
        assert result["code"] == "2330"
        assert result["cash_dividend"] == 0
        assert result["stock_dividend"] == 0
    
    def test_parse_empty_record(self):
        """測試空紀錄"""
        raw = {}
        result = parse_dividend_record(raw)
        
        assert result["code"] == ""
        assert result["cash_dividend"] == 0

# crawler/test_fetch.py
import pytest
import json
import tempfile
from pathlib import Path
from fetch import save_stock, save_raw

class TestSaveStock:
    """儲存個股資料測試"""
    
    def test_save_new_stock(self, tmp_path):
        """測試儲存新股票"""
        # 設定臨時目錄
        import fetch
        fetch.DATA_DIR = tmp_path
        
        stock_data = {
            "code": "2330",
            "name": "台積電",
            "dividend_history": [
                {"year": 2026, "cash_dividend": 3.5}
            ]
        }
        
        save_stock(stock_data)
        
        filepath = tmp_path / "stocks" / "2330.json"
        assert filepath.exists()
        
        with open(filepath) as f:
            saved = json.load(f)
        assert saved["code"] == "2330"
        assert len(saved["dividend_history"]) == 1
    
    def test_save_stock_merges_history(self, tmp_path):
        """測試合併歷史資料"""
        import fetch
        fetch.DATA_DIR = tmp_path
        
        # 先儲存一笔
        stock_data_2025 = {
            "code": "2330",
            "name": "台積電",
            "dividend_history": [
                {"year": 2025, "cash_dividend": 3.2}
            ]
        }
        save_stock(stock_data_2025)
        
        # 再儲存另一年
        stock_data_2026 = {
            "code": "2330",
            "name": "台積電",
            "dividend_history": [
                {"year": 2026, "cash_dividend": 3.5}
            ]
        }
        save_stock(stock_data_2026)
        
        filepath = tmp_path / "stocks" / "2330.json"
        with open(filepath) as f:
            saved = json.load(f)
        
        assert len(saved["dividend_history"]) == 2
```

### 2.2 整合測試

```python
# crawler/test_integration.py
import pytest
import json
import tempfile
from pathlib import Path
from fetch import main as run_crawler

class TestCrawlerIntegration:
    """爬蟲整合測試"""
    
    def test_full_crawl_creates_files(self, tmp_path):
        """測試完整爬蟲建立檔案"""
        # 使用臨時目錄
        import fetch
        fetch.DATA_DIR = tmp_path
        
        # 執行爬蟲（使用 mock 或真實 API）
        # run_crawler()
        
        # 驗證檔案存在
        stocks_dir = tmp_path / "stocks"
        assert stocks_dir.exists()
        
        # 驗證有資料
        stock_files = list(stocks_dir.glob("*.json"))
        assert len(stock_files) > 0
    
    def test_stock_file_format(self, tmp_path):
        """測試股票檔案格式"""
        import fetch
        fetch.DATA_DIR = tmp_path
        
        # run_crawler()
        
        # 讀取第一支股票
        stocks_dir = tmp_path / "stocks"
        stock_files = list(stocks_dir.glob("*.json"))
        
        if stock_files:
            with open(stock_files[0]) as f:
                stock = json.load(f)
            
            assert "code" in stock
            assert "name" in stock
            assert "dividend_history" in stock
            assert isinstance(stock["dividend_history"], list)
    
    def test_raw_data_saved(self, tmp_path):
        """測試原始資料儲存"""
        import fetch
        fetch.DATA_DIR = tmp_path
        
        # run_crawler()
        
        raw_dir = tmp_path / "raw"
        assert raw_dir.exists()
        
        # 檢查有日期子目錄
        date_dirs = list(raw_dir.iterdir())
        assert len(date_dirs) > 0
```

---

## 3. 測試執行

```bash
# 執行所有測試
pytest crawler/ -v

# 執行特定測試類別
pytest crawler/test_twse_stock.py -v

# 執行特定測試方法
pytest crawler/test_twse_stock.py::TestParseDividendRecord::test_parse_normal_record -v

# 產生覆蓋率報告
pytest crawler/ --cov=crawler --cov-report=html
```

---

## 4. 驗收標準

| 標準 | 目標 |
|------|------|
| 單元測試通過率 | 100% |
| 整合測試通過率 | 100% |
| 測試覆蓋率 | > 80% |
| 爬蟲執行時間 | < 2 分鐘 |
| 資料格式正確 | 100% |

---

## 5. 測試資料

```json
// crawler/tests/fixtures/raw_stock_data.json
{
  "stock_code": "2330",
  "stock_name": "台積電",
  "year": 2026,
  "quarter": 2,
  "announce_date": "2026-06-01",
  "ex_date": "2026-07-25",
  "pay_date": "2026-08-15",
  "cash_dividend": 3.5,
  "stock_dividend": 0
}
```
