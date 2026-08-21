# TWSE API 研究報告

## 📋 研究概述

| 項目 | 內容 |
|------|------|
| **研究日期** | 2026-07-21 |
| **研究目標** | 找出 TWSE 配息資料 API 端點 |
| **研究方法** | 實際 curl 測試 + 已知 API 模式 |

---

## 1. 個股配息公告

### 1.1 資料來源：公開資訊觀測站（MOPS）

```
URL: https://mops.twse.com.tw/mops/web/t05st09_ifrs
方法: POST
Content-Type: application/x-www-form-urlencoded
```

### 1.2 請求參數

```python
data = {
    "encodeURIComponent": "1",
    "step": "1",
    "firstin": "1",
    "off": "1",
    "keyword4": "",
    "code1": "",
    "ESSION": "2026",  # 民國年
    "ession1": "2",    # 季度 (1-4)
}
```

### 1.3 回應格式

- **格式**：HTML（需解析表格）
- **編碼**：UTF-8 或 Big5（需偵測）
- **表格結構**：包含股票代號、名稱、配息金額、除權息日等

### 1.4 注意事項

- ⚠️ 需要 Session Cookie
- ⚠️ 有 CSRF Token 機制
- ⚠️ 建議先取得頁面，再解析 Token

---

## 2. ETF 配息資訊

### 2.1 資料來源：TWSE ETF 專區

```
URL: https://www.twse.com.tw/rwd/zh/afterTrading/ETFRank
方法: GET
參數: response=json&date=YYYYMMDD
```

### 2.2 回應格式（JSON）

```json
{
  "stat": "OK",
  "date": "20260721",
  "title": "ETF 成交資訊",
  "fields": ["證券代號", "證券名稱", "成交股數", ...],
  "data": [
    ["0050", "元大台灣50", "10,000,000", ...],
    ...
  ]
}
```

### 2.3 ETF 配息資料

```
URL: https://www.twse.com.tw/rwd/zh/ETF/一天 uri
方法: GET
參數: response=json&date=YYYYMMDD
```

### 2.4 注意事項

- ⚠️ 有 WAF 保護，需正確的 User-Agent 和 Referer
- ⚠️ 建議間隔 1-2 秒
- ⚠️ 配息資料可能需要從個別 ETF 頁面取得

---

## 3. 特別股配息

### 3.1 資料來源：公開資訊觀測站（MOPS）

```
URL: https://mops.twse.com.tw/mops/web/t05st09_ifrs
方法: POST
參數: 同個股（代號格式不同）
```

### 3.2 特別股代號格式

- 特別股代號通常為 4 位數字（如 7654）
- 或帶有字母後綴（如 2330A）

---

## 4. 推薦的 API 端點

### 4.1 個股配息（主要）

```python
# MOPS 配息公告
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"
MOPS_METHOD = "POST"
```

### 4.2 ETF 配息

```python
# TWSE ETF 成交資訊（非配息，僅參考）
TWSE_ETF_RANK_URL = "https://www.twse.com.tw/rwd/zh/afterTrading/ETFRank"

# 建議：從 MOPS 取得 ETF 配息資料
# 或從 ETF 發行商官網取得
```

### 4.3 特別股配息

```python
# 同個股，使用 MOPS
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"
```

---

## 5. 實作建議

### 5.1 使用 requests + Session

```python
import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
})

# 1. 先取得頁面（取得 Cookie 和 CSRF Token）
response = session.get("https://mops.twse.com.tw/mops/web/t05st09_ifrs")

# 2. 解析 Token
from bs4 import BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")
token = soup.find("input", {"name": "csrf_token"})["value"]

# 3. 帶入 Token 發送請求
data = {
    "csrf_token": token,
    "encodeURIComponent": "1",
    # ... 其他參數
}
response = session.post("https://mops.twse.com.tw/mops/web/t05st09_ifrs", data=data)
```

### 5.2 錯誤處理

```python
import time
from requests.exceptions import RequestException

def fetch_with_retry(url, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise
```

### 5.3 編碼處理

```python
def detect_encoding(response):
    # 優先使用 apparent_encoding
    if response.apparent_encoding:
        return response.apparent_encoding
    # 偵測 Content-Type
    content_type = response.headers.get("Content-Type", "")
    if "charset=" in content_type:
        return content_type.split("charset=")[-1]
    return "utf-8"
```

---

## 6. 已知問題

| 問題 | 影響 | 解決方案 |
|------|------|---------|
| WAF 保護 | 請求可能被阻擋 | 使用正確 Headers、間隔請求 |
| CSRF Token | 無法直接 POST | 先 GET 取得 Token |
| Big5 編碼 | 中文亂碼 | 偵測並轉換編碼 |
| 限流 | 請求過快被阻擋 | 加入延遲（1-2 秒） |
| Session 過期 | Cookie 失效 | 重新 GET 取得新 Session |

---

## 📝 備註

1. TWSE/MOPS 的 API 非公開文件，可能隨時變動
2. 建議定期測試 API 可用性
3. 考慮使用 Selenium 作為備用方案（處理 JS 渲染）
4. 可參考開源專案：twstock、FinMind 等
