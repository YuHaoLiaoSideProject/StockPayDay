# Phase 6 通知功能（LINE Notify） — 開發規格

> **技術棧**：Python 3.11+ · requests
> **Tech Decision**：`docs/tech-decision-stockpayday-2026-07-21.md`
> **操作流程**：`docs/interaction-flows/phases/phase-6-通知功能.md`
> **BDD**：`docs/bdds/stockpayday.feature`（LINE 通知章節）
> **測試計畫**：`docs/test-plans/phases/phase-6-通知功能測試計畫.md`
> **狀態**：設計完成，待開發

---

## 概述

配息日前自動推播 LINE 通知提醒使用者。核心包含：

1. **篩選模組**：從 `api/upcoming.json` 篩選 3 天內除權息的證券
2. **訊息格式化**：將篩選結果轉為可讀的推播訊息
3. **推播模組**：呼叫 LINE Notify API 發送訊息

> 此階段為純 Python 腳本（`processor/notify.py`），無前端互動，無 API endpoint。

---

## 1. 後端實作規格

### 1.1 依賴新增

```bash
# 若尚未安裝 requests
pip install requests
# 加入 crawler/requirements.txt
echo "requests>=2.31.0" >> crawler/requirements.txt
```

### 1.2 檔案改動總覽

```
processor/
├── notify.py                 ← 新增：LINE Notify 推播腳本（主模組）
├── test_notify.py            ← 新增：單元測試
└── test_integration.py       ← 新增：整合測試
```

### 1.3 notify.py — 主模組

職責：讀取 upcoming.json → 篩選 → 格式化 → 推播 LINE Notify。作為獨立腳本執行，可整合至 GitHub Actions 工作流程。

