# Phase 2 爬蟲（ETF + 特別股） — 開發規格

> **對應 Roadmap**：Phase 2 — `docs/roadmaps/phases.md` 項目 #3
> **技術棧**：Python 3.11+ · requests · BeautifulSoup
> **Tech Decision**：`docs/tech-decision-stockpayday-2026-07-21.md`
> **操作流程**：`docs/interaction-flows/phases/phase-2-爬蟲ETF特別股.md`
> **研究報告**：`docs/research/twse-api-research.md`
> **狀態**：設計完成，待開發

---

## 概述

擴充爬蟲支援 ETF 和特別股配息資料。核心包含：

1. **ETF 爬蟲**：twse_etf.py 抓取 ETF 配息資料
2. **特別股爬蟲**：twse_preferred.py 抓取特別股配息資料
3. **整合測試**：確保三類證券可同時抓取

### 資料來源

所有證券配息資料統一從 **MOPS（公開資訊觀測站）** 取得：

```
URL: https://mops.twse.com.tw/mops/web/t05st09_ifrs
方法: POST
注意: 需要 CSRF Token，回應為 HTML 表格
```

詳細 API 研究請參考：`docs/research/twse-api-research.md`

---

## 1. 後端實作規格

### 1.1 檔案改動總覽

```
crawler/
├── fetch.py                  ← 修改：整合 ETF + 特別股爬蟲
└── sources/
    ├── twse_stock.py         ← 已有（Phase 1）
    ├── twse_etf.py           ← 新增：ETF 爬蟲模組
    └── twse_preferred.py     ← 新增：特別股爬蟲模組
```

### 1.2 fetch.py — 整合三類爬蟲

```python
"""
主爬蟲腳本 — 整合所有爬蟲模組

資料來源：
- 個股/ETF/特別股配息：MOPS (https://mops.twse.com.tw/mops/web/t05st09_ifrs)
- 使用相同端點，透過代號格式篩選不同類型
"""
import json
import time
from datetime import datetime
from pathlib import Path
from sources.twse_stock import fetch_stock_dividends
from sources.twse_etf import fetch_etf_dividends
from sources.twse_preferred import fetch_preferred_dividends

# 專案根目錄
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

def ensure_dirs():
    """確保資料目錄存在"""
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "stocks").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "etfs").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "preferred").mkdir(parents=True, exist_ok=True)

def save_raw(data: dict, filename: str):
    """儲存原始資料到 data/raw/"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    raw_dir = DATA_DIR / "raw" / date_str
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = raw_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 原始資料已儲存: {filepath}")

def save_stock(stock_data: dict, subfolder: str = "stocks"):
    """
    儲存證券基底資料
    
    Args:
        stock_data: 證券資料
        subfolder: 子目錄名稱（stocks/etfs/preferred）
    """
    code = stock_data["code"]
    filepath = DATA_DIR / subfolder / f"{code}.json"
    
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

def get_current_year_quarter() -> tuple:
    """
    取得當前民國年和季度
    
    Returns:
        (year, quarter) - 民國年、季度
    """
    now = datetime.now()
    roc_year = now.year - 1911  # 西元轉民國
    quarter = (now.month - 1) // 3 + 1
    return roc_year, quarter

def main():
    """主執行流程"""
    print("🕷️ 開始抓取所有證券配息資料...")
    ensure_dirs()
    
    # 取得當前年季
    year, quarter = get_current_year_quarter()
    print(f"📅 抓取 {year} 年第 {quarter} 季配息資料...")
    
    # 1. 抓取個股
    print("\n📋 抓取個股資料...")
    try:
        raw_stocks, stocks = fetch_stock_dividends(year, quarter)
        save_raw(raw_stocks, "stocks.json")
        for stock in stocks:
            save_stock(stock, "stocks")
        print(f"   ✅ 個股：{len(stocks)} 支")
    except Exception as e:
        print(f"   ❌ 個股爬蟲失敗: {e}")
        stocks = []
    
    # 2. 抓取 ETF
    print("\n📋 抓取 ETF 資料...")
    try:
        raw_etfs, etfs = fetch_etf_dividends(year, quarter)
        save_raw(raw_etfs, "etfs.json")
        for etf in etfs:
            save_stock(etf, "etfs")
        print(f"   ✅ ETF：{len(etfs)} 支")
    except Exception as e:
        print(f"   ❌ ETF 爬蟲失敗: {e}")
        etfs = []
    
    # 3. 抓取特別股
    print("\n📋 抓取特別股資料...")
    try:
        raw_preferred, preferred = fetch_preferred_dividends(year, quarter)
        save_raw(raw_preferred, "preferred.json")
        for pref in preferred:
            save_stock(pref, "preferred")
        print(f"   ✅ 特別股：{len(preferred)} 支")
    except Exception as e:
        print(f"   ❌ 特別股爬蟲失敗: {e}")
        preferred = []
    
    # 4. 統計
    print(f"\n{'='*50}")
    print(f"✅ 爬蟲完成")
    print(f"   個股：{len(stocks)} 支")
    print(f"   ETF：{len(etfs)} 支")
    print(f"   特別股：{len(preferred)} 支")
    print(f"   總計：{len(stocks) + len(etfs) + len(preferred)} 支")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
```

