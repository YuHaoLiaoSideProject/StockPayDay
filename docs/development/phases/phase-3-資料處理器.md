# Phase 3 資料處理器 — 開發規格

> **對應 Roadmap**：Phase 3 — `docs/roadmaps/phases.md` 項目 #4
> **技術棧**：Python 3.11+ · pathlib · json · datetime
> **操作流程**：`docs/interaction-flows/phases/phase-3-資料處理器.md`
> **BDD**：`docs/bdds/stockpayday.feature`（LINE 通知、自動化部署、Edge Cases 相關 Scenario）
> **測試計畫**：`docs/test-plans/phases/phase-3-資料處理器測試計畫.md`
> **狀態**：設計完成，待開發

---

## 概述

將 `data/` 基底資料轉換為前端可用的 `api/` JSON 檔案，並可選地透過 LINE Notify 推播配息提醒。核心包含：

1. **Upcoming 生成器**：篩選未來配息，產出 `api/upcoming.json`
2. **Securities Index 生成器**：彙整所有證券清單，產出 `api/securities-index.json`
3. **Securities History 生成器**：每支證券產生獨立歷史檔案 `api/securities/{code}.json`
4. **LINE Notify 模組**：篩選 3 天內配息，推播 LINE 訊息

---

## 1. 後端實作規格

### 1.1 依賴新增

```bash
# 無額外第三方依賴，僅使用 Python 標準庫
# 若需 HTTP 推播 LINE Notify（processor/notify.py）：
pip install requests  # 已在 crawler/requirements.txt 中
```

### 1.2 檔案改動總覽

```
processor/
├── generate_api.py            ← 新增：主處理器腳本
├── generate_api_test.py       ← 新增：單元測試
├── integration_test.py        ← 新增：整合測試
└── notify.py                  ← 新增：LINE Notify 推播模組
```

> 輸入來源：`data/stocks/*.json`、`data/etfs/*.json`、`data/preferred/*.json`
> 輸出目標：`api/upcoming.json`、`api/securities-index.json`、`api/securities/*.json`

### 1.3 generate_api.py — 主處理器

