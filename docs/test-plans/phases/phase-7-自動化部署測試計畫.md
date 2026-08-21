# 測試計畫：Phase 7 自動化部署（GitHub Actions）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 7 — 自動化部署 |
| **測試類型** | 整合測試、E2E 測試 |
| **工具** | GitHub Actions、Playwright |
| **BDD 對應** | GitHub Actions 自動化流程 |

---

## 1. 測試項目

### 1.1 Workflow 整合測試

| 測試項目 | 預期結果 | 測試方式 |
|----------|----------|----------|
| 手動觸發 | Workflow 執行成功 | GitHub UI |
| 爬蟲執行 | 資料更新 | 檢查 data/ |
| 處理器執行 | api/ 更新 | 檢查 api/ |
| 通知執行 | LINE 推播 | 檢查 LINE |
| 部署 | GitHub Pages 更新 | 瀏覽器訪問 |

### 1.2 E2E 部署測試

| 測試項目 | 預期結果 | 測試工具 |
|----------|----------|----------|
| 網站可訪問 | 200 OK | curl、Playwright |
| 資料正確 | 顯示最新資料 | Playwright |
| 功能正常 | 所有功能可用 | Playwright |

---

## 2. 測試案例

### 2.1 Workflow 手動觸發測試

```yaml
# .github/workflows/test-manual-trigger.yml
name: Test Manual Trigger

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Verify workflow runs
        run: |
          echo "✅ Workflow 手動觸發成功"
          echo "Current time: $(date)"
```

### 2.2 爬蟲執行測試

```yaml
# .github/workflows/test-crawler.yml
name: Test Crawler

on:
  workflow_dispatch:

jobs:
  test-crawler:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r crawler/requirements.txt
      
      - name: Run crawler
        run: python crawler/fetch.py
      
      - name: Verify data
        run: |
          echo "📋 檢查 data/ 目錄..."
          if [ -d "data/stocks" ]; then
            echo "✅ data/stocks/ 存在"
            ls -la data/stocks/ | head -10
          else
            echo "❌ data/stocks/ 不存在"
            exit 1
          fi
```

### 2.3 完整流程測試

```yaml
# .github/workflows/test-full-flow.yml
name: Test Full Flow

on:
  workflow_dispatch:

jobs:
  test-full:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r crawler/requirements.txt
      
      - name: Run crawler
        run: python crawler/fetch.py
      
      - name: Run processor
        run: python processor/generate_api.py
      
      - name: Run notify (dry run)
        run: python processor/notify.py --dry-run
        env:
          LINE_NOTIFY_TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
      
      - name: Verify API files
        run: |
          echo "📋 檢查 api/ 目錄..."
          if [ -f "api/upcoming.json" ]; then
            echo "✅ api/upcoming.json 存在"
            cat api/upcoming.json | head -20
          else
            echo "❌ api/upcoming.json 不存在"
            exit 1
          fi
          
          if [ -f "api/securities-index.json" ]; then
            echo "✅ api/securities-index.json 存在"
          else
            echo "❌ api/securities-index.json 不存在"
            exit 1
          fi
```

### 2.4 部署驗證測試

```typescript
// frontend/tests/e2e/deployment.spec.ts
import { test, expect } from '@playwright/test'

test.describe('部署驗證', () => {
  test('網站可訪問', async ({ page }) => {
    const response = await page.goto('/')
    expect(response?.status()).toBe(200)
  })
  
  test('顯示行事曆', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.calendar')).toBeVisible()
  })
  
  test('資料載入成功', async ({ page }) => {
    await page.goto('/')
    
    // 等待資料載入
    await page.waitForResponse('**/upcoming.json')
    
    // 驗證行事曆有資料
    await expect(page.locator('.has-dividend').first()).toBeVisible()
  })
  
  test('搜尋功能正常', async ({ page }) => {
    await page.goto('/')
    
    // 等待資料載入
    await page.waitForResponse('**/securities-index.json')
    
    // 測試搜尋
    await page.fill('input[placeholder*="搜尋"]', '2330')
    await expect(page.locator('.search-result')).toContainText('台積電')
  })
})
```

---

## 3. 測試執行

### 3.1 手動觸發測試

```bash
# 在 GitHub repo 執行
# 1. 前往 Actions 頁面
# 2. 選擇 "Update Dividend Data" workflow
# 3. 點擊 "Run workflow"
# 4. 等待執行完成
# 5. 檢查每個 step 的結果
```

### 3.2 本地測試

```bash
# 測試爬蟲
python crawler/fetch.py

# 測試處理器
python processor/generate_api.py

# 測試通知（dry run）
python processor/notify.py --dry-run

# 測試前端
cd frontend && npm run dev
```

### 3.3 E2E 測試

```bash
# 執行 Playwright 測試
cd frontend && npx playwright test tests/e2e/deployment.spec.ts
```

---

## 4. 驗收標準

### 4.1 Workflow 測試

| 標準 | 目標 |
|------|------|
| 手動觸發 | 可正常執行 |
| 爬蟲執行 | 資料更新成功 |
| 處理器執行 | api/ 更新成功 |
| 通知執行 | LINE 推播成功（或 dry run） |
| 部署 | GitHub Pages 更新 |

### 4.2 部署驗證

| 標準 | 目標 |
|------|------|
| 網站可訪問 | HTTP 200 |
| 資料正確 | 顯示最新資料 |
| 功能正常 | 所有功能可用 |
| 載入速度 | < 3 秒 |

---

## 5. 測試環境設定

### 5.1 GitHub Secrets

```yaml
# 需要設定的 Secrets
LINE_NOTIFY_TOKEN: "your-line-notify-token"
```

### 5.2 GitHub Pages 設定

```yaml
# Settings → Pages
Source: Deploy from a branch
Branch: gh-pages
```

---

## 6. 測試注意事項

1. **測試環境分離** — 使用測試 branch 或 fork 測試
2. **不要污染生產資料** — 測試用的 data/ 和 api/ 不要 commit
3. **監控 GitHub Actions** — 注意執行時間和次數限制
4. **驗證部署** — 每次部署後手動驗證網站
5. **日誌檢查** — 失敗時檢查 Actions 日誌
