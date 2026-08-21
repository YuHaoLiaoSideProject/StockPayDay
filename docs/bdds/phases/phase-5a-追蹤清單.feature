# language: zh-TW
@phase-5a @frontend
Feature: 追蹤清單
  作為一個投資人
  我想要收藏感興趣的證券
  以便在專屬頁面掌握其配息時程

  Background:
    Given 網站已部署至 GitHub Pages
    And 資料已從 TWSE 抓取並處理完成

  # ==================== 加入/移除追蹤 ====================

  @smoke
  Scenario: 從股票詳情頁加入追蹤
    Given 使用者在股票詳情頁（/stock/:code）
    And 該股票未追蹤
    When 使用者點擊右上角 ❤️ 按鈕
    Then ❤️ 圖示變為實心紅色
    And 導覽列追蹤清單徽章數字 +1
    And 該股票加入追蹤清單（localStorage）

  @smoke
  Scenario: 從股票詳情頁移除追蹤
    Given 使用者在股票詳情頁（/stock/:code）
    And 該股票已追蹤
    When 使用者點擊右上角 ❤️ 按鈕
    Then ❤️ 圖示變為空心
    And 導覽列追蹤清單徽章數字 -1
    And 該股票從追蹤清單移除

  @smoke
  Scenario: 從列表模式加入追蹤
    Given 使用者在列表模式
    And 某支股票未追蹤
    When 使用者點擊該列表項目右側的小型 ❤️ 按鈕
    Then ❤️ 圖示變為實心紅色
    And 導覽列徽章數字 +1

  # ==================== 追蹤清單頁面 ====================

  @smoke
  Scenario: 查看追蹤清單
    Given 使用者有追蹤的股票
    When 使用者點擊導覽列「❤️ 追蹤清單」連結
    Then 導航至 /watchlist
    And 顯示追蹤清單頁面
    And 預設顯示行事曆模式

  @edge-case
  Scenario: 追蹤清單為空
    Given 使用者無追蹤的股票
    When 使用者點擊導覽列「❤️ 追蹤清單」連結
    Then 顯示空狀態引導畫面
    And 顯示搜尋欄
    And 顯示「查看行事曆」按鈕

  Scenario: 切換追蹤清單顯示模式
    Given 使用者在追蹤清單頁面
    And 追蹤清單有股票
    When 使用者點擊「📋 列表」按鈕
    Then 切換為列表模式
    When 使用者點擊「📅 行事曆」按鈕
    Then 切換回行事曆模式

  # ==================== 追蹤清單搜尋 ====================

  @smoke
  Scenario: 從追蹤清單頁搜尋加入追蹤
    Given 使用者在追蹤清單頁面（/watchlist）
    When 使用者在搜尋欄輸入股票代號或名稱
    Then 即時顯示搜尋結果下拉列表（最多 10 筆）
    When 使用者點擊搜尋結果的 ❤️ 按鈕
    Then 該股票加入追蹤清單
    And 追蹤清單立即更新顯示

  @edge-case
  Scenario: 搜尋無結果
    Given 使用者在追蹤清單頁面
    When 使用者在搜尋欄輸入不存在的代號
    Then 顯示「找不到符合的證券」提示

  # ==================== 追蹤標記 ====================

  Scenario: 行事曆顯示追蹤標記
    Given 使用者在追蹤清單頁面
    And 追蹤清單有股票
    When 行事曆載入完成
    Then 追蹤股票的配息日有紅色圓點標示

  Scenario: 列表顯示追蹤按鈕
    Given 使用者在追蹤清單頁面列表模式
    And 追蹤清單有股票
    When 列表載入完成
    Then 每筆列表項目顯示 ❤️ 按鈕

  # ==================== 持久化 ====================

  @smoke
  Scenario: 追蹤清單持久化
    Given 使用者已加入追蹤股票
    When 使用者關閉瀏覽器再開啟
    Then 追蹤清單仍存在
    And 導覽列徽章顯示正確數量

  # ==================== 導覽列整合 ====================

  Scenario: 導覽列追蹤徽章
    Given 使用者有追蹤的股票
    When 任何頁面載入
    Then 導覽列顯示追蹤清單連結
    And 連結顯示追蹤數量徽章

  Scenario: 導覽列徽章為空
    Given 使用者無追蹤的股票
    When 任何頁面載入
    Then 導覽列追蹤清單連結不顯示徽章
