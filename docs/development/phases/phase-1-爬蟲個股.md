# Phase 1 爬蟲（個股） — 開發規格

> **對應 Roadmap**：Phase 1 — `docs/roadmaps/phases.md` 項目 #2
> **技術棧**：Python 3.11+ · requests · BeautifulSoup
> **Tech Decision**：`docs/tech-decision-stockpayday-2026-07-21.md`
> **操作流程**：`docs/interaction-flows/phases/phase-1-爬蟲個股.md`
> **狀態**：設計完成，待開發

---

## 概述

從 TWSE 抓取個股配息資料並儲存。核心包含：

1. **主腳本**：fetch.py 統籌爬蟲流程
2. **個股爬蟲**：twse_stock.py 抓取 TWSE 個股資料
3. **資料儲存**：raw/ 原始資料 + stocks/ 基底資料

---

## 1. 後端實作規格

### 1.1 檔案改動總覽

```
crawler/
├── __init__.py
├── fetch.py                  ← 新增：主爬蟲腳本
└── sources/
    ├── __init__.py
    └── twse_stock.py         ← 新增：個股爬蟲模組
```

### 1.2 fetch.py — 主爬蟲腳本

```python
"""
StockPayDay++ 主爬蟲腳本
負責協調所有爬蟲模組，抓取 TWSE 配息資料

資料來源：MOPS (https://mops.twse.com.tw/mops/web/t05st09_ifrs)
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 專案根目錄
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

def ensure_dirs():
    """確保資料目錄存在"""
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "stocks").mkdir(parents=True, exist_ok=True)

def save_raw(data: dict, filename: str):
    """儲存原始資料到 data/raw/"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    raw_dir = DATA_DIR / "raw" / date_str
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = raw_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 原始資料已儲存: {filepath}")

def save_stock(stock_data: dict):
    """儲存個股基底資料到 data/stocks/"""
    code = stock_data["code"]
    filepath = DATA_DIR / "stocks" / f"{code}.json"
    
    # 讀取舊資料（如果存在）
    existing = {}
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)
    
    # 合併歷史資料（避免重複）
    existing_history = {h["year"]: h for h in existing.get("dividend_history", [])}
    for h in stock_data.get("dividend_history", []):
        existing_history[h["year"]] = h
    
    stock_data["dividend_history"] = sorted(
        existing_history.values(),
        key=lambda x: x["year"],
        reverse=True
    )
    stock_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(stock_data, f, ensure_ascii=False, indent=2)

def main():
    """主執行流程"""
    print("🕷️ 開始抓取個股配息資料...")
    ensure_dirs()
    
    # TODO: 呼叫 twse_stock.py 抓取資料
    # from sources.twse_stock import fetch_stock_dividends
    # raw_data, stocks = fetch_stock_dividends()
    # save_raw(raw_data, "stocks.json")
    # for stock in stocks:
    #     save_stock(stock)
    
    print("✅ 個股爬蟲完成")

if __name__ == "__main__":
    main()
```

### 1.3 twse_stock.py — 個股爬蟲模組

