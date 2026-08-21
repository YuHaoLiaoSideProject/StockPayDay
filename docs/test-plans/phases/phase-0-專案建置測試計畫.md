# 測試計畫：Phase 0 專案建置

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 0 — 專案建置 |
| **測試類型** | 環境驗證、冒煙測試 |
| **工具** | Shell script、手動驗證 |

---

## 1. 測試項目

### 1.1 Python 環境

| 測試項目 | 預期結果 | 驗證方式 |
|----------|----------|----------|
| Python 版本 | 3.11+ | `python --version` |
| pip 可用 | 正常執行 | `pip --version` |
| 虛擬環境建立 | 成功建立 venv | `python -m venv venv` |
| 虛擬環境啟動 | 可 activate | `source venv/bin/activate` |
| requirements.txt 安裝 | 無錯誤 | `pip install -r requirements.txt` |

### 1.2 Node.js 環境

| 測試項目 | 預期結果 | 驗證方式 |
|----------|----------|----------|
| Node.js 版本 | 18+ | `node --version` |
| npm 可用 | 正常執行 | `npm --version` |
| npm install | 無錯誤 | `cd frontend && npm install` |
| npm run dev | 可啟動 | `npm run dev` |
| Vite 開發伺服器 | 正常運作 | 瀏覽器開啟顯示頁面 |

### 1.3 目錄結構

| 測試項目 | 預期結果 | 驗證方式 |
|----------|----------|----------|
| crawler/ 存在 | 目錄存在 | `ls -la crawler/` |
| processor/ 存在 | 目錄存在 | `ls -la processor/` |
| data/ 存在 | 目錄存在 | `ls -la data/` |
| api/ 存在 | 目錄存在 | `ls -la api/` |
| frontend/ 存在 | 目錄存在 | `ls -la frontend/` |
| .gitignore 存在 | 檔案存在 | `cat .gitignore` |
| README.md 存在 | 檔案存在 | `cat README.md` |

---

## 2. 自動化驗證腳本

### tests/phase0_verify.sh

```bash
#!/bin/bash
# Phase 0 驗證腳本

echo "🔍 驗證 Phase 0 專案建置..."

# 檢查 Python
echo ""
echo "📋 Python 環境："
python_version=$(python --version 2>&1)
echo "  $python_version"

# 檢查 Node.js
echo ""
echo "📋 Node.js 環境："
node_version=$(node --version 2>&1)
echo "  $node_version"

# 檢查目錄結構
echo ""
echo "📋 目錄結構："
dirs=("crawler" "processor" "data" "api" "frontend" "docs")
for dir in "${dirs[@]}"; do
  if [ -d "$dir" ]; then
    echo "  ✅ $dir/"
  else
    echo "  ❌ $dir/ 不存在"
  fi
done

# 檢查檔案
echo ""
echo "📋 關鍵檔案："
files=("requirements.txt" ".gitignore" "README.md")
for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✅ $file"
  else
    echo "  ❌ $file 不存在"
  fi
done

# 測試 pip install
echo ""
echo "📋 測試 pip install..."
if pip install -r requirements.txt -q 2>/dev/null; then
  echo "  ✅ pip install 成功"
else
  echo "  ❌ pip install 失敗"
fi

# 測試 npm install
echo ""
echo "📋 測試 npm install..."
cd frontend
if npm install -q 2>/dev/null; then
  echo "  ✅ npm install 成功"
else
  echo "  ❌ npm install 失敗"
fi
cd ..

echo ""
echo "✅ Phase 0 驗證完成"
```

---

## 3. 驗收標準

| 標準 | 目標 |
|------|------|
| Python 環境 | 3.11+ 可用 |
| Node.js 環境 | 18+ 可用 |
| pip install | 無錯誤完成 |
| npm install | 無錯誤完成 |
| npm run dev | 可正常啟動 |
| 目錄結構 | 符合 Tech Decision |
| .gitignore | 正確設定 |
| README.md | 已建立 |