```python
"""
LINE Notify 推播腳本

功能：
- 讀取 api/upcoming.json
- 篩選 3 天內除權息的證券
- 格式化為推播訊息
- 呼叫 LINE Notify API 發送

使用方式：
    python processor/notify.py

環境變數：
    LINE_NOTIFY_TOKEN: LINE Notify 推播 Token（必填）

前置條件：
    api/upcoming.json 必須已由 processor/generate_api.py 產出
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

import requests

# 專案根目錄
ROOT_DIR = Path(__file__).parent.parent
API_DIR = ROOT_DIR / "api"

# LINE Notify API
LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"

# 篩選天數
FILTER_DAYS = 3

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_upcoming(api_dir: Path = API_DIR) -> List[Dict]:
    """
    讀取 upcoming.json

    Args:
        api_dir: api 目錄路徑

    Returns:
        配息證券列表，若檔案不存在或解析失敗則回傳空列表
    """
    filepath = api_dir / "upcoming.json"

    if not filepath.exists():
        logger.warning(f"找不到 upcoming.json: {filepath}")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.error("upcoming.json 格式錯誤：應為 JSON 陣列")
            return []

        return data

    except json.JSONDecodeError as e:
        logger.error(f"upcoming.json 解析失敗: {e}")
        return []


def filter_upcoming_by_days(
    upcoming: List[Dict],
    days: int = FILTER_DAYS,
    reference_date: Optional[datetime] = None,
) -> List[Dict]:
    """
    篩選指定天數內除權息的證券

    Args:
        upcoming: 配息證券列表（每筆需含 ex_date 欄位，格式 YYYY-MM-DD）
        days: 篩選天數（預設 3 天）
        reference_date: 參考日期（預設為今天，測試用）

    Returns:
        篩選後的證券列表
    """
    if not upcoming:
        return []

    if reference_date is None:
        reference_date = datetime.now()

    # 計算截止日期（今天 + days 天的 23:59:59）
    deadline = reference_date.replace(hour=23, minute=59, second=59) + timedelta(days=days)

    filtered = []
    for stock in upcoming:
        ex_date_str = stock.get("ex_date")
        if not ex_date_str:
            continue

        try:
            ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"無效的 ex_date 格式: {ex_date_str}（證券: {stock.get('code')}）")
            continue

        # 篩選條件：ex_date 在 [reference_date, deadline] 範圍內
        if reference_date <= ex_date <= deadline:
            filtered.append(stock)

    # 按除權息日排序（近的在前）
    filtered.sort(key=lambda s: s.get("ex_date", ""))

    return filtered


def format_message(stocks: List[Dict]) -> str:
    """
    將篩選結果格式化為推播訊息

    訊息格式：
        📢 配息提醒

        以下證券即將除權息：

        • {代號} {名稱}
          除權息日：{ex_date}
          配息金額：${dividend}

    Args:
        stocks: 篩選後的證券列表

    Returns:
        格式化後的訊息字串
    """
    if not stocks:
        return ""

    lines = ["📢 配息提醒", "", "以下證券即將除權息：", ""]

    for stock in stocks:
        code = stock.get("code", "???")
        name = stock.get("name", "未知")
        ex_date = stock.get("ex_date", "未知")
        dividend = stock.get("dividend", 0)

        lines.append(f"• {code} {name}")
        lines.append(f"  除權息日：{ex_date}")
        lines.append(f"  配息金額：${dividend}")
        lines.append("")

    return "\n".join(lines).rstrip()


def send_line_notify(token: str, message: str) -> bool:
    """
    呼叫 LINE Notify API 發送訊息

    Args:
        token: LINE Notify Token
        message: 推播訊息

    Returns:
        True 表示成功，False 表示失敗
    """
    if not token:
        logger.error("LINE Notify Token 未設定")
        return False

    if not message:
        logger.warning("推播訊息為空，跳過推播")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
    }

    data = {
        "message": message,
    }

    try:
        response = requests.post(
            LINE_NOTIFY_API,
            headers=headers,
            data=data,
            timeout=30,
        )

        if response.status_code == 200:
            logger.info("✅ LINE Notify 推播成功")
            return True
        else:
            logger.error(
                f"❌ LINE Notify 推播失敗: HTTP {response.status_code} — {response.text}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.error("❌ LINE Notify API 請求逾時")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ LINE Notify API 連線失敗")
        return False
    except Exception as e:
        logger.error(f"❌ LINE Notify 推播例外: {e}")
        return False


def main(api_dir: Path = API_DIR) -> bool:
    """
    主執行流程

    流程：
        1. 讀取 upcoming.json
        2. 篩選 3 天內除權息的證券
        3. 若無符合條件則結束
        4. 格式化訊息
        5. 呼叫 LINE Notify 推播
        6. 記錄結果

    Args:
        api_dir: api 目錄路徑

    Returns:
        True 表示推播成功或無需推播，False 表示推播失敗
    """
    logger.info("🔔 開始執行通知腳本...")

    # 1. 讀取 upcoming.json
    upcoming = load_upcoming(api_dir)
    if not upcoming:
        logger.info("ℹ️ upcoming.json 為空或不存在，無需推播")
        return True

    # 2. 篩選 3 天內除權息
    filtered = filter_upcoming_by_days(upcoming)

    # 3. 無符合條件 → 結束
    if not filtered:
        logger.info("ℹ️ 無符合條件的證券（3 天內無除權息），不推播")
        return True

    logger.info(f"📋 找到 {len(filtered)} 支即將除權息的證券")

    # 4. 格式化訊息
    message = format_message(filtered)

    # 5. 取得 Token
    token = os.environ.get("LINE_NOTIFY_TOKEN", "")
    if not token:
        logger.error("❌ 環境變數 LINE_NOTIFY_TOKEN 未設定")
        return False

    # 6. 推播
    success = send_line_notify(token, message)

    if success:
        logger.info("✅ 通知推播完成")
    else:
        logger.error("❌ 通知推播失敗")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

### 1.4 測試檔案

#### test_notify.py — 單元測試

```python
"""
notify.py 單元測試

測試項目：
- filter_upcoming_by_days: 篩選邏輯
- format_message: 訊息格式化
- send_line_notify: API 呼叫（mock）
"""
import pytest
from datetime import datetime, timedelta
from notify import filter_upcoming_by_days, format_message, send_line_notify, load_upcoming


