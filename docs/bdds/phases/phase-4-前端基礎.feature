# language: zh-TW
@phase-4 @frontend
Feature: 前端基礎（行事曆 + 列表）
  作為一個投資人
  我想要快速查看台股未來配息日期
  以便掌握領息時程，不錯過任何配息機會

  Background:
    Given 網站已部署至 GitHub Pages
    And 資料已從 TWSE 抓取並處理完成

  # ==================== 首頁顯示 ====================

  @smoke
  Scenario: 開啟網站顯示行事曆模式
    Given 使用者開啟網站
    When 頁面載入完成
    Then 顯示行事曆模式
    And 預設顯示當前月份
    And 有配息的日期有視覺標示

  @smoke
  Scenario: 切換至列表模式
    Given 使用者在首頁
    When 使用者點擊「列表」Tab
    Then 即時切換為列表模式
    And 列表依日期排序（近的在前）
    And 每筆顯示：日期、代號、名稱、金額

  Scenario: 切換回行事曆模式
    Given 使用者在列表模式
    When 使用者點擊「行事曆」Tab
    Then 即時切換回行事曆模式

  # ==================== 行事曆互動 ====================

  @smoke
  Scenario: 點擊日期查看配息股票
    Given 使用者在行事曆模式
    And 該日有配息股票
    When 使用者點擊該日期
    Then 顯示該日配息股票列表
    And 列表包含股票代號、名稱、配息金額

  Scenario: 點擊無配息的日期
    Given 使用者在行事曆模式
    And 該日無配息股票
    When 使用者點擊該日期
    Then 顯示「該日無配息股票」提示

  # ==================== 資料載入 ====================

  Scenario: 資料載入中
    Given 使用者開啟網站
    When 資料正在載入
    Then 顯示全頁 Loading Spinner
    And 顯示「載入中...」文字

  Scenario: 資料載入成功
    Given 使用者開啟網站
    When 資料載入完成
    Then 顯示行事曆或列表模式
    And 不再顯示 Loading Spinner

  @edge-case
  Scenario: 資料載入失敗
    Given 使用者開啟網站
    When 資料載入失敗
    Then 顯示錯誤訊息「資料載入失敗，請稍後再試」
    And 顯示「重試」按鈕

  Scenario: 點擊重試按鈕
    Given 使用者看到載入失敗訊息
    When 使用者點擊「重試」按鈕
    Then 重新載入資料
    And 顯示 Loading Spinner

  # ==================== 空狀態 ====================

  @edge-case
  Scenario: 無未來配息資料
    Given 使用者開啟網站
    And 目前沒有即將配息的證券
    When 資料載入完成
    Then 顯示空狀態訊息「目前沒有即將配息的證券」

  # ==================== 證券類型 ====================

  Scenario: 顯示個股配息
    Given 使用者開啟網站
    When 資料載入完成
    Then 行事曆或列表包含個股配息資料

  Scenario: 顯示 ETF 配息
    Given 使用者開啟網站
    When 資料載入完成
    Then 行事曆或列表包含 ETF 配息資料

  Scenario: 顯示特別股配息
    Given 使用者開啟網站
    When 資料載入完成
    Then 行事曆或列表包含特別股配息資料

  # ==================== Edge Cases ====================

  @edge-case
  Scenario: 網路斷線時顯示錯誤
    Given 使用者開啟網站
    When 網路斷線無法載入資料
    Then 顯示錯誤訊息「資料載入失敗，請檢查網路後重試」
