# 測試計畫：Phase 2 爬蟲（ETF + 特別股）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 2 — 爬蟲（ETF + 特別股） |
| **測試類型** | 單元測試、整合測試 |
| **工具** | pytest |
| **BDD 對應** | ETF、特別股配息資料抓取 |

---

## 1. 測試項目

### 1.1 單元測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| TWSEETFCrawler.fetch_etf_list | 回傳 ETF 列表 | test_twse_etf.py |
| TWSEETFCrawler.fetch_etf_dividend | 回傳 ETF 配息資料 | test_twse_etf.py |
| TWSEPreferredCrawler.fetch_preferred_list | 回傳特別股列表 | test_twse_preferred.py |
| save_stock（ETF） | 正確儲存 ETF 資料 | test_fetch.py |
| save_stock（特別股） | 正確儲存特別股資料 | test_fetch.py |

### 1.2 整合測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| fetch_etf_dividends | data/etfs/ 有檔案 | test_integration.py |
| fetch_preferred_dividends | data/preferred/ 有檔案 | test_integration.py |
| 完整爬蟲流程（三類） | 所有目錄有資料 | test_integration.py |

---

## 2. 測試案例

### 2.1 單元測試

```python
# crawler/test_twse_etf.py
import pytest
from sources.twse_etf import TWSEETFCrawler

class TestTWSEETFCrawler:
    """TWSE ETF 爬蟲測試"""
    
    def test_fetch_etf_list(self):
        """測試 ETF 列表抓取"""
        crawler = TWSEETFCrawler()
        # 使用 mock 測試
        # etfs = crawler.fetch_etf_list()
        # assert len(etfs) > 0
        # assert any(e["code"] == "0050" for e in etfs)
        pass
    
    def test_fetch_etf_dividend(self):
        """測試單支 ETF 配息抓取"""
        crawler = TWSEETFCrawler()
        # dividend = crawler.fetch_etf_dividend("0050")
        # assert "dividend_history" in dividend
        pass
    
    def test_etf_data_format(self):
        """測試 ETF 資料格式"""
        # 驗證包含必要欄位
        pass

# crawler/test_twse_preferred.py
import pytest
from sources.twse_preferred import TWSEPreferredCrawler

class TestTWSEPreferredCrawler:
    """TWSE 特別股爬蟲測試"""
    
    def test_fetch_preferred_list(self):
        """測試特別股列表抓取"""
        crawler = TWSEPreferredCrawler()
        # preferred = crawler.fetch_preferred_list()
        # assert len(preferred) > 0
        pass
    
    def test_preferred_data_format(self):
        """測試特別股資料格式"""
        # 驗證包含必要欄位
        pass
```

### 2.2 整合測試

```python
# crawler/test_integration.py
import pytest
import json
from pathlib import Path

class TestCrawlerIntegration:
    """爬蟲整合測試（ETF + 特別股）"""
    
    def test_full_crawl_all_types(self, tmp_path):
        """測試完整爬蟲（三類證券）"""
        import fetch
        fetch.DATA_DIR = tmp_path
        
        # run_crawler()
        
        # 驗證三類目錄都有資料
        stocks_dir = tmp_path / "stocks"
        etfs_dir = tmp_path / "etfs"
        preferred_dir = tmp_path / "preferred"
        
        assert stocks_dir.exists()
        assert etfs_dir.exists()
        assert preferred_dir.exists()
        
        # 驗證有檔案
        assert len(list(stocks_dir.glob("*.json"))) > 0
        assert len(list(etfs_dir.glob("*.json"))) > 0
        assert len(list(preferred_dir.glob("*.json"))) > 0
    
    def test_etf_file_format(self, tmp_path):
        """測試 ETF 檔案格式"""
        import fetch
        fetch.DATA_DIR = tmp_path
        
        # run_crawler()
        
        etfs_dir = tmp_path / "etfs"
        etf_files = list(etfs_dir.glob("*.json"))
        
        if etf_files:
            with open(etf_files[0]) as f:
                etf = json.load(f)
            
            assert "code" in etf
            assert "name" in etf
            assert "type" in etf
            assert etf["type"] == "etf"
    
    def test_preferred_file_format(self, tmp_path):
        """測試特別股檔案格式"""
        import fetch
        fetch.DATA_DIR = tmp_path
        
        # run_crawler()
        
        preferred_dir = tmp_path / "preferred"
        preferred_files = list(preferred_dir.glob("*.json"))
        
        if preferred_files:
            with open(preferred_files[0]) as f:
                preferred = json.load(f)
            
            assert "code" in preferred
            assert "name" in preferred
            assert "type" in preferred
            assert preferred["type"] == "preferred"
    
    def test_crawler_failure_isolation(self, tmp_path):
        """測試爬蟲失敗隔離"""
        # 模擬 ETF 爬蟲失敗，驗證其他類別不受影響
        pass
```

---

## 3. 測試執行

```bash
# 執行所有測試
pytest crawler/ -v

# 執行 ETF 測試
pytest crawler/test_twse_etf.py -v

# 執行特別股測試
pytest crawler/test_twse_preferred.py -v

# 執行整合測試
pytest crawler/test_integration.py -v

# 產生覆蓋率報告
pytest crawler/ --cov=crawler --cov-report=html
```

---

## 4. 驗收標準

| 標準 | 目標 |
|------|------|
| 單元測試通過率 | 100% |
| 整合測試通過率 | 100% |
| ETF 資料正確 | 至少 10 支（含 0050、0056） |
| 特別股資料正確 | 至少 5 支 |
| 總執行時間 | < 3 分鐘 |
| 失敗隔離 | 某類失敗不影響其他類別 |

---

## 5. 測試資料

```json
// crawler/tests/fixtures/raw_etf_data.json
{
  "code": "0050",
  "name": "元大台灣50",
  "year": 2026,
  "quarter": 2,
  "ex_date": "2026-07-20",
  "cash_dividend": 1.8
}

// crawler/tests/fixtures/raw_preferred_data.json
{
  "code": "7654",
  "name": "某特別股",
  "year": 2026,
  "quarter": 2,
  "ex_date": "2026-07-28",
  "cash_dividend": 0.95
}
```
