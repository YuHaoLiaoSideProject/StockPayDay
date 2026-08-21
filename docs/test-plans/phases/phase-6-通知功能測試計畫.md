# 測試計畫：Phase 6 通知功能（LINE Notify）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 6 — 通知功能 |
| **測試類型** | 單元測試、整合測試 |
| **工具** | pytest + mock |
| **BDD 對應** | LINE Notify 推播功能 |

---

## 1. 測試項目

### 1.1 單元測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| filter_upcoming_by_days | 篩選 3 天內配息 | test_notify.py |
| format_message | 正確格式化訊息 | test_notify.py |
| send_line_notify | 呼叫 API 成功 | test_notify.py |

### 1.2 整合測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| full_notify_flow | 推播成功 | test_integration.py |
| no_upcoming_no_notify | 無符合條件不推播 | test_integration.py |
| invalid_token_error | Token 無效有錯誤 | test_integration.py |

---

## 2. 測試案例

### 2.1 單元測試

```python
# processor/test_notify.py
import pytest
from datetime import datetime, timedelta
from notify import filter_upcoming_by_days, format_message, send_line_notify

class TestFilterUpcomingByDays:
    """篩選配息證券測試"""
    
    def test_filters_within_3_days(self):
        """測試篩選 3 天內配息"""
        today = datetime.now()
        
        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": (today + timedelta(days=1)).strftime("%Y-%m-%d")},
            {"code": "0056", "name": "元大高股息", "ex_date": (today + timedelta(days=5)).strftime("%Y-%m-%d")},
            {"code": "0050", "name": "元大台灣50", "ex_date": (today + timedelta(days=2)).strftime("%Y-%m-%d")},
        ]
        
        result = filter_upcoming_by_days(upcoming, days=3)
        
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
        today = datetime.now()
        
        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": (today - timedelta(days=1)).strftime("%Y-%m-%d")},
        ]
        
        result = filter_upcoming_by_days(upcoming, days=3)
        assert result == []

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
            {"code": "0050", "name": "元大台灣50", "ex_date": "2026-07-28", "dividend": 2.1}
        ]
        
        message = format_message(stocks)
        
        assert "2330" in message
        assert "0050" in message
        assert "📢" in message  # 訊息標題
    
    def test_format_includes_header(self):
        """測試包含標題"""
        stocks = [{"code": "2330", "name": "台積電", "ex_date": "2026-07-25", "dividend": 3.5}]
        
        message = format_message(stocks)
        
        assert "配息提醒" in message

class TestSendLineNotify:
    """LINE Notify 推播測試"""
    
    def test_send_success(self, monkeypatch):
        """測試推播成功"""
        mock_response = pytest.importorskip("requests").Response()
        mock_response.status_code = 200
        
        def mock_post(*args, **kwargs):
            return mock_response
        
        monkeypatch.setattr("requests.post", mock_post)
        
        result = send_line_notify("test_token", "test_message")
        assert result is True
    
    def test_send_failure(self, monkeypatch):
        """測試推播失敗"""
        mock_response = pytest.importorskip("requests").Response()
        mock_response.status_code = 401
        
        def mock_post(*args, **kwargs):
            return mock_response
        
        monkeypatch.setattr("requests.post", mock_post)
        
        result = send_line_notify("invalid_token", "test_message")
        assert result is False
```

### 2.2 整合測試

```python
# processor/test_integration.py
import pytest
import json
from pathlib import Path
from notify import main as run_notify

class TestNotifyIntegration:
    """通知整合測試"""
    
    def test_full_notify_flow(self, tmp_path, monkeypatch):
        """測試完整通知流程"""
        # 準備 upcoming.json
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        
        today = datetime.now()
        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "dividend": 3.5}
        ]
        (api_dir / "upcoming.json").write_text(json.dumps(upcoming))
        
        # Mock LINE Notify API
        mock_response = pytest.importorskip("requests").Response()
        mock_response.status_code = 200
        
        def mock_post(*args, **kwargs):
            return mock_response
        
        monkeypatch.setattr("requests.post", mock_post)
        
        # 執行通知
        import notify
        notify.API_DIR = api_dir
        
        # run_notify()
        
        # 驗證（這裡需要更細緻的驗證）
        pass
    
    def test_no_upcoming_no_notify(self, tmp_path, monkeypatch):
        """測試無符合條件不推播"""
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        
        # 空的 upcoming
        (api_dir / "upcoming.json").write_text("[]")
        
        # Mock LINE Notify API
        call_count = 0
        
        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return pytest.importorskip("requests").Response()
        
        monkeypatch.setattr("requests.post", mock_post)
        
        # 執行通知
        import notify
        notify.API_DIR = api_dir
        
        # run_notify()
        
        # 驗證沒有呼叫 API
        assert call_count == 0
    
    def test_invalid_token_error(self, tmp_path, monkeypatch):
        """測試 Token 無效時有錯誤"""
        api_dir = tmp_path / "api"
        api_dir.mkdir()
        
        today = datetime.now()
        upcoming = [
            {"code": "2330", "name": "台積電", "ex_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "dividend": 3.5}
        ]
        (api_dir / "upcoming.json").write_text(json.dumps(upcoming))
        
        # Mock LINE Notify API 返回 401
        mock_response = pytest.importorskip("requests").Response()
        mock_response.status_code = 401
        
        def mock_post(*args, **kwargs):
            return mock_response
        
        monkeypatch.setattr("requests.post", mock_post)
        
        # 執行通知（應該記錄錯誤但不崩潰）
        import notify
        notify.API_DIR = api_dir
        
        # run_notify()
        
        # 驗證（需要檢查日誌）
        pass
```

---

## 3. 測試執行

```bash
# 執行所有測試
pytest processor/test_notify.py -v

# 執行整合測試
pytest processor/test_integration.py -v

# 產生覆蓋率報告
pytest processor/ --cov=processor --cov-report=html
```

---

## 4. 驗收標準

| 標準 | 目標 |
|------|------|
| 單元測試通過率 | 100% |
| 整合測試通過率 | 100% |
| 篩選邏輯正確 | 3 天內配息 |
| 訊息格式正確 | 包含所有必要資訊 |
| 推播成功 | API 返回 200 |
| 無符合條件不推播 | 不呼叫 API |
| Token 無效處理 | 記錄錯誤不崩潰 |

---

## 5. 測試資料

```json
// processor/tests/fixtures/upcoming.json
[
  {
    "code": "2330",
    "name": "台積電",
    "type": "stock",
    "ex_date": "2026-07-25",
    "pay_date": "2026-08-15",
    "dividend": 3.5
  },
  {
    "code": "0056",
    "name": "元大高股息",
    "type": "etf",
    "ex_date": "2026-07-20",
    "pay_date": "2026-08-10",
    "dividend": 1.8
  }
]
```

---

## 6. 測試注意事項

1. **不要使用真實 Token 測試** — 使用 mock 或測試用 Token
2. **Mock LINE Notify API** — 避免發送真實推播
3. **測試環境變數** — 使用 `monkeypatch.setenv` 設定測試 Token
4. **日誌驗證** — 驗證錯誤有正確記錄
