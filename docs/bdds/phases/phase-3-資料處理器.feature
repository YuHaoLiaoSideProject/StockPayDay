# language: zh-TW
@phase-3 @processor
Feature: 資料處理器
  作為一個開發者
  我想要將爬蟲資料轉換為前端可用的格式
  以便前端能正確顯示配息資訊

  Background:
    Given 爬蟲已產出 data/ 目錄資料
    And data/stocks/、data/etfs/、data/preferred/ 目錄存在

  # ==================== 處理器執行 ====================

  @smoke
  Scenario: 執行處理器腳本
    Given 開發者在專案根目錄
    When 執行 python processor/generate_api.py
    Then 讀取 data/ 目錄所有資料
    And 產出 api/ 目錄檔案

  @smoke
  Scenario: 處理器執行時間
    Given 處理器腳本已執行
    When 記錄執行時間
    Then 執行時間 < 30 秒

  # ==================== upcoming.json ====================

  @smoke
  Scenario: 產出 upcoming.json
    Given 處理器腳本已執行
    When 檢查 api/upcoming.json
    Then 檔案存在
    And 格式為 JSON 陣列

  @smoke
  Scenario: upcoming.json 只包含未來配息
    Given 處理器腳本已執行
    When 檢查 api/upcoming.json 每筆資料
    Then ex_date >= 今天
    And 不包含已過期的配息

  Scenario: upcoming.json 資料格式正確
    Given 處理器腳本已執行
    When 檢查 api/upcoming.json 每筆資料
    Then 包含 code 欄位
    And 包含 name 欄位
    And 包含 type 欄位（stock/etf/preferred）
    And 包含 ex_date 欄位（YYYY-MM-DD）
    And 包含 pay_date 欄位（YYYY-MM-DD）
    And 包含 dividend 欄位（數字）

  # ==================== securities-index.json ====================

  @smoke
  Scenario: 產出 securities-index.json
    Given 處理器腳本已執行
    When 檢查 api/securities-index.json
    Then 檔案存在
    And 格式為 JSON 陣列

  Scenario: securities-index.json 包含所有證券
    Given 處理器腳本已執行
    When 檢查 api/securities-index.json
    Then 包含所有證券代號
    And 每筆包含 code 和 name

  # ==================== securities/{code}.json ====================

  @smoke
  Scenario: 產出單股歷史檔案
    Given 處理器腳本已執行
    When 檢查 api/securities/ 目錄
    Then 每支證券有一個 JSON 檔案
    And 檔名為 {code}.json

  Scenario: 單股歷史檔案格式正確
    Given 處理器腳本已執行
    When 檢查任一 api/securities/{code}.json
    Then 包含 code 欄位
    And 包含 name 欄位
    And 包含 history 欄位（陣列）
    And history 每筆包含 year、ex_date、dividend

  # ==================== 資料驗證 ====================

  @smoke
  Scenario: 資料格式驗證通過
    Given 處理器腳本已執行
    When 執行資料驗證腳本
    Then 所有檔案格式正確
    And 無缺漏欄位

  @edge-case
  Scenario: 資料格式驗證失敗
    Given 爬蟲產出的資料格式異常
    When 執行處理器腳本
    Then 記錄驗證錯誤
    And 跳過異常資料繼續處理

  # ==================== 錯誤處理 ====================

  @edge-case
  Scenario: data/ 目錄不存在
    Given data/ 目錄不存在
    When 執行處理器腳本
    Then 記錄錯誤訊息
    And 不產出 api/ 檔案

  @edge-case
  Scenario: 資料為空
    Given data/ 目錄存在但無資料
    When 執行處理器腳本
    Then 產出空的 upcoming.json（[]）
    And 產出空的 securities-index.json（[]）

  @edge-case
  Scenario: 部分資料缺失
    Given data/stocks/ 有資料但 data/etfs/ 為空
    When 執行處理器腳本
    Then 產出的 upcoming.json 只包含個股
    And 記錄警告訊息
