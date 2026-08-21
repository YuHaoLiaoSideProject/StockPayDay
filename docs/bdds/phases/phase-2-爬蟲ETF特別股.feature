# language: zh-TW
@phase-2 @crawler
Feature: 爬蟲 — ETF + 特別股
  作為一個投資人
  我想要系統自動抓取 ETF 和特別股配息資料
  以便獲得完整的配息資訊

  Background:
    Given 開發者已設定 Python 虛擬環境
    And 已安裝 requirements.txt 依賴
    And Phase 1 個股爬蟲已完成

  # ==================== ETF 爬蟲 ====================

  @smoke
  Scenario: 執行 ETF 爬蟲
    Given 開發者在專案根目錄
    When 執行 ETF 爬蟲模組
    Then 從 TWSE 抓取 ETF 資料
    And 儲存至 data/etfs/ 目錄

  @smoke
  Scenario: ETF 資料包含 0050、0056
    Given ETF 爬蟲已執行
    When 檢查 data/etfs/ 目錄
    Then 包含 0050.json（元大台灣50）
    And 包含 0056.json（元大高股息）

  Scenario: ETF 資料格式正確
    Given ETF 爬蟲已抓取資料
    When 檢查任一 ETF JSON 檔案
    Then 包含 code 欄位
    And 包含 name 欄位
    And 包含 dividend_history 欄位

  # ==================== 特別股爬蟲 ====================

  @smoke
  Scenario: 執行特別股爬蟲
    Given 開發者在專案根目錄
    When 執行特別股爬蟲模組
    Then 從 TWSE 抓取特別股資料
    And 儲存至 data/preferred/ 目錄

  Scenario: 特別股資料格式正確
    Given 特別股爬蟲已抓取資料
    When 檢查任一特別股 JSON 檔案
    Then 包含 code 欄位
    And 包含 name 欄位
    And 包含 dividend_history 欄位

  # ==================== 整合測試 ====================

  @smoke
  Scenario: 同時抓取所有證券類型
    Given 開發者在專案根目錄
    When 執行完整爬蟲腳本
    Then 產生 data/stocks/ 個股資料
    And 產生 data/etfs/ ETF 資料
    And 產生 data/preferred/ 特別股資料

  Scenario: 爬蟲總執行時間
    Given 開發者執行完整爬蟲
    When 記錄總執行時間
    Then 總執行時間 < 3 分鐘

  # ==================== 錯誤處理 ====================

  @edge-case
  Scenario: ETF 爬蟲失敗不影響個股
    Given 個股爬蟲已成功
    When ETF 爬蟲執行失敗
    Then 個股資料仍存在
    And 記錄 ETF 爬蟲錯誤

  @edge-case
  Scenario: 特別股爬蟲失敗不影響其他
    Given 個股和 ETF 爬蟲已成功
    When 特別股爬蟲執行失敗
    Then 個股和 ETF 資料仍存在
    And 記錄特別股爬蟲錯誤

  @edge-case
  Scenario: 網路連線失敗
    Given 網路連線中斷
    When 執行爬蟲腳本
    Then 記錄錯誤訊息
    And 不產生不完整的資料