class TestFilterUpcomingByDays:
    """篩選配息證券測試"""

    def test_filters_within_3_days(self):
        """測試篩選 3 天內配息"""
        today = datetime(2026, 7, 21)

        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-22"},
            {"code": "0056", "name": "元大高股息", "ex_date": "2026-07-28"},
            {"code": "0050", "name": "元大台灣50", "ex_date": "2026-07-23"},
        ]

        result = filter_upcoming_by_days(upcoming, days=3, reference_date=today)

        assert len(result) == 2
        codes = [r["code"] for r in result]
        assert "2330" in codes
        assert "0050" in codes
        assert "0056" not in codes

    def test_empty_when_no_upcoming(self):
        """測試無配息時回傳空列表"""
        result = filter_upcoming_by_days([], days=3)
        assert result == []

    def test_empty_when_all_past(self):
        """測試所有配息已過時回傳空列表"""
        today = datetime(2026, 7, 21)

        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-20"},
        ]

        result = filter_upcoming_by_days(upcoming, days=3, reference_date=today)
        assert result == []

    def test_includes_same_day(self):
        """測試包含當天除權息"""
        today = datetime(2026, 7, 21)

        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-21"},
        ]

        result = filter_upcoming_by_days(upcoming, days=3, reference_date=today)
        assert len(result) == 1

    def test_includes_deadline_day(self):
        """測試包含截止日當天"""
        today = datetime(2026, 7, 21)

        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-24"},
        ]

        result = filter_upcoming_by_days(upcoming, days=3, reference_date=today)
        assert len(result) == 1

    def test_excludes_after_deadline(self):
        """測試排除超過截止日"""
        today = datetime(2026, 7, 21)

        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25"},
        ]

        result = filter_upcoming_by_days(upcoming, days=3, reference_date=today)
        assert len(result) == 0

    def test_sorts_by_ex_date(self):
        """測試按除權息日排序"""
        today = datetime(2026, 7, 21)

        upcoming = [
            {"code": "0050", "name": "元大台灣50", "ex_date": "2026-07-23"},
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-22"},
        ]

        result = filter_upcoming_by_days(upcoming, days=3, reference_date=today)
        assert result[0]["code"] == "2330"
        assert result[1]["code"] == "0050"


class TestFormatMessage:
    """訊息格式化測試"""

    def test_format_single_stock(self):
        """測試單支股票格式化"""
        stocks = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25", "dividend": 3.5}
        ]

        message = format_message(stocks)

        assert "2330" in message
        assert "台積電" in message
        assert "2026-07-25" in message
        assert "3.5" in message

    def test_format_multiple_stocks(self):
        """測試多支股票格式化"""
        stocks = [
            {"code": "2330", "name": "台積電", "ex_date": "2026-07-25", "dividend": 3.5},
            {"code": "0050", "name": "元大台灣50", "ex_date": "2026-07-28", "dividend": 2.1},
        ]

        message = format_message(stocks)

        assert "2330" in message
        assert "0050" in message
        assert "📢" in message

    def test_format_includes_header(self):
        """測試包含標題"""
        stocks = [{"code": "2330", "name": "台積電", "ex_date": "2026-07-25", "dividend": 3.5}]

        message = format_message(stocks)

        assert "配息提醒" in message

    def test_format_empty_returns_empty(self):
        """測試空列表回傳空字串"""
        message = format_message([])
        assert message == ""


