# Phase 2 爬蟲（MOPS 配息日） — 開發規格

> **對應 Roadmap**：Phase 2 — `docs/roadmaps/phases.md`
> **技術棧**：Python 3.11+ · requests · BeautifulSoup
> **資料來源**：MOPS（公開資訊觀測站）
> **狀態**：設計完成，待開發

---

## 概述

從 MOPS 抓取配息日（pay_date）資料，作為 TWT48U 的補充。核心包含：

1. **MOPS 爬蟲**：抓取指定年季的配息公告
2. **資料儲存**：以季為單位，存到 `data/mops/{YYYY}-Q{N}.json`

### 資料來源

```
URL: https://mops.twse.com.tw/mops/web/t05st09_ifrs
方法: POST
注意: 需要 CSRF Token，回應為 HTML 表格
```

### MOPS 欄位（只存 3 個）

| 欄位 | 說明 |
|------|------|
| `code` | 證券代號 |
| `ex_date` | 除息交易日 |
| `pay_date` | 配息日（股利發放日） |

---

## 1. 後端實作規格

### 1.1 檔案改動總覽

```
crawler/
├── fetch.py                  ← 修改：整合 MOPS 爬蟲
└── sources/
    ├── base_crawler.py       ← 已有：共用功能
    └── twse_mops.py          ← 新增：MOPS 爬蟲
```

### 1.2 twse_mops.py — MOPS 爬蟲模組

```python
"""
TWSE MOPS 爬蟲 — 配息公告
從公開資訊觀測站抓取配息日資料

資料來源：https://mops.twse.com.tw/mops/web/t05st09_ifrs
方法: POST
注意: 需要 CSRF Token，回應為 HTML 表格

只擷取以下欄位：
- code（證券代號）
- ex_date（除息交易日）
- pay_date（配息日）
"""

import requests
import time
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# MOPS 配息公告 URL
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"


class MOPSCrawler:
    """MOPS 配息爬蟲"""

    def __init__(self, max_retries: int = 3, delay: float = 2.0):
        """
        初始化爬蟲

        Args:
            max_retries: 最大重試次數
            delay: 重試間隔秒數（會遞增）
        """
        if max_retries < 1:
            raise ValueError(f"max_retries must be >= 1, got {max_retries}")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        self.max_retries = max_retries
        self.delay = delay
        self._csrf_token: Optional[str] = None

    def _get_csrf_token(self) -> str:
        """
        從 MOPS 頁面取得 CSRF Token

        Returns:
            CSRF Token 字串（取不到則回傳空字串）
        """
        response = self._request_with_retry(MOPS_DIVIDEND_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        for name in ("csrf_token", "_token", "token", "csrf"):
            tag = soup.find("input", {"name": name})
            if tag and tag.get("value"):
                token = tag["value"].strip()
                logger.info("CSRF token 取得成功 (%s)", name)
                return token

        logger.warning("未找到 CSRF token 欄位")
        return ""

    def _request_with_retry(
        self,
        url: str,
        method: str = "GET",
        data: Optional[dict] = None,
    ) -> requests.Response:
        """
        帶有重試機制的 HTTP 請求

        Args:
            url: 請求 URL
            method: GET / POST
            data: POST 表單資料

        Returns:
            Response 物件
        """
        last_exception: Optional[RequestException] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if method.upper() == "POST":
                    resp = self.session.post(url, data=data, timeout=30)
                else:
                    resp = self.session.get(url, timeout=30)

                resp.raise_for_status()
                return resp

            except RequestException as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    wait = self.delay * attempt
                    logger.warning(
                        "MOPS 請求失敗，%s 秒後重試 (%d/%d): %s",
                        wait, attempt, self.max_retries, exc,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "MOPS 請求失敗，已達最大重試次數 (%d): %s",
                        self.max_retries, exc,
                    )

        if last_exception is None:
            raise RuntimeError("MOPS 請求失敗：未預期的錯誤")
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

    def fetch(self, year: int, quarter: int) -> List[Dict]:
        """
        抓取指定年季的配息資料

        Args:
            year: 民國年（例如 114）
            quarter: 季度 1-4

        Returns:
            配息資料列表（只含 code, ex_date, pay_date）
        """
        # 1. 取得 CSRF Token
        if not self._csrf_token:
            self._csrf_token = self._get_csrf_token()

        # 2. 準備 POST 資料
        form_data = {
            "csrf_token": self._csrf_token,
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "keyword4": "",
            "code1": "",
            "YEARN": str(year),
            "SEASON": str(quarter),
        }

        # 3. 發送 POST 請求
        resp = self._request_with_retry(
            MOPS_DIVIDEND_URL, method="POST", data=form_data,
        )

        # 4. 偵測編碼
        encoding = self._detect_encoding(resp)
        resp.encoding = encoding

        # 5. 解析 HTML 表格
        records = self._parse_html_table(resp.text)
        logger.info(
            "MOPS fetch(%d, Q%d) — 解析到 %d 筆",
            year, quarter, len(records),
        )
        return records

    def _parse_html_table(self, html: str) -> List[Dict]:
        """
        解析 MOPS 回傳 HTML 中的配息資料表格

        Args:
            html: MOPS 回傳的 HTML 內容

        Returns:
            配息資料列表（只含 code, ex_date, pay_date）
        """
        soup = BeautifulSoup(html, "html.parser")
        records: List[Dict] = []

        # 找到資料表格
        table = (
            soup.find("table", {"id": "table01"})
            or soup.find("table", class_="tableTF")
        )
        if not table:
            logger.warning("找不到資料表格")
            return records

        rows = table.find_all("tr")
        for row in rows[1:]:  # 跳過標題列
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            code = cells[0].get_text(strip=True)
            if not code or code == "合計":
                continue

            # 只擷取需要的欄位
            ex_date = self._roc_to_ad(cells[3].get_text(strip=True))
            pay_date = self._roc_to_ad(cells[4].get_text(strip=True))

            record = {
                "code": code,
                "ex_date": ex_date,
                "pay_date": pay_date,
            }
            records.append(record)

        return records

    @staticmethod
    def _roc_to_ad(roc_date: str) -> str:
        """
        民國年日期字串轉西元年

        格式：114/06/01 或 114年06月01日 → 2025-06-01
        """
        if not roc_date:
            return ""

        # 移除空白
        normalized = roc_date.strip()

        # 嘗試匹配 "114年06月01日" 格式
        match = re.match(r"(\d{2,3})年(\d{1,2})月(\d{1,2})日", normalized)
        if match:
            roc_year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            ad_year = roc_year + 1911
            return f"{ad_year:04d}-{month:02d}-{day:02d}"

        # 嘗試匹配 "114/06/01" 格式
        parts = normalized.replace("-", "/").split("/")
        if len(parts) == 3:
            try:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                if year < 1000:  # 民國年
                    year += 1911
                return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                pass

        return normalized


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_mops(year: int, quarter: int) -> List[Dict]:
    """
    抓取 MOPS 配息資料（便捷包裝）

    Args:
        year: 民國年
        quarter: 季度

    Returns:
        配息資料列表
    """
    crawler = MOPSCrawler()
    return crawler.fetch(year, quarter)
```

