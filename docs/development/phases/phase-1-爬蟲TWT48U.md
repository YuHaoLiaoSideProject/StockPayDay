# Phase 1~2 爬蟲（TWT48U + MOPS） — 開發規格

> **對應 Roadmap**：Phase 1~2 — `docs/roadmaps/phases.md`
> **技術棧**：Python 3.11+ · requests · BeautifulSoup
> **資料來源**：TWSE TWT48U + MOPS
> **狀態**：設計完成，待開發

---

## 概述

從 TWSE/MOPS 抓取配息資料。核心包含：

1. **TWT48U 爬蟲**：抓取未來 1-2 個月的除息預告
2. **MOPS 爬蟲**：抓取配息日（pay_date）資料
3. **資料儲存**：分開儲存到 `data/twses/` 和 `data/mops/`

### 資料來源

```
URL: https://www.twse.com.tw/rwd/zh/exRight/TWT48U
方法: GET
參數: response=json
回傳: JSON 格式
```

### TWT48U 欄位

| 位置 | 欄位 | 說明 |
|------|------|------|
| [0] | 除權除息日期 | 除息日（民國年） |
| [1] | 股票代號 | 證券代碼 |
| [2] | 名稱 | 證券名稱 |
| [3] | 除權息 | 權/息/權息 |
| [4] | 無償配股率 | 股票股利 |
| [7] | 現金股利 | 配息金額 |

---

## 1. 後端實作規格

### 1.1 檔案改動總覽

```
crawler/
├── fetch.py                  ← 修改：整合 TWT48U 爬蟲
└── sources/
    ├── base_crawler.py       ← 新增：共用功能
    └── twse_twt48u.py        ← 新增：TWT48U 爬蟲
```

### 1.2 twse_twt48u.py — TWT48U 爬蟲模組

```python
"""
TWSE TWT48U 爬蟲 — 除權除息預告表
從臺灣證券交易所抓取未來除權除息預告資料

資料來源：https://www.twse.com.tw/rwd/zh/exRight/TWT48U
方法: GET
參數: response=json
回傳: JSON 格式

注意事項：
- 需要完整的瀏覽器 Headers（TWSE 有 WAF 保護）
- 回傳民國年日期，需轉換為西元年
- 資料範圍為未來 1-2 個月
"""

import requests
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# TWSE TWT48U URL
TWT48U_URL = "https://www.twse.com.tw/rwd/zh/exRight/TWT48U"


class TWT48UCrawler:
    """TWSE TWT48U 爬蟲"""

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
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": "https://www.twse.com.tw/zh/trading/exRight/TWT48U.html",
            "Sec-CH-UA": '"Google Chrome";v="125", "Chromium";v="125"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
        })
        self.max_retries = max_retries
        self.delay = delay

    def fetch(self) -> List[Dict]:
        """
        抓取未來除權除息預告資料

        Returns:
            配息資料列表
        """
        params = {"response": "json"}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(TWT48U_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                records = []
                for row in data.get("data", []):
                    record = self._parse_row(row)
                    if record:
                        records.append(record)

                logger.info("TWT48U 抓取成功：%d 筆", len(records))
                return records

            except Exception as e:
                if attempt < self.max_retries:
                    wait = self.delay * attempt
                    logger.warning(
                        "TWT48U 請求失敗，%s 秒後重試 (%d/%d): %s",
                        wait, attempt, self.max_retries, e,
                    )
                    import time
                    time.sleep(wait)
                else:
                    logger.error("TWT48U 請求失敗，已達最大重試次數: %s", e)
                    raise

        return []

    def _parse_row(self, row: List) -> Optional[Dict]:
        """
        解析一筆資料

        Args:
            row: 原始資料陣列

        Returns:
            解析後的資料字典，或 None（格式異常時）
        """
        try:
            # 解析日期（民國年 → 西元年）
            ex_date = self._parse_date(row[0])

            # 解析配息金額
            cash_dividend = self._parse_number(row[7])

            # 解析股票股利
            stock_dividend = self._parse_number(row[4])

            return {
                "code": row[1],
                "name": row[2],
                "ex_date": ex_date,
                "type": row[3],  # 權/息/權息
                "cash_dividend": cash_dividend,
                "stock_dividend": stock_dividend,
            }
        except (IndexError, ValueError) as e:
            logger.warning("解析 TWT48U 資料失敗: %s", e)
            return None

    def _parse_date(self, date_str: str) -> str:
        """
        解析民國年日期字串為西元年

        格式：115年08月21日 → 2026-08-21

        Args:
            date_str: 民國年日期字串

        Returns:
            西元年日期字串 (YYYY-MM-DD)
        """
        if not date_str:
            return ""

        # 匹配民國年格式
        match = re.match(r"(\d{2,3})年(\d{1,2})月(\d{1,2})日", date_str)
        if match:
            roc_year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))

            # 民國年轉西元年
            ad_year = roc_year + 1911
            return f"{ad_year:04d}-{month:02d}-{day:02d}"

        return date_str

    @staticmethod
    def _parse_number(text: str) -> float:
        """
        解析數字字串

        Args:
            text: 數字字串（可能包含 HTML 標籤）

        Returns:
            浮點數
        """
        if not text:
            return 0.0

        # 移除 HTML 標籤
        import re
        text = re.sub(r"<[^>]+>", "", text)

        # 清理字串
        cleaned = text.strip().replace(",", "").replace("--", "0")
        cleaned = cleaned.replace("\u3000", "")  # 全形空格

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_twt48u() -> List[Dict]:
    """
    抓取 TWT48U 資料（便捷包裝）

    Returns:
        配息資料列表
    """
    crawler = TWT48UCrawler()
    return crawler.fetch()
```

