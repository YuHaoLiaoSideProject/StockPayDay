# language: zh-TW
@phase-2 @crawler
Feature: 爬蟲 — MOPS 配息日
  作為一個投資人
  我想要系統自動抓取配息日資料
  以便知道何時會收到股利

  Background:
    Given 開發者已設定 Python 虛擬環境
    And 已安裝 requirements.txt 依賴
    And Phase 1 TWT48U 爬蟲已完成

  # ==================== 爬蟲執行 ====================

  @smoke
  Scenario: 執行 MOPS 爬蟲
    Given 開發者在專案根目錄
    When 執行 MOPS 爬蟲
    Then 從 MOPS 抓取配息日資料
    And 儲存至 data/mops/ 目錄

  @smoke
  Scenario: 爬蟲抓取至少 10 筆資料
    Given MOPS 爬蟲已執行
    When 檢查 data/mops/ 目錄
    Then 至少有 1 個季 JSON 檔案
    And 每個檔案包含至少 10 筆資料

  # ==================== 資料格式 ====================

  @smoke
  Scenario: 配息日資料格式正確
    Given MOPS 爬蟲已抓取資料
    When 檢查任一季 JSON 檔案
    Then 包含 code 欄位（證券代號）
    And 包含 ex_date 欄位（除息日）
    And 包含 pay_date 欄位（配息日）

  Scenario: 日期格式為西元年
    Given MOPS 爬蟲已抓取資料
    When 檢查 ex_date 和 pay_date 欄位
    Then 格式為 YYYY-MM-DD
    And 無民國年格式

  # ==================== 資料合併 ====================

  @smoke
  Scenario: 重複執行不會產生重複資料
    Given MOPS 爬蟲已執行過
    When 再次執行 MOPS 爬蟲
    Then 資料筆數不變（或僅新增）
    And 無重複的 (code, ex_date) 組合

  # ==================== 效能 ====================

  Scenario: 爬蟲執行時間
    Given MOPS 爬蟲已執行
    When 記錄執行時間
    Then 總執行時間 < 60 秒

  # ==================== 錯誤處理 ====================

  @edge-case
  Scenario: CSRF Token 取得失敗
    Given MOPS 頁面結構變動
    When 執行 MOPS 爬蟲
    Then 記錄錯誤訊息
    And 重試 3 次後放棄

  @edge-case
  Scenario: 網路連線失敗
    Given 網路連線中斷
    When 執行 MOPS 爬蟲
    Then 記錄錯誤訊息
    And 重試 3 次後放棄

  @edge-case
  Scenario: HTML 表格解析失敗
    Given MOPS 回傳的 HTML 表格結構異常
    When 執行 MOPS 爬蟲
    Then 記錄警告訊息
    And 嘗試多種選擇器解析

  @edge-case
  Scenario: 資料為空
    Given MOPS 回傳的資料為空
    When 執行 MOPS 爬蟲
    Then 記錄警告訊息
    And 不寫入檔案