### 1.3 twse_etf.py — ETF 爬蟲模組

```python
"""
TWSE ETF 配息爬蟲
從公開資訊觀測站（MOPS）抓取 ETF 配息資料

資料來源：https://mops.twse.com.tw/mops/web/t05st09_ifrs
（使用相同端點，與個股/特別股共用）

注意事項：
- ETF 代號格式：4 位數字（如 0050、0056、00878）
- 需要先 GET 取得 CSRF Token
- 使用 POST 發送請求
- 回應為 HTML，需解析表格
"""
import requests
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional
from requests.exceptions import RequestException

# MOPS 配息公告 URL（共用）
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"

class TWSEETFCrawler:
    """TWSE ETF 配息爬蟲"""
    
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
        
        # 解析 CSRF Token
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
        if response.apparent_encoding:
            return response.apparent_encoding
        
        content_type = response.headers.get("Content-Type", "")
        if "charset=" in content_type:
            return content_type.split("charset=")[-1].strip()
        
        return "utf-8"
    
    def fetch_etf_list(self) -> List[Dict]:
        """
        抓取 ETF 清單
        
        Returns:
            ETF 基本資訊列表
        """
        # TODO: 實作 ETF 列表抓取
        # 方案 1：從 MOPS 取得（使用代號格式篩選）
        # 方案 2：從 TWSE ETF 專區取得
        # 方案 3：維護一份已知 ETF 清單
        pass
    
    def fetch_etf_dividends_for_quarter(self, year: int, quarter: int) -> List[Dict]:
        """
        抓取指定年季的 ETF 配息資料
        
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
        
        # 5. 解析 HTML 表格，篩選 ETF
        return self._parse_html_table_for_etf(response.text)
    
    def _parse_html_table_for_etf(self, html: str) -> List[Dict]:
        """
        解析 HTML 表格，篩選 ETF 配息資料
        
        ETF 代號特徵：
        - 4 位數字（如 0050、0056、00878）
        
        Args:
            html: HTML 內容
            
        Returns:
            ETF 配息資料列表
        """
        soup = BeautifulSoup(html, "html.parser")
        records = []
        
        # 找到資料表格
        table = soup.find("table", {"id": "table01"})
        if not table:
            table = soup.find("table", class_="tableTF")
        
        if not table:
            print("⚠️ 找不到資料表格")
            return records
        
        # 解析表格行
        rows = table.find_all("tr")
        for row in rows[1:]:  # 跳過標題行
            cells = row.find_all("td")
            if len(cells) >= 8:
                code = cells[0].get_text(strip=True)
                
                # 篩選 ETF
                if self._is_etf(code):
                    record = {
                        "code": code,
                        "name": cells[1].get_text(strip=True),
                        "announce_date": cells[2].get_text(strip=True),
                        "ex_date": cells[3].get_text(strip=True),
                        "pay_date": cells[4].get_text(strip=True),
                        "cash_dividend": self._parse_number(cells[5].get_text(strip=True)),
                        "stock_dividend": self._parse_number(cells[6].get_text(strip=True)),
                        "type": "etf",
                    }
                    records.append(record)
        
        return records
    
    def _is_etf(self, code: str) -> bool:
        """
        判斷是否為 ETF
        
        ETF 代號特徵：
        - 4 位數字（如 0050、0056、00878）
        
        Args:
            code: 證券代號
            
        Returns:
            是否為 ETF
        """
        if len(code) == 4 and code.isdigit():
            code_num = int(code)
            # ETF 代號範圍：0001-0999（約略）
            if 1 <= code_num <= 999:
                return True
        return False
    
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

def fetch_etf_dividends(year: int, quarter: int) -> Tuple[Dict, List[Dict]]:
    """
    抓取所有 ETF 配息資料
    
    Args:
        year: 民國年
        quarter: 季度
        
    Returns:
        (raw_data, processed_etfs)
    """
    crawler = TWSEETFCrawler()
    
    try:
        etfs = crawler.fetch_etf_dividends_for_quarter(year, quarter)
        
        # 整理 raw_data
        raw_data = {
            "year": year,
            "quarter": quarter,
            "records": etfs,
            "count": len(etfs),
        }
        
        return raw_data, etfs
        
    except Exception as e:
        print(f"❌ ETF 爬蟲失敗: {e}")
        return {}, []
```