```python
"""
資料處理器 — 將 data/ 基底資料轉換為 api/ 前端用 JSON

職責：
1. 讀取 data/{stocks,etfs,preferred}/*.json
2. 產生 api/upcoming.json（未來配息清單）
3. 產生 api/securities-index.json（證券清單）
4. 產生 api/securities/{code}.json（單股歷史）

使用方式：
    python processor/generate_api.py
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 專案路徑
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
API_DIR = ROOT_DIR / "api"

# 子目錄
DATA_SUBDIRS = ["stocks", "etfs", "preferred"]


def load_all_securities() -> List[Dict]:
    """
    從 data/ 目錄讀取所有證券基底資料

    遍歷 data/stocks/、data/etfs/、data/preferred/，
    讀取每個 JSON 檔案，合併為單一列表。

    Returns:
        證券資料列表，每筆包含 code, name, type, dividend_history 等欄位
    """
    securities = []
    for subdir in DATA_SUBDIRS:
        dir_path = DATA_DIR / subdir
        if not dir_path.exists():
            continue
        for json_file in sorted(dir_path.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                securities.append(data)
    return securities


def generate_upcoming(securities: List[Dict], today: Optional[str] = None) -> List[Dict]:
    """
    篩選未來配息，產生 upcoming 清單

    業務規則：
    - ex_date >= today（今天或未來）才納入
    - 每筆包含 code, name, type, ex_date, pay_date, dividend
    - 依 ex_date 升冪排序

    Args:
        securities: load_all_securities() 回傳的完整列表
        today: 用於測試覆蓋，預設為 datetime.now().strftime("%Y-%m-%d")

    Returns:
        upcoming 配息列表（已排序）
    """
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")

    upcoming = []
    for sec in securities:
        for record in sec.get("dividend_history", []):
            ex_date = record.get("ex_date", "")
            if ex_date >= today:
                upcoming.append({
                    "code": sec["code"],
                    "name": sec["name"],
                    "type": sec.get("type", "stock"),
                    "ex_date": ex_date,
                    "pay_date": record.get("pay_date", ""),
                    "dividend": record.get("cash_dividend", 0),
                })

    # 依 ex_date 升冪排序
    upcoming.sort(key=lambda x: x["ex_date"])
    return upcoming


def generate_securities_index(securities: List[Dict]) -> List[Dict]:
    """
    產生證券清單索引

    每筆包含 code, name，供前端搜尋功能使用。

    Args:
        securities: 完整證券列表

    Returns:
        證券索引列表
    """
    index = []
    for sec in securities:
        index.append({
            "code": sec["code"],
            "name": sec["name"],
        })
    return index


def generate_securities_history(
    securities: List[Dict],
    output_dir: Optional[Path] = None,
) -> None:
    """
    產出每支證券的歷史配息檔案

    每支證券一個 JSON 檔案：
    api/securities/{code}.json

    檔案格式：
    {
        "code": "2330",
        "name": "台積電",
        "history": [
            {"year": 2026, "ex_date": "2026-07-25", "dividend": 3.5},
            ...
        ]
    }

    Args:
        securities: 完整證券列表
        output_dir: 輸出目錄，預設為 api/securities/
    """
    if output_dir is None:
        output_dir = API_DIR / "securities"
    output_dir.mkdir(parents=True, exist_ok=True)

    for sec in securities:
        history = []
        for record in sec.get("dividend_history", []):
            history.append({
                "year": record.get("year"),
                "ex_date": record.get("ex_date", ""),
                "dividend": record.get("cash_dividend", 0),
            })

        # 依年份降冪排序
        history.sort(key=lambda x: x["year"] or 0, reverse=True)

        data = {
            "code": sec["code"],
            "name": sec["name"],
            "history": history,
        }

        filepath = output_dir / f"{sec['code']}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def save_api_file(data, filename: str, output_dir: Optional[Path] = None) -> Path:
    """
    將資料寫入 api/ 目錄的 JSON 檔案

    Args:
        data: 要序列化的 Python 物件
        filename: 檔案名稱（如 upcoming.json）
        output_dir: 輸出目錄，預設為 api/

    Returns:
        寫入的檔案路徑
    """
    if output_dir is None:
        output_dir = API_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def main():
    """
    主執行流程

    流程：
    1. 讀取所有基底資料
    2. 產生 upcoming.json
    3. 產生 securities-index.json
    4. 產生 securities/*.json
    5. 輸出統計資訊
    """
    print("🔄 開始產生 API 資料...")

    # 1. 讀取基底資料
    securities = load_all_securities()
    if not securities:
        print("❌ 找不到基底資料，請先執行爬蟲")
        return

    print(f"📊 讀取到 {len(securities)} 支證券")

    # 2. 產生 upcoming.json
    print("📅 篩選未來配息...")
    upcoming = generate_upcoming(securities)
    save_api_file(upcoming, "upcoming.json")
    print(f"   ✅ upcoming.json: {len(upcoming)} 筆未來配息")

    # 3. 產生 securities-index.json
    print("📋 產生證券清單...")
    index = generate_securities_index(securities)
    save_api_file(index, "securities-index.json")
    print(f"   ✅ securities-index.json: {len(index)} 支證券")

    # 4. 產生 securities/*.json
    print("📁 產生單股歷史...")
    generate_securities_history(securities)
    print(f"   ✅ securities/: {len(index)} 個檔案")

    # 5. 統計
    print(f"\n{'='*50}")
    print(f"✅ API 資料產生完成")
    print(f"   未來配息：{len(upcoming)} 筆")
    print(f"   證券總數：{len(index)} 支")
    print(f"   輸出目錄：{API_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
```

### 1.4 notify.py — LINE Notify 推播模組

