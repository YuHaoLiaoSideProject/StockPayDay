# language: zh-TW
@phase-1 @crawler
Feature: 爬蟲 — TWT48U 除息預告
  作為一個投資人
  我想要系統自動抓取未來除權除息預告資料
  以便獲得即將除息的股票資訊

  Background:
    Given 開發者已設定 Python 虛擬環境
    And 已安裝 requirements.txt 依賴

  # ==================== 爬蟲執行 ====================

  @smoke
  Scenario: 執行 TWT48U 爬蟲
    Given 開發者在專案根目錄
    When 執行 TWT48U 爬蟲
    Then 從 TWSE 抓取除息預告資料
    And 儲存至 data/twses/ 目錄

  @smoke
  Scenario: 爬蟲抓取至少 10 支股票
    Given TWT48U 爬蟲已執行
    When 檢查 data/twses/ 目錄
    Then 至少有 1 個月分 JSON 檔案
    And 每個檔案包含至少 10 筆資料

  # ==================== 資料格式 ====================

  @smoke
  Scenario: 除息預告資料格式正確
    Given TWT48U 爬蟲已抓取資料
    When 檢查任一月分 JSON 檔案
    Then 包含 code 欄位（證券代號）
    And 包含 name 欄位（證券名稱）
    And 包含 ex_date 欄位（除息日）
    And 包含 type 欄位（權/息/權息）
    And 包含 cash_dividend 欄位（配息金額）

  Scenario: 除息日格式為西元年
    Given TWT48U 爬蟲已抓取資料
    When 檢查 ex_date 欄位
    Then 格式為 YYYY-MM-DD
    And 無民國年格式

  # ==================== 資料合併 ====================

  @smoke
  Scenario: 重複執行不會產生重複資料
    Given TWT48U 爬蟲已執行過
    When 再次執行 TWT48U 爬蟲
    Then 資料筆數不變（或僅新增）
    And 無重複的 (code, ex_date) 組合

  # ==================== 效能 ====================

  Scenario: 爬蟲執行時間
    Given TWT48U 爬蟲已執行
    When 記錄執行時間
    Then 總執行時間 < 30 秒

  # ==================== 錯誤處理 ====================

  @edge-case
  Scenario: 網路連線失敗
    Given 網路連線中斷
    When 執行 TWT48U 爬蟲
    Then 記錄錯誤訊息
    And 重試 3 次後放棄

  @edge-case
  Scenario: TWSE 限流（WAF 封鎖）
    Given TWSE 回傳封鎖訊息
    When 執行 TWT48U 爬蟲
    Then 記錄錯誤訊息
    And 重試 3 次後放棄

  @edge-case
  Scenario: 資料格式異常
    Given TWSE 回傳的資料格式不符合預期
    When 執行 TWT48U 爬蟲
    Then 記錄警告訊息
    And 跳過該筆資料繼續處理