### 1.4 twse_preferred.py — 特別股爬蟲模組

```python
"""
TWSE 特別股配息爬蟲
從公開資訊觀測站（MOPS）抓取特別股配息資料

資料來源：https://mops.twse.com.tw/mops/web/t05st09_ifrs
（使用相同端點，與個股/ETF 共用）

注意事項：
- 特別股代號格式：4 位數字（如 7654）或帶字母後綴（如 2330A）
- 需要先 GET 取得 CSRF Token
- 使用 POST 發送請求
- 回應為 HTML，需解析表格
"""
import requests
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional
from requests.exceptions import RequestException

# MOPS 配息公告 URL（共用）
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"

class TWSEPreferredCrawler:
    """TWSE 特別股配息爬蟲"""
    
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
        
        # 解析 CSRF Token
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
        if response.apparent_encoding:
            return response.apparent_encoding
        
        content_type = response.headers.get("Content-Type", "")
        if "charset=" in content_type:
            return content_type.split("charset=")[-1].strip()
        
        return "utf-8"
    
    def fetch_preferred_list(self) -> List[Dict]:
        """
        抓取特別股清單
        
        Returns:
            特別股基本資訊列表
        """
        # TODO: 實作特別股列表抓取
        # 方案 1：從 MOPS 取得（使用代號格式篩選）
        # 方案 2：從 TWSE 特別股專區取得
        # 方案 3：維護一份已知特別股清單
        pass
    
    def fetch_preferred_dividends_for_quarter(self, year: int, quarter: int) -> List[Dict]:
        """
        抓取指定年季的特別股配息資料
        
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
        
        # 5. 解析 HTML 表格，篩選特別股
        return self._parse_html_table_for_preferred(response.text)
    
    def _parse_html_table_for_preferred(self, html: str) -> List[Dict]:
        """
        解析 HTML 表格，篩選特別股配息資料
        
        特別股代號特徵：
        - 4 位數字（如 7654）
        - 或帶字母後綴（如 2330A、2330B）
        
        Args:
            html: HTML 內容
            
        Returns:
            特別股配息資料列表
        """
        soup = BeautifulSoup(html, "html.parser")
        records = []
        
        # 找到資料表格
        table = soup.find("table", {"id": "table01"})
        if not table:
            table = soup.find("table", class_="tableTF")
        
        if not table:
            print("⚠️ 找不到資料表格")
            return records
        
        # 解析表格行
        rows = table.find_all("tr")
        for row in rows[1:]:  # 跳過標題行
            cells = row.find_all("td")
            if len(cells) >= 8:
                code = cells[0].get_text(strip=True)
                
                # 篩選特別股（需要額外判斷邏輯）
                if self._is_preferred_stock(code):
                    record = {
                        "code": code,
                        "name": cells[1].get_text(strip=True),
                        "announce_date": cells[2].get_text(strip=True),
                        "ex_date": cells[3].get_text(strip=True),
                        "pay_date": cells[4].get_text(strip=True),
                        "cash_dividend": self._parse_number(cells[5].get_text(strip=True)),
                        "stock_dividend": self._parse_number(cells[6].get_text(strip=True)),
                        "type": "preferred",
                    }
                    records.append(record)
        
        return records
    
    def _is_preferred_stock(self, code: str) -> bool:
        """
        判斷是否為特別股
        
        特別股代號特徵：
        - 4 位數字且 >= 7000（如 7654）
        - 或帶字母後綴（如 2330A）
        
        Args:
            code: 證券代號
            
        Returns:
            是否為特別股
        """
        # 帶字母後綴
        if len(code) == 5 and code[:4].isdigit() and code[4].isalpha():
            return True
        
        # 4 位數字且 >= 7000（特別股常見範圍）
        if len(code) == 4 and code.isdigit():
            code_num = int(code)
            if code_num >= 7000:
                return True
        
        return False
    
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

def fetch_preferred_dividends(year: int, quarter: int) -> Tuple[Dict, List[Dict]]:
    """
    抓取所有特別股配息資料
    
    Args:
        year: 民國年
        quarter: 季度
        
    Returns:
        (raw_data, processed_preferred)
    """
    crawler = TWSEPreferredCrawler()
    
    try:
        preferred = crawler.fetch_preferred_dividends_for_quarter(year, quarter)
        
        # 整理 raw_data
        raw_data = {
            "year": year,
            "quarter": quarter,
            "records": preferred,
            "count": len(preferred),
        }
        
        return raw_data, preferred
        
    except Exception as e:
        print(f"❌ 特別股爬蟲失敗: {e}")
        return {}, []
```