```python
"""
LINE Notify 推播模組 — 篩選即將配息的證券並推播提醒

業務規則：
- 篩選 ex_date 在 3 天內的證券
- 推播格式：代號、名稱、除權息日、配息金額
- 無符合條件時不推播

使用方式：
    python processor/notify.py
    需設定環境變數 LINE_NOTIFY_TOKEN
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict

LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"


def filter_upcoming_3days(upcoming: List[Dict], today: Optional[str] = None) -> List[Dict]:
    """
    篩選 3 天內即將配息的證券

    Args:
        upcoming: upcoming.json 的內容
        today: 用於測試覆蓋

    Returns:
        符合條件的配息列表
    """
    if today is None:
        today = datetime.now()
    else:
        today = datetime.strptime(today, "%Y-%m-%d")

    deadline = today + timedelta(days=3)
    today_str = today.strftime("%Y-%m-%d")
    deadline_str = deadline.strftime("%Y-%m-%d")

    return [
        item for item in upcoming
        if today_str <= item["ex_date"] <= deadline_str
    ]


def format_notify_message(items: List[Dict]) -> str:
    """
    格式化 LINE 推播訊息

    格式範例：
    📢 配息提醒

    以下證券即將除權息：

    • 0056 元大高股息
      除權息日：2026-07-20
      配息金額：$1.80

    • 2330 台積電
      除權息日：2026-07-25
      配息金額：$3.50

    Args:
        items: 符合條件的配息列表

    Returns:
        格式化後的訊息字串
    """
    if not items:
        return ""

    lines = ["📢 配息提醒\n", "以下證券即將除權息：\n"]
    for item in items:
        lines.append(f"• {item['code']} {item['name']}")
        lines.append(f"  除權息日：{item['ex_date']}")
        lines.append(f"  配息金額：${item['dividend']:.2f}")
        lines.append("")

    return "\n".join(lines)


def send_line_notify(message: str, token: str) -> bool:
    """
    發送 LINE Notify 推播

    Args:
        message: 推播訊息
        token: LINE Notify Token

    Returns:
        是否成功
    """
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}

    try:
        response = requests.post(LINE_NOTIFY_API, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"❌ LINE 推播失敗: {e}")
        return False


def main():
    """
    主執行流程

    1. 讀取 api/upcoming.json
    2. 篩選 3 天內配息
    3. 有符合條件則推播，無則略過
    """
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    if not token:
        print("⚠️ 未設定 LINE_NOTIFY_TOKEN，跳過推播")
        return

    api_dir = Path(__file__).parent.parent / "api"
    upcoming_file = api_dir / "upcoming.json"

    if not upcoming_file.exists():
        print("⚠️ upcoming.json 不存在，請先執行 generate_api.py")
        return

    with open(upcoming_file, "r", encoding="utf-8") as f:
        upcoming = json.load(f)

    items = filter_upcoming_3days(upcoming)

    if not items:
        print("ℹ️ 無符合條件的配息（3 天內），不推播")
        return

    message = format_notify_message(items)
    success = send_line_notify(message, token)

    if success:
        print(f"✅ LINE 推播成功：{len(items)} 支證券")
    else:
        print("❌ LINE 推播失敗")


if __name__ == "__main__":
    main()
```

### 1.5 generate_api_test.py — 單元測試

```python
"""
單元測試 — generate_api 模組

覆蓋：
- generate_upcoming 日期篩選
- generate_securities_index 完整性
- generate_securities_history 檔案結構
- save_api_file 寫入正確性
"""
import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from generate_api import (
    generate_upcoming,
    generate_securities_index,
    generate_securities_history,
    save_api_file,
    load_all_securities,
)


class TestGenerateUpcoming:
    """測試 upcoming.json 產生"""

    def test_filters_future_dividends(self):
        """只包含今天及未來的配息"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "dividend_history": [
                {"year": 2026, "ex_date": yesterday, "cash_dividend": 3.0},
                {"year": 2027, "ex_date": tomorrow, "cash_dividend": 3.5},
            ],
        }]

        upcoming = generate_upcoming(securities, today=today)
        assert len(upcoming) == 1
        assert upcoming[0]["ex_date"] == tomorrow
        assert upcoming[0]["dividend"] == 3.5

    def test_includes_all_security_types(self):
        """包含所有證券類型（stock, etf, preferred）"""
        securities = [
            {"code": "2330", "name": "台積電", "type": "stock",
             "dividend_history": [{"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 3.5}]},
            {"code": "0050", "name": "元大台灣50", "type": "etf",
             "dividend_history": [{"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 1.8}]},
            {"code": "7654", "name": "某特別股", "type": "preferred",
             "dividend_history": [{"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 0.95}]},
        ]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert len(upcoming) == 3
        types = {u["type"] for u in upcoming}
        assert types == {"stock", "etf", "preferred"}

    def test_sorted_by_ex_date(self):
        """依 ex_date 升冪排序"""
        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "dividend_history": [
                {"year": 2027, "ex_date": "2099-03-01", "cash_dividend": 3.5},
                {"year": 2026, "ex_date": "2099-01-01", "cash_dividend": 3.0},
            ],
        }]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert upcoming[0]["ex_date"] == "2099-01-01"
        assert upcoming[1]["ex_date"] == "2099-03-01"

    def test_empty_when_all_past(self):
        """所有配息都在過去時回傳空列表"""
        securities = [{
            "code": "2330", "name": "台積電", "type": "stock",
            "dividend_history": [
                {"year": 2020, "ex_date": "2020-07-25", "cash_dividend": 3.0},
            ],
        }]

        upcoming = generate_upcoming(securities, today="2026-07-21")
        assert len(upcoming) == 0


class TestGenerateSecuritiesIndex:
    """測試 securities-index.json 產生"""

    def test_includes_all_securities(self):
        """包含所有證券的 code 和 name"""
        securities = [
            {"code": "2330", "name": "台積電"},
            {"code": "2317", "name": "鴻海"},
            {"code": "0050", "name": "元大台灣50"},
        ]

        index = generate_securities_index(securities)
        assert len(index) == 3
        codes = {i["code"] for i in index}
        assert codes == {"2330", "2317", "0050"}


class TestGenerateSecuritiesHistory:
    """測試單股歷史檔案產生"""

    def test_creates_one_file_per_security(self, tmp_path):
        """每支證券一個 JSON 檔案"""
        securities = [{
            "code": "2330",
            "name": "台積電",
            "dividend_history": [
                {"year": 2026, "ex_date": "2026-07-25", "cash_dividend": 3.5},
                {"year": 2025, "ex_date": "2025-07-18", "cash_dividend": 3.2},
            ],
        }]

        generate_securities_history(securities, output_dir=tmp_path)
        filepath = tmp_path / "2330.json"
        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)
        assert data["code"] == "2330"
        assert data["name"] == "台積電"
        assert len(data["history"]) == 2
        # 應依年份降冪
        assert data["history"][0]["year"] == 2026
        assert data["history"][1]["year"] == 2025

    def test_history_sorted_descending(self, tmp_path):
        """歷史依年份降冪排序"""
        securities = [{
            "code": "0050",
            "name": "元大台灣50",
            "dividend_history": [
                {"year": 2024, "ex_date": "2024-06-12", "cash_dividend": 1.5},
                {"year": 2026, "ex_date": "2026-07-20", "cash_dividend": 1.8},
                {"year": 2025, "ex_date": "2025-07-15", "cash_dividend": 1.6},
            ],
        }]

        generate_securities_history(securities, output_dir=tmp_path)
        with open(tmp_path / "0050.json") as f:
            data = json.load(f)
        years = [h["year"] for h in data["history"]]
        assert years == [2026, 2025, 2024]


class TestSaveApiFile:
    """測試 JSON 檔案寫入"""

    def test_writes_valid_json(self, tmp_path):
        """寫入的檔案可正確解析"""
        data = [{"code": "2330", "name": "台積電"}]
        filepath = save_api_file(data, "test.json", output_dir=tmp_path)
        assert filepath.exists()

        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == data
```

