# language: zh-TW
@phase-6 @backend
Feature: 通知功能（LINE Notify）
  作為一個投資人
  我想要在配息日前收到提醒通知
  以便不會錯過任何配息機會

  Background:
    Given 資料已從 TWSE 抓取並處理完成
    And api/upcoming.json 已產出

  # ==================== LINE 通知 ====================

  @smoke
  Scenario: 接收配息提醒通知
    Given 使用者已設定 LINE Notify Token
    And 有證券即將在 3 天內除權息
    When 系統執行通知腳本
    Then 推播 LINE 訊息
    And 訊息包含：代號、名稱、除權息日、配息金額

  @edge-case
  Scenario: 無符合條件的配息
    Given 使用者已設定 LINE Notify Token
    And 沒有證券在 3 天內除權息
    When 系統執行通知腳本
    Then 不推播任何訊息

  @edge-case
  Scenario: LINE Notify Token 未設定
    Given 使用者未設定 LINE Notify Token
    When 系統執行通知腳本
    Then 記錄錯誤訊息
    And 不推播任何訊息

  @edge-case
  Scenario: LINE Notify Token 無效
    Given 使用者已設定無效的 LINE Notify Token
    And 有證券即將在 3 天內除權息
    When 系統執行通知腳本
    Then 記錄推播失敗錯誤
    And 不中斷後續流程

  # ==================== 訊息格式 ====================

  Scenario: 通知訊息格式正確
    Given 有證券即將在 3 天內除權息
    When 系統產生通知訊息
    Then 訊息包含「📢 配息提醒」標題
    And 每筆證券包含：代號、名稱、除權息日、配息金額
    And 訊息格式清晰易讀

  # ==================== Edge Cases ====================

  @edge-case
  Scenario: upcoming.json 不存在
    Given api/upcoming.json 不存在
    When 系統執行通知腳本
    Then 記錄警告訊息
    And 正常結束不推播

  @edge-case
  Scenario: upcoming.json 格式錯誤
    Given api/upcoming.json 格式錯誤
    When 系統執行通知腳本
    Then 記錄錯誤訊息
    And 回傳空列表不推播

  @edge-case
  Scenario: LINE Notify API 超時
    Given 使用者已設定 LINE Notify Token
    And 有證券即將在 3 天內除權息
    When 系統執行通知腳本
    And LINE Notify API 請求逾時
    Then 記錄超時錯誤
    And 不中斷後續流程
