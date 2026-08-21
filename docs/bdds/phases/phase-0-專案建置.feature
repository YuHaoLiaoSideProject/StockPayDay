# language: zh-TW
@phase-0 @setup
Feature: 專案建置
  作為一個開發者
  我想要快速建立專案骨架
  以便開始開發功能

  # ==================== 目錄結構 ====================

  @smoke
  Scenario: 建立完整目錄結構
    Given 開發者在空目錄
    When 執行專案建置腳本
    Then 建立 crawler/ 目錄
    And 建立 processor/ 目錄
    And 建立 data/ 目錄（含 raw, stocks, etfs, preferred）
    And 建立 api/ 目錄
    And 建立 frontend/ 目錄
    And 建立 docs/ 目錄

  # ==================== Python 環境 ====================

  @smoke
  Scenario: Python 虛擬環境設定
    Given 開發者已安裝 Python 3.11+
    When 執行 pip install -r requirements.txt
    Then 安裝 requests 套件
    And 安裝 beautifulsoup4 套件
    And 安裝 python-dotenv 套件

  @edge-case
  Scenario: Python 版本過舊
    Given 開發者安裝 Python 3.10
    When 執行專案建置腳本
    Then 顯示錯誤訊息要求 Python 3.11+

  # ==================== 前端環境 ====================

  @smoke
  Scenario: Vue + Vite 初始化
    Given 開發者在 frontend/ 目錄
    When 執行 npm create vite@latest
    And 選擇 Vue + TypeScript
    Then 建立 Vue 專案骨架
    And 建立 package.json

  @smoke
  Scenario: Tailwind CSS 安裝
    Given frontend/ 專案已建立
    When 執行 npm install -D tailwindcss postcss autoprefixer
    And 執行 npx tailwindcss init -p
    Then 建立 tailwind.config.js
    And 建立 postcss.config.js

  @smoke
  Scenario: npm run dev 啟動
    Given frontend/ 專案已設定完成
    When 執行 npm run dev
    Then 開發伺服器啟動
    And 瀏覽器可看到 Vue 預設頁面

  # ==================== 版本控制 ====================

  @smoke
  Scenario: .gitignore 建立
    Given 開發者在根目錄
    When 建立 .gitignore
    Then 忽略 venv/ 目錄
    And 忽略 node_modules/ 目錄
    And 忽略 __pycache__/ 目錄
    And 忽略 .env 檔案

  @smoke
  Scenario: README.md 建立
    Given 開發者在根目錄
    When 建立 README.md
    Then 包含專案說明
    And 包含環境設定步驟
    And 包含使用方式