### 1.6 integration_test.py — 整合測試

```python
"""
整合測試 — 完整處理器流程

測試 data/ → processor → api/ 的端到端流程
"""
import pytest
import json
import time
from pathlib import Path
from generate_api import main as run_processor


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

        # monkeypatch 路徑
        import generate_api
        monkeypatch.setattr(generate_api, "DATA_DIR", data_dir)
        monkeypatch.setattr(generate_api, "API_DIR", tmp_path / "api")

        # 執行處理器
        run_processor()

        # 驗證 api/ 檔案
        api_dir = tmp_path / "api"
        assert (api_dir / "upcoming.json").exists()
        assert (api_dir / "securities-index.json").exists()
        assert (api_dir / "securities").exists()
        assert (api_dir / "securities" / "2330.json").exists()

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

        import generate_api
        monkeypatch.setattr(generate_api, "DATA_DIR", data_dir)
        monkeypatch.setattr(generate_api, "API_DIR", tmp_path / "api")

        run_processor()

        # 驗證每個 JSON 都可解析
        api_dir = tmp_path / "api"
        for json_file in api_dir.rglob("*.json"):
            with open(json_file) as f:
                json.load(f)  # 不拋出異常即為成功

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

        import generate_api
        monkeypatch.setattr(generate_api, "DATA_DIR", data_dir)
        monkeypatch.setattr(generate_api, "API_DIR", tmp_path / "api")

        start = time.time()
        run_processor()
        elapsed = time.time() - start

        assert elapsed < 30, f"處理時間 {elapsed:.1f}s 超過 30 秒上限"
```

---

## 2. 前端實作規格

不適用。本階段為純後端模組，無前端實作。

---

## 3. 不適用章節

本階段無 API endpoint、WebSocket、跨系統資料流、UI 元件或基礎架構設定，以下章節不適用：

- ~~3. API / Message 合約~~ — 本模組為本地腳本，無 HTTP API
- ~~4. 資料流~~ — 資料流已在「概述」及「後端實作規格」中以文字描述
- ~~5. 生命週期~~ — 無狀態管理或連線管理
- ~~7. CSS 關鍵樣式~~ — 無前端元件
- ~~9. 基礎架構設定~~ — Nginx/systemd 不涉及本模組

---

## 4. 資料流

```
data/stocks/*.json  ──┐
data/etfs/*.json    ──┼──→ load_all_securities() ──→ securities (List[Dict])
data/preferred/*.json┘                                        │
                                                              ├─→ generate_upcoming()      → api/upcoming.json
                                                              ├─→ generate_securities_index() → api/securities-index.json
                                                              └─→ generate_securities_history() → api/securities/{code}.json
```