### 1.5 資料格式規格

#### data/etfs/{code}.json（ETF 基底資料）

```json
{
  "code": "0050",
  "name": "元大台灣50",
  "market": "TWSE",
  "type": "etf",
  "dividend_history": [
    {
      "year": 2026,
      "quarter": 2,
      "announce_date": "2026-06-01",
      "ex_date": "2026-07-20",
      "pay_date": "2026-08-10",
      "cash_dividend": 1.8,
      "stock_dividend": 0
    }
  ],
  "last_updated": "2026-07-21"
}
```

#### data/preferred/{code}.json（特別股基底資料）

```json
{
  "code": "7654",
  "name": "某特別股",
  "market": "TWSE",
  "type": "preferred",
  "dividend_history": [
    {
      "year": 2026,
      "quarter": 2,
      "announce_date": "2026-06-01",
      "ex_date": "2026-07-28",
      "pay_date": "2026-08-20",
      "cash_dividend": 0.95,
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
| ETF 資料為空 | Phase 2 互動流程 | 記錄警告，繼續執行 |
| 特別股無配息紀錄 | 邊界情況 | 正常行為，不寫入 |
| 某類證券 API 失敗 | Phase 2 互動流程 | 記錄失敗，其他類別繼續 |
| TWSE 改版 | Tech Decision 風險 | 監控成功率，手動更新 |
| CSRF Token 取得失敗 | API 研究 | 重試 3 次，失敗後記錄錯誤 |
| HTML 表格結構變動 | API 研究 | 監控解析成功率 |

---

## 3. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 研究 MOPS API 實際回應格式 | Phase 1 |
| 2 | 實作 twse_etf.py 爬蟲 | #1 |
| 3 | 實作 twse_preferred.py 爬蟲 | #1 |
| 4 | 修改 fetch.py 整合三類爬蟲 | #2, #3 |
| 5 | 測試：執行完整爬蟲 | #4 |
| 6 | 驗證資料格式正確性 | #5 |

---

## 4. 驗收檢查清單

### ETF 爬蟲
- [ ] `data/etfs/` 有 ETF 基底資料
- [ ] 至少 10 支 ETF 資料正確（含 0050、0056）
- [ ] ETF 資料包含配息歷史

### 特別股爬蟲
- [ ] `data/preferred/` 有特別股基底資料
- [ ] 特別股資料格式正確

### 整合測試
- [ ] 同時抓取三類證券可正常完成
- [ ] 各類資料分別儲存到對應目錄
- [ ] 總執行時間 < 3 分鐘

### 錯誤處理
- [ ] 某類證券失敗不影響其他類別
- [ ] 失敗項目有記錄日誌
- [ ] CSRF Token 取得失敗有處理
- [ ] 網路失敗有重試機制
