# language: zh-TW
@phase-5 @frontend
Feature: 前端進階（單股歷史 + 搜尋）
  作為一個投資人
  我想要查看單一證券歷史配息紀錄
  以便深入了解個股配息表現

  Background:
    Given 網站已部署至 GitHub Pages
    And 資料已從 TWSE 抓取並處理完成

  # ==================== 單股歷史 ====================

  @smoke
  Scenario: 從行事曆查看單股歷史
    Given 使用者在行事曆模式
    And 使用者已點擊某日期
    And 顯示該日配息股票列表
    When 使用者點擊某支股票
    Then 導航至單股歷史頁面
    And 顯示股票代號與名稱
    And 歷史配息表格顯示：年份、除權息日、配息金額

  @smoke
  Scenario: 從列表查看單股歷史
    Given 使用者在列表模式
    When 使用者點擊某支股票
    Then 導航至單股歷史頁面
    And 顯示股票代號與名稱
    And 歷史配息表格顯示：年份、除權息日、配息金額

  Scenario: 返回首頁
    Given 使用者在單股歷史頁面
    When 使用者點擊「← 返回」按鈕
    Then 導航回首頁
    And 回到之前的顯示模式（行事曆或列表）

  # ==================== 搜尋功能 ====================

  @smoke
  Scenario: 搜尋股票代號
    Given 使用者在首頁
    When 使用者在搜尋欄輸入「2330」
    Then 即時顯示符合的搜尋結果
    And 結果包含「2330 台積電」

  @smoke
  Scenario: 搜尋股票名稱
    Given 使用者在首頁
    When 使用者在搜尋欄輸入「台積」
    Then 即時顯示符合的搜尋結果
    And 結果包含「2330 台積電」

  Scenario: 點擊搜尋結果
    Given 使用者在首頁
    And 搜尋結果已顯示
    When 使用者點擊某筆搜尋結果
    Then 導航至該股票歷史頁面

  @edge-case
  Scenario: 搜尋無結果
    Given 使用者在首頁
    When 使用者在搜尋欄輸入「XXXXX」
    Then 顯示「找不到符合的證券」提示

  # ==================== Edge Cases ====================

  @edge-case
  Scenario: 單股資料不存在
    Given 使用者點擊某支股票
    When 該股票資料不存在
    Then 顯示錯誤訊息「找不到該證券資料」
    And 顯示返回按鈕

  @edge-case
  Scenario: 搜尋欄為空時
    Given 使用者在首頁
    When 搜尋欄為空
    Then 不顯示搜尋結果下拉

  @edge-case
  Scenario: 歷史資料為空
    Given 使用者在單股歷史頁面
    When 該股票無歷史配息資料
    Then 顯示「暫無歷史配息資料」提示