後續（可選）：
```
api/upcoming.json ──→ notify.py filter_upcoming_3days() ──→ LINE Notify API
```

---

## 5. 邊界條件處理

| 情境 | 來源 | 處理方式 |
|------|------|---------|
| `data/` 目錄為空或不存在 | Interaction Flow 異常處理 | `load_all_securities()` 回傳空列表，main() 顯示錯誤訊息後退出 |
| 資料格式異常（缺欄位） | Interaction Flow 異常處理 | 使用 `.get()` 提供預設值，避免 KeyError |
| `api/` 寫入權限不足 | Interaction Flow 異常處理 | `mkdir(parents=True, exist_ok=True)` 自動建立；寫入失敗由 Python 拋出 PermissionError |
| 所有配息都在過去 | BDD Edge Case「無未來配息資料」 | `generate_upcoming()` 回傳空列表，`upcoming.json` 為 `[]`，前端顯示空狀態 |
| 單股無歷史配息資料 | BDD Edge Case「歷史資料為空」 | `history` 為空陣列 `[]`，前端顯示「暫無歷史配息資料」 |
| 某類證券目錄不存在 | Phase 2 整合考量 | `load_all_securities()` 跳過不存在的目錄，不中斷執行 |
| 無符合 3 天內配息 | BDD「無符合條件的配息」 | `filter_upcoming_3days()` 回傳空列表，不推播任何訊息 |
| LINE_NOTIFY_TOKEN 未設定 | notify.py | 跳過推播，僅列印警告訊息 |

---

## 6. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 實作 `generate_api.py` 核心函式（load_all_securities, generate_upcoming, generate_securities_index, generate_securities_history, save_api_file） | Phase 1-2 完成（data/ 有資料） |
| 2 | 實作 `generate_api_test.py` 單元測試 | #1 |
| 3 | 實作 `integration_test.py` 整合測試（含 tmp_path fixtures） | #1 |
| 4 | 執行測試並修正問題 | #2, #3 |
| 5 | 實作 `notify.py` LINE Notify 推播模組 | #1 |
| 6 | 端到端驗證：`python processor/generate_api.py` 執行正確 | #4 |
| 7 | 端到端驗證：`python processor/notify.py` 推播正確 | #5 |

---

## 7. BDD Scenario 對照表

| BDD Scenario | 對應實作 | 驗證方式 |
|-------------|---------|---------|
| 接收配息提醒通知 | `notify.py` → `filter_upcoming_3days()` + `send_line_notify()` | 單元測試 + 手動測試 |
| 無符合條件的配息 | `notify.py` → `filter_upcoming_3days()` 回傳空列表 | 單元測試 `test_empty_when_all_past` |
| GitHub Actions 每日自動執行 | `.github/workflows/update.yml` 中 `python processor/generate_api.py` | 手動觸發 workflow |
| GitHub Actions 手動觸發 | 同上 | 手動觸發 workflow |
| 單股資料不存在 | `generate_securities_history()` 產生空 `history: []` | 整合測試 |
| 歷史資料為空 | 同上，`history` 為 `[]` | 單元測試 |
| 無未來配息資料 | `generate_upcoming()` 回傳 `[]`，`upcoming.json` 為 `[]` | 單元測試 `test_empty_when_all_past` |

---

## 8. 驗收檢查清單

### API 產出
- [ ] `api/upcoming.json` 已產生
- [ ] `api/securities-index.json` 已產生
- [ ] `api/securities/` 目錄有單股歷史檔案

### 資料格式
- [ ] `upcoming.json` 只包含 `ex_date >= 今天` 的資料
- [ ] `upcoming.json` 每筆包含 code, name, type, ex_date, pay_date, dividend
- [ ] `upcoming.json` 依 ex_date 升冪排序
- [ ] `securities-index.json` 包含所有證券代號 + 名稱
- [ ] `securities/{code}.json` 每支證券一個檔案
- [ ] 單股歷史 `history` 陣列依年份降冪排序

### 執行驗證
- [ ] `python processor/generate_api.py` 可正常執行
- [ ] 執行時間 < 30 秒
- [ ] 無紅色錯誤訊息

### 測試
- [ ] 單元測試 100% 通過
- [ ] 整合測試 100% 通過
- [ ] 覆蓋所有 BDD Scenario（見 §7 對照表）

### LINE Notify（可選）
- [ ] `processor/notify.py` 可正常執行
- [ ] 3 天內配息正確推播
- [ ] 無符合條件時不推播
