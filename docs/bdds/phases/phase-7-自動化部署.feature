# language: zh-TW
@phase-7 @devops
Feature: 自動化部署（GitHub Actions）
  作為一個開發者
  我想要系統自動每日抓取資料並部署
  以便使用者 always 看到最新的配息資訊

  Background:
    Given GitHub repo 已設定 GitHub Actions

  # ==================== 自動執行 ====================

  @smoke
  Scenario: GitHub Actions 每日自動執行
    Given GitHub Actions cron 排程設定為每日 UTC 08:00
    When 到達排程時間
    Then 自動執行爬蟲
    And 自動執行處理器
    And 自動執行通知
    And 自動部署至 GitHub Pages

  @smoke
  Scenario: GitHub Actions 手動觸發
    Given 開發者在 GitHub repo
    When 開發者點擊 "Run workflow"
    Then 手動觸發 GitHub Actions
    And 執行完整流程

  # ==================== 流程步驟 ====================

  Scenario: 爬蟲執行成功
    Given GitHub Actions 已觸發
    When 爬蟲腳本執行
    Then 從 TWSE 抓取資料
    And 儲存至 data/ 目錄
    And 回傳成功狀態

  Scenario: 處理器執行成功
    Given 爬蟲執行成功
    When 處理器腳本執行
    And 讀取 data/ 目錄資料
    Then 產出 api/upcoming.json
    And 產出 api/securities-index.json
    And 產出 api/securities/ 目錄

  Scenario: 通知執行成功
    Given 處理器執行成功
    And 有證券即將在 3 天內除權息
    When 通知腳本執行
    Then 推播 LINE 訊息

  Scenario: 部署成功
    Given 所有腳本執行成功
    When GitHub Actions 部署
    Then api/ 目錄部署至 GitHub Pages
    And 網站可正常訪問

  # ==================== 失敗處理 ====================

  @edge-case
  Scenario: 爬蟲執行失敗
    Given GitHub Actions 已觸發
    When 爬蟲腳本執行失敗
    Then 記錄錯誤訊息
    And 不執行後續步驟
    And GitHub 顯示失敗狀態

  @edge-case
  Scenario: 處理器執行失敗
    Given 爬蟲執行成功
    When 處理器腳本執行失敗
    Then 記錄錯誤訊息
    And 不執行後續步驟
    And GitHub 顯示失敗狀態

  @edge-case
  Scenario: 通知執行失敗
    Given 處理器執行成功
    When 通知腳本執行失敗
    Then 記錄錯誤訊息
    And 不中斷部署流程
    And 繼續執行部署

  @edge-case
  Scenario: 部署失敗
    Given 所有腳本執行成功
    When GitHub Actions 部署失敗
    Then 記錄錯誤訊息
    And GitHub 顯示失敗狀態
    And 網站保持舊版本