### 1.3 資料儲存邏輯

```python
"""
資料儲存 — TWT48U

檔案結構：
data/twses/
├── 2026-08.json    # 8月除息預告
├── 2026-09.json    # 9月除息預告
└── 2026-10.json    # 10月除息預告
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 專案根目錄
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data" / "twses"


def ensure_dirs():
    """確保資料目錄存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_twt48u(records: List[Dict]):
    """
    儲存 TWT48U 資料到月分檔案

    Args:
        records: 配息資料列表
    """
    ensure_dirs()

    # 依月份分組
    by_month: Dict[str, List[Dict]] = {}
    for rec in records:
        month = rec["ex_date"][:7]  # "2026-08"
        by_month.setdefault(month, []).append(rec)

    # 合併到各月檔案
    for month, new_records in by_month.items():
        filepath = DATA_DIR / f"{month}.json"

        # 讀取舊資料
        old_records = []
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                old_records = data.get("records", [])

        # 合併（以 code + ex_date 為 key 去重）
        merged = merge_records(old_records, new_records)

        # 寫入
        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "records": merged,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info("已儲存 %s.json：%d 筆", month, len(merged))


def merge_records(old: List[Dict], new: List[Dict]) -> List[Dict]:
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

#### data/twses/{YYYY-MM}.json

```json
{
  "last_updated": "2026-08-21",
  "records": [
    {
      "code": "00850",
      "name": "元大臺灣ESG永續",
      "ex_date": "2026-08-21",
      "type": "息",
      "cash_dividend": 0.85,
      "stock_dividend": 0.0
    },
    {
      "code": "00907",
      "name": "永豐優息存股",
      "ex_date": "2026-08-25",
      "type": "息",
      "cash_dividend": 0.24,
      "stock_dividend": 0.0
    }
  ]
}
```

---

## 2. 邊界條件處理

| 情境 | 處理方式 |
|------|---------|
| TWSE 限流（WAF 封鎖） | 加入完整 Headers，重試 3 次 |
| 回應格式異常 | 記錄錯誤，跳過該筆 |
| 資料為空 | 記錄警告，不寫入檔案 |
| 民國年格式異常 | 嘗試解析，失敗則保留原始值 |
| 舊資料合併 | 以 (code, ex_date) 為 key 去重 |

---

## 3. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 研究 TWT48U API 回應格式 | - |
| 2 | 實作 twse_twt48u.py 爬蟲 | #1 |
| 3 | 實作資料儲存邏輯 | #2 |
| 4 | 修改 fetch.py 整合 | #2, #3 |
| 5 | 測試：執行爬蟲並檢查資料 | #4 |

---

## 4. 驗收檢查清單

### 爬蟲執行
- [ ] `python crawler/fetch.py` 可正常執行
- [ ] 執行過程無紅色錯誤訊息
- [ ] 執行時間 < 30 秒

### 資料儲存
- [ ] `data/twses/` 有月分檔案（如 2026-08.json）
- [ ] 至少 10 支股票資料正確
- [ ] 每筆資料包含：code, name, ex_date, type, cash_dividend

### 資料格式
- [ ] ex_date 為西元年格式（YYYY-MM-DD）
- [ ] cash_dividend 為數字
- [ ] 重複執行不會產生重複資料

### 錯誤處理
- [ ] 網路失敗時有錯誤訊息
- [ ] 可重新執行不影響舊資料