class TestSendLineNotify:
    """LINE Notify 推播測試"""

    def test_send_success(self, monkeypatch):
        """測試推播成功"""
        import requests as req

        mock_response = req.Response()
        mock_response.status_code = 200
        mock_response._content = b'{"message":"ok"}'

        def mock_post(*args, **kwargs):
            return mock_response

        monkeypatch.setattr("requests.post", mock_post)

        result = send_line_notify("test_token", "test_message")
        assert result is True

    def test_send_failure(self, monkeypatch):
        """測試推播失敗（401）"""
        import requests as req

        mock_response = req.Response()
        mock_response.status_code = 401
        mock_response._content = b'{"message":"invalid token"}'

        def mock_post(*args, **kwargs):
            return mock_response

        monkeypatch.setattr("requests.post", mock_post)

        result = send_line_notify("invalid_token", "test_message")
        assert result is False

    def test_send_empty_token(self):
        """測試空 Token"""
        result = send_line_notify("", "test_message")
        assert result is False

    def test_send_empty_message(self):
        """測試空訊息"""
        result = send_line_notify("test_token", "")
        assert result is False
```

#### test_integration.py — 整合測試

```python
"""
notify.py 整合測試

測試項目：
- full_notify_flow: 完整推播流程
- no_upcoming_no_notify: 無符合條件不推播
- invalid_token_error: Token 無效有錯誤
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta


class TestNotifyIntegration:
    """通知整合測試"""

    def test_full_notify_flow(self, tmp_path, monkeypatch):
        """測試完整通知流程"""
        from notify import main as run_notify

        # 準備 upcoming.json
        api_dir = tmp_path / "api"
        api_dir.mkdir()

        today = datetime.now()
        upcoming = [
            {
                "code": "2330",
                "name": "台積電",
                "ex_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                "dividend": 3.5,
            }
        ]
        (api_dir / "upcoming.json").write_text(json.dumps(upcoming))

        # Mock LINE Notify API
        import requests as req

        mock_response = req.Response()
        mock_response.status_code = 200
        mock_response._content = b'{"message":"ok"}'

        def mock_post(*args, **kwargs):
            return mock_response

        monkeypatch.setattr("requests.post", mock_post)
        monkeypatch.setenv("LINE_NOTIFY_TOKEN", "test_token")

        # 執行通知
        success = run_notify(api_dir=api_dir)
        assert success is True

    def test_no_upcoming_no_notify(self, tmp_path, monkeypatch):
        """測試無符合條件不推播"""
        from notify import main as run_notify

        api_dir = tmp_path / "api"
        api_dir.mkdir()

        # 空的 upcoming
        (api_dir / "upcoming.json").write_text("[]")

        # 追蹤 API 呼叫次數
        call_count = 0

        import requests as req

        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return req.Response()

        monkeypatch.setattr("requests.post", mock_post)
        monkeypatch.setenv("LINE_NOTIFY_TOKEN", "test_token")

        # 執行通知
        success = run_notify(api_dir=api_dir)
        assert success is True
        assert call_count == 0  # 不應呼叫 API

    def test_invalid_token_error(self, tmp_path, monkeypatch):
        """測試 Token 無效時回傳失敗"""
        from notify import main as run_notify

        api_dir = tmp_path / "api"
        api_dir.mkdir()

        today = datetime.now()
        upcoming = [
            {
                "code": "2330",
                "name": "台積電",
                "ex_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                "dividend": 3.5,
            }
        ]
        (api_dir / "upcoming.json").write_text(json.dumps(upcoming))

        # Mock LINE Notify API 返回 401
        import requests as req

        mock_response = req.Response()
        mock_response.status_code = 401
        mock_response._content = b'{"message":"invalid token"}'

        def mock_post(*args, **kwargs):
            return mock_response

        monkeypatch.setattr("requests.post", mock_post)
        monkeypatch.setenv("LINE_NOTIFY_TOKEN", "invalid_token")

        # 執行通知（應該失敗但不崩潰）
        success = run_notify(api_dir=api_dir)
        assert success is False

    def test_missing_upcoming_file(self, tmp_path, monkeypatch):
        """測試 upcoming.json 不存在"""
        from notify import main as run_notify

        api_dir = tmp_path / "api"
        api_dir.mkdir()

        monkeypatch.setenv("LINE_NOTIFY_TOKEN", "test_token")

        # 執行通知（應該正常結束，不推播）
        success = run_notify(api_dir=api_dir)
        assert success is True
```

---

## 2. 邊界條件處理

| 情境 | 來源 | 處理方式 |
|------|------|---------|
| upcoming.json 不存在 | BDD @edge-case | 記錄 warning，回傳 True（無需推播） |
| upcoming.json 格式錯誤 | 邊界情況 | 記錄 error，回傳空列表 |
| LINE Notify Token 未設定 | BDD @edge-case | 記錄 error，回傳 False |
| LINE Notify Token 無效（401） | BDD @edge-case | 記錄 error，回傳 False |
| LINE Notify API 失敗（5xx） | 互動流程異常 | 記錄 error，回傳 False |
| LINE Notify API 逾時 | 邊界情況 | 記錄 error，回傳 False |
| 所有配息已過期 | 互動流程 | 篩選結果為空，不推播 |
| ex_date 格式無效 | 邊界情況 | 記錄 warning，跳過該筆 |
| 無符合 3 天內條件 | BDD @edge-case | 記錄 info，不推播 |

---

## 3. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 建立 `processor/notify.py` 基本骨架（import、常數、logging） | - |
| 2 | 實作 `load_upcoming()` 讀取 JSON | #1 |
| 3 | 實作 `filter_upcoming_by_days()` 篩選邏輯 | #1 |
| 4 | 實作 `format_message()` 訊息格式化 | #1 |
| 5 | 實作 `send_line_notify()` API 呼叫 | #1 |
| 6 | 實作 `main()` 主流程串接 | #2, #3, #4, #5 |
| 7 | 撰寫 `test_notify.py` 單元測試 | #3, #4, #5 |
| 8 | 撰寫 `test_integration.py` 整合測試 | #6 |
| 9 | 執行測試並驗證 | #7, #8 |

---

## 4. 環境變數

| 變數 | 必填 | 說明 | 範例 |
|------|:---:|------|------|
| `LINE_NOTIFY_TOKEN` | ✅ | LINE Notify 推播 Token | `xxxxx` |

取得方式：
1. 前往 [LINE Notify](https://notify-bot.line.me/) 登入
2. 建立 Personal Access Token
3. 設定至 GitHub Secrets 或本地環境變數

---

## 5. GitHub Actions 整合

```yaml
# .github/workflows/update.yml 中新增步驟
- name: Notify
  if: success()
  run: python processor/notify.py
  env:
    LINE_NOTIFY_TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
```

執行順序：`fetch.py → generate_api.py → notify.py`

---

## 6. 驗收檢查清單

### 腳本執行
- [ ] `python processor/notify.py` 可正常執行
- [ ] 無紅色錯誤訊息

### 資料篩選
- [ ] 正確讀取 `api/upcoming.json`
- [ ] 篩選 `ex_date` 在 3 天內的證券
- [ ] 無符合條件時不推播

### 推播功能
- [ ] 呼叫 LINE Notify API 成功
- [ ] 推播訊息包含：代號、名稱、除權息日、配息金額
- [ ] 訊息格式清晰易讀

### 錯誤處理
- [ ] Token 無效時有錯誤訊息
- [ ] API 失敗時有記錄日誌
- [ ] 不會因錯誤中斷整個流程

---

## 7. BDD Scenario 對照表

| BDD Scenario | 對應規格章節 |
|--------------|-------------|
| 接收配息提醒通知 | 1.3 `main()` → `filter_upcoming_by_days()` → `format_message()` → `send_line_notify()` |
| 無符合條件的配息 | 1.3 `main()` → `filter_upcoming_by_days()` 回傳空列表 → 記錄 info 不推播 |
| GitHub Actions 每日自動執行 | 4. GitHub Actions 整合（`notify.py` 步驟） |
| GitHub Actions 手動觸發 | 4. GitHub Actions 整合（`workflow_dispatch`） |