```python
"""
TWSE 個股配息爬蟲
從公開資訊觀測站（MOPS）抓取個股配息資料

資料來源：https://mops.twse.com.tw/mops/web/t05st09_ifrs

注意事項：
- 需要先 GET 取得 CSRF Token
- 使用 POST 發送請求
- 回應為 HTML，需解析表格
- 有 WAF 保護，需正確 Headers
"""
import requests
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional
from requests.exceptions import RequestException

# MOPS 配息公告 URL
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"

class TWSEStockCrawler:
    """TWSE 個股配息爬蟲"""
    
    def __init__(self, max_retries: int = 3, delay: float = 2.0):
        """
        初始化爬蟲
        
        Args:
            max_retries: 最大重試次數
            delay: 重試間隔秒數（會遞增）
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        self.max_retries = max_retries
        self.delay = delay
        self._csrf_token: Optional[str] = None
    
    def _get_csrf_token(self) -> str:
        """
        取得 CSRF Token
        
        Returns:
            CSRF Token 字串
        """
        response = self._request_with_retry(MOPS_DIVIDEND_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 解析 CSRF Token（根據實際頁面結構調整）
        token_input = soup.find("input", {"name": "csrf_token"})
        if token_input:
            return token_input.get("value", "")
        
        # 備用：嘗試其他常見 Token 欄位名稱
        for name in ["_token", "token", "csrf"]:
            token_input = soup.find("input", {"name": name})
            if token_input:
                return token_input.get("value", "")
        
        return ""
    
    def _request_with_retry(self, url: str, method: str = "GET", data: dict = None) -> requests.Response:
        """
        帶有重試機制的 HTTP 請求
        
        Args:
            url: 請求 URL
            method: 請求方法（GET/POST）
            data: POST 請求的資料
            
        Returns:
            Response 物件
            
        Raises:
            RequestException: 請求失敗
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "POST":
                    response = self.session.post(url, data=data, timeout=30)
                else:
                    response = self.session.get(url, timeout=30)
                
                response.raise_for_status()
                return response
                
            except RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.delay * (attempt + 1)
                    print(f"⚠️ 請求失敗，{wait_time} 秒後重試... ({attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 請求失敗，已達最大重試次數: {e}")
        
        raise last_exception
    
    def _detect_encoding(self, response: requests.Response) -> str:
        """
        偵測回應編碼
        
        Args:
            response: Response 物件
            
        Returns:
            編碼名稱
        """
        # 優先使用 apparent_encoding
        if response.apparent_encoding:
            return response.apparent_encoding
        
        # 從 Content-Type 偵測
        content_type = response.headers.get("Content-Type", "")
        if "charset=" in content_type:
            return content_type.split("charset=")[-1].strip()
        
        return "utf-8"
    
    def fetch_dividend_list(self, year: int, quarter: int) -> List[Dict]:
        """
        抓取指定年季的配息公告列表
        
        Args:
            year: 民國年
            quarter: 季度 (1-4)
            
        Returns:
            配息資料列表
        """
        # 1. 取得 CSRF Token
        if not self._csrf_token:
            self._csrf_token = self._get_csrf_token()
        
        # 2. 準備 POST 資料
        data = {
            "csrf_token": self._csrf_token,
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "keyword4": "",
            "code1": "",
            "ESSION": str(year),
            "ession1": str(quarter),
        }
        
        # 3. 發送 POST 請求
        response = self._request_with_retry(MOPS_DIVIDEND_URL, method="POST", data=data)
        
        # 4. 偵測編碼並解析
        encoding = self._detect_encoding(response)
        response.encoding = encoding
        
        # 5. 解析 HTML 表格
        return self._parse_html_table(response.text)
    
    def _parse_html_table(self, html: str) -> List[Dict]:
        """
        解析 HTML 表格中的配息資料
        
        Args:
            html: HTML 內容
            
        Returns:
            配息資料列表
        """
        soup = BeautifulSoup(html, "html.parser")
        records = []
        
        # 找到資料表格（根據實際頁面結構調整選擇器）
        table = soup.find("table", {"id": "table01"})
        if not table:
            # 嘗試其他選擇器
            table = soup.find("table", class_="tableTF")
        
        if not table:
            print("⚠️ 找不到資料表格")
            return records
        
        # 解析表格行
        rows = table.find_all("tr")
        for row in rows[1:]:  # 跳過標題行
            cells = row.find_all("td")
            if len(cells) >= 8:
                record = {
                    "code": cells[0].get_text(strip=True),
                    "name": cells[1].get_text(strip=True),
                    "announce_date": cells[2].get_text(strip=True),
                    "ex_date": cells[3].get_text(strip=True),
                    "pay_date": cells[4].get_text(strip=True),
                    "cash_dividend": self._parse_number(cells[5].get_text(strip=True)),
                    "stock_dividend": self._parse_number(cells[6].get_text(strip=True)),
                }
                records.append(record)
        
        return records
    
    def _parse_number(self, text: str) -> float:
        """
        解析數字字串
        
        Args:
            text: 數字字串（可能包含逗號）
            
        Returns:
            浮點數
        """
        try:
            return float(text.replace(",", "").replace("--", "0"))
        except (ValueError, AttributeError):
            return 0.0
    
    def parse_dividend_record(self, raw_record: Dict) -> Dict:
        """
        解析單筆配息紀錄
        
        Args:
            raw_record: TWSE 原始資料
            
        Returns:
            標準化後的配息資料
        """
        return {
            "code": raw_record.get("code", ""),
            "name": raw_record.get("name", ""),
            "announce_date": raw_record.get("announce_date", ""),
            "ex_date": raw_record.get("ex_date", ""),
            "pay_date": raw_record.get("pay_date", ""),
            "cash_dividend": float(raw_record.get("cash_dividend", 0)),
            "stock_dividend": float(raw_record.get("stock_dividend", 0)),
        }

def fetch_stock_dividends() -> Tuple[Dict, List[Dict]]:
    """
    抓取所有個股配息資料
    
    Returns:
        (raw_data, processed_stocks)
    """
    crawler = TWSEStockCrawler()
    
    # TODO: 實作完整抓取邏輯
    # 1. 抓取最近 N 個月的配息公告
    # 2. 依股票代號分組
    # 3. 產出 raw_data 和 processed_stocks
    
    raw_data = {}
    processed_stocks = []
    
    return raw_data, processed_stocks
```

### 1.4 資料格式規格

#### data/stocks/{code}.json（個股基底資料）

```json
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

---

## 2. 邊界條件處理

| 情境 | 來源 | 處理方式 |
|------|------|---------|
| 網路斷線 | Phase 1 互動流程 | 重試 3 次，失敗後記錄錯誤 |
| TWSE API 改版 | Tech Decision 風險 | 監控爬蟲成功率，手動更新解析邏輯 |
| TWSE 限流 | Phase 1 互動流程 | 加入延遲（1-2 秒/請求） |
| 資料格式異常 | Phase 1 互動流程 | 記錄異常資料，跳過繼續 |
| 股票無配息紀錄 | 邊界情況 | 正常行為，不寫入 dividend_history |

---

## 3. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 建立 crawler/ 目錄結構 | Phase 0 |
| 2 | 實作 fetch.py 主腳本框架 | #1 |
| 3 | 研究 TWSE API/網頁結構 | - |
| 4 | 實作 twse_stock.py 爬蟲 | #3 |
| 5 | 整合 fetch.py 與 twse_stock.py | #2, #4 |
| 6 | 實作資料儲存邏輯 | #2 |
| 7 | 測試：執行爬蟲並檢查資料 | #5, #6 |

---

## 4. 驗收檢查清單

### 爬蟲執行
- [ ] `python crawler/fetch.py` 可正常執行
- [ ] 執行過程無紅色錯誤訊息
- [ ] 執行時間 < 2 分鐘

### 資料儲存
- [ ] `data/raw/` 有 TWSE 原始回應 JSON
- [ ] `data/stocks/` 有個股基底資料
- [ ] 至少 10 支股票資料正確

### 資料格式
- [ ] 每支股票包含 `code` 欄位
- [ ] 每支股票包含 `name` 欄位
- [ ] 每支股票包含 `dividend_history` 陣列
- [ ] `dividend_history` 包含 `ex_date` 和 `cash_dividend`

### 錯誤處理
- [ ] 網路失敗時有錯誤訊息
- [ ] 可重新執行不影響舊資料
- [ ] 異常資料有記錄日誌
