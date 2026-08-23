# Phase 0 專案建置 — 開發規格

> **對應 Roadmap**：Phase 0 — `docs/roadmaps/phases.md` 項目 #1
> **技術棧**：Python 3.11+ · Vue 3 · Vite 5 · Tailwind CSS 3
> **操作流程**：`docs/interaction-flows/phases/phase-0-專案建置.md`
> **狀態**：設計完成，待開發

---

## 概述

建立專案骨架，讓開發環境可正常運作。核心包含：

1. **目錄結構**：建立符合 Tech Decision 規劃的完整目錄
2. **Python 環境**：虛擬環境 + requirements.txt
3. **Vue 前端**：Vite + Tailwind CSS 初始化
4. **版本控制**：.gitignore + README.md

---

## 1. 後端實作規格（Python 環境）

### 1.1 目錄結構建立

```
StockPayDay++/
├── crawler/                  ← 爬蟲目錄
│   ├── __init__.py
│   ├── fetch.py              ← 主腳本（空殼）
│   └── sources/              ← 爬蟲模組
│       └── __init__.py
├── processor/                ← 處理器目錄
│   ├── __init__.py
│   ├── generate_api.py       ← 主腳本（空殼）
│   └── notify.py             ← 通知腳本（空殼）
├── data/                     ← 基底資料（空目錄）
│   ├── raw/
│   ├── stocks/
│   ├── etfs/
│   └── preferred/
├── api/                      ← 前端用（空目錄）
│   └── securities/
├── frontend/                 ← Vue 前端
├── docs/                     ← 文件
├── .github/                  ← GitHub Actions
├── requirements.txt          ← Python 依賴
├── .gitignore
└── README.md
```

### 1.2 requirements.txt

```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
```

### 1.3 虛擬環境設定腳本（選用）

```bash
# setup.sh
#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ 虛擬環境設定完成"
```

### 1.4 環境變數設定

建立 `.env.example` 檔案：

```bash
# .env.example
# LINE Notify Token（用於推播通知）
LINE_NOTIFY_TOKEN=your_token_here

# TWSE 設定（選用）
TWSE_REQUEST_DELAY=2
TWSE_MAX_RETRIES=3
```

---

## 2. 前端實作規格

### 2.1 Vue + Vite + Tailwind 初始化

```bash
# 在 frontend/ 目錄下初始化
cd frontend
npm create vite@latest . -- --template vue
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
chmod +x setup.sh  # 如果有 setup.sh
```

### 2.2 tailwind.config.js 關鍵設定

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',  // 支援深色模式（Phase 8）
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### 2.3 src/style.css Tailwind 引入

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 2.4 檔案改動總覽

```
frontend/
├── index.html
├── package.json              ← 修改：加入 scripts
├── vite.config.js
├── tailwind.config.js        ← 新增
├── postcss.config.js         ← 新增（tailwind init 自動產生）
├── src/
│   ├── main.js
│   ├── App.vue               ← 修改：基礎佈局
│   ├── style.css             ← 修改：加入 Tailwind
│   └── components/           ← 空目錄
└── public/
```

---

## 3. 邊界條件處理

| 情境 | 處理方式 |
|------|---------|
| Python 版本過舊 | 檢查 `python --version`，需 3.11+ |
| Node.js 未安裝 | 安裝 Node.js 18+ |
| npm install 失敗 | 清除 node_modules 重試 |
| tailwindcss init 失敗 | 手動建立 tailwind.config.js |

---

## 4. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 建立根目錄結構 | - |
| 2 | 建立 requirements.txt | - |
| 3 | 設定 Python 虛擬環境 | #2 |
| 4 | 建立 frontend/ 目錄 | - |
| 5 | 初始化 Vue + Vite | #4 |
| 6 | 安裝並設定 Tailwind CSS | #5 |
| 7 | 建立 .gitignore | - |
| 8 | 建立 README.md | - |
| 9 | 驗證：pip install + npm run dev | #3, #6 |

---

## 5. 驗收檢查清單

### 目錄結構
- [ ] `crawler/` 目錄已建立
- [ ] `processor/` 目錄已建立
- [ ] `data/` 目錄已建立（含 raw, stocks, etfs, preferred 子目錄）
- [ ] `api/` 目錄已建立
- [ ] `frontend/` 目錄已建立

### Python 環境
- [ ] `requirements.txt` 已建立
- [ ] `pip install -r requirements.txt` 成功
- [ ] 虛擬環境可正常啟動

### 前端環境
- [ ] Vue + Vite 初始化成功
- [ ] Tailwind CSS 安裝並設定完成
- [ ] `npm run dev` 可正常啟動
- [ ] 瀏覽器可看到 Vue 預設頁面

### 版本控制
- [ ] `.gitignore` 已建立（含 venv, node_modules, __pycache__）
- [ ] `README.md` 已建立
- [ ] Git 可正常 commit
