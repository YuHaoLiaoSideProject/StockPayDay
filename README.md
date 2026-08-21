# StockPayDay++

提醒投資人股利發放日期的工具。

## 功能

- **Crawler**：從臺灣證券交易所（TWSE）與證櫃（TPEx）抓取股利發放資料
- **Processor**：處理原始資料、產生靜態 JSON API、發送 LINE 通知
- **Frontend**：Vue 3 + Vite + Tailwind CSS 靜態站台

## 目錄結構

```
StockPayDay++/
├── crawler/          # 資料爬蟲
├── processor/        # 資料處理與通知
├── frontend/         # Vue 3 前端
├── data/             # 原始與處理後資料（git ignored）
├── api/              # 靜態 JSON API（git ignored）
└── docs/             # 專案文件
```

## 快速開始

### 後端

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 環境變數

複製 `.env.example` 為 `.env` 並填入：

```bash
LINE_NOTIFY_TOKEN=your_token_here
TWSE_REQUEST_DELAY=2
TWSE_MAX_RETRIES=3
```

## License

MIT
