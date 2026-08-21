# 測試計畫：Phase 3 資料處理器

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 3 — 資料處理器 |
| **測試類型** | 單元測試、整合測試 |
| **工具** | pytest |
| **BDD 對應** | 資料轉換、API 檔案產出 |

---

## 1. 測試項目

### 1.1 單元測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| generate_upcoming | 只包含未來配息 | test_generate_api.py |
| generate_upcoming 篩選日期 | ex_date >= 今天 | test_generate_api.py |
| generate_securities_index | 包含所有證券 | test_generate_api.py |
| generate_securities_history | 每支一個檔案 | test_generate_api.py |
| save_api_file | 正確寫入 JSON | test_generate_api.py |

### 1.2 整合測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| 完整處理流程 | api/ 有所有檔案 | test_integration.py |
| 資料格式驗證 | JSON 格式正確 | test_integration.py |
| 處理時間 | < 30 秒 | test_integration.py |

---

## 2. 測試案例

### 2.1 單元測試

```python
# processor/test_generate_api.py
import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from generate_api import (
    generate_upcoming,
    generate_securities_index,
    generate_securities_history
)

class TestGenerateUpcoming:
    """測試 upcoming.json 產生"""
    
    def test_filters_future_dividends(self, tmp_path):
        """測試只包含未來配息"""
        # 準備測試資料
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        stocks_data = [
            {
                "code": "2330",
                "name": "台積電",
                "dividend_history": [
                    {"year": 2026, "ex_date": yesterday, "cash_dividend": 3.0},  # 過去
                    {"year": 2027, "ex_date": tomorrow, "cash_dividend": 3.5}   # 未來
                ]
            }
        ]
        
        upcoming = generate_upcoming(stocks_data)
        
        # 只應包含未來配息
        assert len(upcoming) == 1
        assert upcoming[0]["ex_date"] == tomorrow
    
    def test_includes_all_security_types(self):
        """測試包含所有證券類型"""
        stocks_data = [
            {"code": "2330", "name": "台積電", "type": "stock",
             "dividend_history": [{"year": 2026, "ex_date": "2027-01-01", "cash_dividend": 3.5}]}
        ]
        etfs_data = [
            {"code": "0050", "name": "元大台灣50", "type": "etf",
             "dividend_history": [{"year": 2026, "ex_date": "2027-01-01", "cash_dividend": 1.8}]}
        ]
        
        upcoming = generate_upcoming(stocks_data + etfs_data)
        
        assert len(upcoming) == 2
        types = [u["type"] for u in upcoming]
        assert "stock" in types
        assert "etf" in types

class TestGenerateSecuritiesIndex:
    """測試 securities-index.json 產生"""
    
    def test_includes_all_securities(self):
        """測試包含所有證券"""
        stocks_data = [
            {"code": "2330", "name": "台積電"},
            {"code": "2317", "name": "鴻海"}
        ]
        etfs_data = [
            {"code": "0050", "name": "元大台灣50"}
        ]
        
        index = generate_securities_index(stocks_data + etfs_data)
        
        assert len(index) == 3
        codes = [i["code"] for i in index]
        assert "2330" in codes
        assert "0050" in codes

class TestGenerateSecuritiesHistory:
    """測試單股歷史檔案產生"""
    
    def test_creates_one_file_per_security(self, tmp_path):
        """測試每支證券一個檔案"""
        stocks_data = [
            {
                "code": "2330",
                "name": "台積電",
                "dividend_history": [
                    {"year": 2026, "ex_date": "2026-07-25", "cash_dividend": 3.5}
                ]
            }
        ]
        
        generate_securities_history(stocks_data, tmp_path)
        
        filepath = tmp_path / "2330.json"
        assert filepath.exists()
        
        with open(filepath) as f:
            data = json.load(f)
        
        assert data["code"] == "2330"
        assert data["name"] == "台積電"
        assert len(data["history"]) == 1
```

### 2.2 整合測試

```python
# processor/test_integration.py
import pytest
import json
import time
from pathlib import Path
from generate_api import main as run_processor

class TestProcessorIntegration:
    """處理器整合測試"""
    
    def test_full_process(self, tmp_path):
        """測試完整處理流程"""
        # 準備 data/ 目錄結構
        data_dir = tmp_path / "data"
        stocks_dir = data_dir / "stocks"
        etfs_dir = data_dir / "etfs"
        preferred_dir = data_dir / "preferred"
        
        stocks_dir.mkdir(parents=True)
        etfs_dir.mkdir(parents=True)
        preferred_dir.mkdir(parents=True)
        
        # 寫入測試資料
        test_stock = {
            "code": "2330",
            "name": "台積電",
            "dividend_history": [
                {"year": 2026, "ex_date": "2027-01-01", "cash_dividend": 3.5}
            ]
        }
        (stocks_dir / "2330.json").write_text(json.dumps(test_stock))
        
        # 執行處理器
        api_dir = tmp_path / "api"
        # run_processor(data_dir, api_dir)
        
        # 驗證 api/ 檔案
        assert (api_dir / "upcoming.json").exists()
        assert (api_dir / "securities-index.json").exists()
        assert (api_dir / "securities").exists()
        assert (api_dir / "securities" / "2330.json").exists()
    
    def test_processing_time(self, tmp_path):
        """測試處理時間"""
        # 準備大量測試資料
        # 執行處理器
        # 驗證時間 < 30 秒
        pass
    
    def test_json_format_valid(self, tmp_path):
        """測試 JSON 格式正確"""
        # 執行處理器
        # 驗證所有 JSON 檔案可正確解析
        pass
```

---

## 3. 測試執行

```bash
# 執行所有測試
pytest processor/ -v

# 執行特定測試
pytest processor/test_generate_api.py -v

# 產生覆蓋率報告
pytest processor/ --cov=processor --cov-report=html
```

---

## 4. 驗收標準

| 標準 | 目標 |
|------|------|
| 單元測試通過率 | 100% |
| 整合測試通過率 | 100% |
| upcoming.json 格式 | 只包含未來配息 |
| securities-index.json | 包含所有證券 |
| securities/ 檔案數 | 與證券數量一致 |
| 處理時間 | < 30 秒 |
| JSON 格式 | 100% 可解析 |

---

## 5. 測試資料

```json
// processor/tests/fixtures/data/stocks/2330.json
{
  "code": "2330",
  "name": "台積電",
  "market": "TWSE",
  "type": "common",
  "dividend_history": [
    {
      "year": 2026,
      "quarter": 2,
      "announce_date": "2026-06-01",
      "ex_date": "2026-07-25",
      "pay_date": "2026-08-15",
      "cash_dividend": 3.5,
      "stock_dividend": 0
    }
  ],
  "last_updated": "2026-07-21"
}
```
