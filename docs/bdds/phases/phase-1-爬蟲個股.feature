# language: zh-TW
@phase-1 @crawler
Feature: 爬蟲 — 個股
  作為一個投資人
  我想要系統自動抓取個股配息資料
  以便獲得最新的配息資訊

  Background:
    Given 開發者已設定 Python 虛擬環境
    And 已安裝 requirements.txt 依賴

  # ==================== 爬蟲執行 ====================

  @smoke
  Scenario: 執行爬蟲腳本
    Given 開發者在專案根目錄
    When 執行 python crawler/fetch.py
    Then 從 TWSE 抓取個股資料
    And 儲存至 data/raw/ 目錄
    And 產生 data/stocks/ 基底資料

  @smoke
  Scenario: 爬蟲抓取至少 10 支個股
    Given 爬蟲腳本已執行
    When 檢查 data/stocks/ 目錄
    Then 至少有 10 個 JSON 檔案
    And 每個檔案代表一支個股

  # ==================== 資料格式 ====================

  @smoke
  Scenario: 個股資料格式正確
    Given 爬蟲已抓取個股資料
    When 檢查任一個股 JSON 檔案
    Then 包含 code 欄位（證券代號）
    And 包含 name 欄位（證券名稱）
    And 包含 dividend_history 欄位（配息歷史）
    And dividend_history 包含年份、除權息日、配息金額

  Scenario: 個股資料包含配息歷史
    Given 爬蟲已抓取個股資料
    When 檢查任一個股的 dividend_history
    Then 至少包含 1 筆歷史配息紀錄
    And 每筆紀錄包含 year、ex_date、dividend

  # ==================== 效能 ====================

  Scenario: 爬蟲執行時間
    Given 爬蟲腳本已執行
    When 記錄執行時間
    Then 總執行時間 < 2 分鐘

  # ==================== 錯誤處理 ====================

  @edge-case
  Scenario: 網路連線失敗
    Given 網路連線中斷
    When 執行爬蟲腳本
    Then 記錄錯誤訊息
    And 不產生不完整的資料

  @edge-case
  Scenario: TWSE 回應異常
    Given TWSE 回傳非 200 狀態碼
    When 執行爬蟲腳本
    Then 記錄錯誤訊息
    And 重試指定次數後放棄

  @edge-case
  Scenario: 資料格式異常
    Given TWSE 回傳的資料格式不符合預期
    When 執行爬蟲腳本
    Then 記錄警告訊息
    And 跳過該筆資料繼續處理