### 1.3 資料儲存邏輯

```python
"""
資料儲存 — MOPS

檔案結構：
data/mops/
└── 2026-Q3.json    # Q3 配息公告
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 專案根目錄
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "mops"


def ensure_dirs():
    """確保資料目錄存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_mops(records: List[Dict], year: int, quarter: int):
    """
    儲存 MOPS 資料到季檔案

    Args:
        records: 配息資料列表
        year: 民國年
        quarter: 季度
    """
    ensure_dirs()

    filename = f"{year + 1911}-Q{quarter}"  # 轉為西元年
    filepath = DATA_DIR / f"{filename}.json"

    # 讀取舊資料
    old_records = []
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            old_records = data.get("records", [])

    # 合併（以 code + ex_date 為 key 去重）
    merged = merge_mops_records(old_records, records)

    # 寫入
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "year": year,
        "quarter": quarter,
        "records": merged,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("已儲存 %s.json：%d 筆", filename, len(merged))


def merge_mops_records(old: List[Dict], new: List[Dict]) -> List[Dict]:
    """
    合併兩筆資料列表，以 (code, ex_date) 為 key 去重

    Args:
        old: 舊資料
        new: 新資料

    Returns:
        合併後的資料列表
    """
    # 建立 lookup
    lookup: Dict[tuple, Dict] = {}
    for rec in old:
        key = (rec["code"], rec["ex_date"])
        lookup[key] = rec

    # 新資料覆蓋舊資料
    for rec in new:
        key = (rec["code"], rec["ex_date"])
        lookup[key] = rec

    # 排序（依 ex_date）
    merged = sorted(lookup.values(), key=lambda x: x["ex_date"])
    return merged
```

### 1.4 資料格式規格

#### data/mops/{YYYY}-Q{N}.json

```json
{
  "last_updated": "2026-08-21",
  "year": 115,
  "quarter": 3,
  "records": [
    {
      "code": "00850",
      "ex_date": "2026-08-21",
      "pay_date": "2026-09-15"
    },
    {
      "code": "00907",
      "ex_date": "2026-08-25",
      "pay_date": "2026-09-20"
    }
  ]
}
```

---

## 2. 邊界條件處理

| 情境 | 處理方式 |
|------|---------|
| CSRF Token 取得失敗 | 重試 3 次，失敗後記錄錯誤 |
| HTML 表格結構異常 | 嘗試多種選擇器 |
| 編碼問題 | 使用 chardet 自動偵測 |
| 資料為空 | 記錄警告，不寫入檔案 |
| 舊資料合併 | 以 (code, ex_date) 為 key 去重 |

---

## 3. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 研究 MOPS API 實際回應格式 | Phase 1 |
| 2 | 實作 twse_mops.py 爬蟲 | #1 |
| 3 | 實作資料儲存邏輯 | #2 |
| 4 | 修改 fetch.py 整合 | #2, #3 |
| 5 | 測試：執行爬蟲並檢查資料 | #4 |

---

## 4. 驗收檢查清單

### 爬蟲執行
- [ ] `python crawler/fetch.py` 可正常執行
- [ ] 執行過程無紅色錯誤訊息
- [ ] 執行時間 < 60 秒

### 資料儲存
- [ ] `data/mops/` 有季檔案（如 2026-Q3.json）
- [ ] 至少 10 筆資料正確
- [ ] 每筆資料包含：code, ex_date, pay_date

### 資料格式
- [ ] ex_date 為西元年格式（YYYY-MM-DD）
- [ ] pay_date 為西元年格式（YYYY-MM-DD）
- [ ] 重複執行不會產生重複資料

### 錯誤處理
- [ ] 網路失敗時有錯誤訊息
- [ ] 可重新執行不影響舊資料
- [ ] CSRF Token 失敗有處理
