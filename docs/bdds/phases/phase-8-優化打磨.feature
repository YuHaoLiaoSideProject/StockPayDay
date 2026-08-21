# language: zh-TW
@phase-8 @frontend
Feature: 優化打磨（RWD + 深色模式）
  作為一個投資人
  我想要在任何裝置上都能正常使用網站
  以便隨時隨地查看配息資訊

  Background:
    Given 網站已部署至 GitHub Pages
    And 資料已從 TWSE 抓取並處理完成

  # ==================== 響應式設計 ====================

  @smoke
  Scenario: 手機版顯示
    Given 使用者使用手機（視窗 < 768px）
    When 開啟網站
    Then 顯示適合手機的佈局
    And 所有功能可正常使用

  @smoke
  Scenario: 平板版顯示
    Given 使用者使用平板（視窗 768px - 1024px）
    When 開啟網站
    Then 顯示適合平板的佈局
    And 所有功能可正常使用

  @smoke
  Scenario: 桌機版顯示
    Given 使用者使用桌機（視窗 > 1024px）
    When 開啟網站
    Then 顯示適合桌機的佈局
    And 所有功能可正常使用

  # ==================== 深色模式 ====================

  @smoke
  Scenario: 偵測系統深色模式偏好
    Given 使用者的作業系統設定為深色模式
    When 開啟網站
    Then 自動套用深色模式主題

  @smoke
  Scenario: 偵測系統淺色模式偏好
    Given 使用者的作業系統設定為淺色模式
    When 開啟網站
    Then 自動套用淺色模式主題

  @smoke
  Scenario: 手動切換深色模式
    Given 使用者在淺色模式
    When 使用者點擊深色模式切換按鈕
    Then 即時切換為深色模式
    And 主題設定持久化（localStorage）

  @smoke
  Scenario: 手動切換淺色模式
    Given 使用者在深色模式
    When 使用者點擊淺色模式切換按鈕
    Then 即時切換為淺色模式

  # ==================== 響應式互動 ====================

  Scenario: 手機版行事曆顯示
    Given 使用者使用手機（視窗 < 768px）
    When 開啟網站
    Then 行事曆顯示為 3-5 欄佈局
    And 可正常點擊日期

  Scenario: 手機版列表顯示
    Given 使用者使用手機（視窗 < 768px）
    When 切換至列表模式
    Then 列表隱藏部分欄位
    And 僅顯示日期、代號、金額

  Scenario: 手機版搜尋欄
    Given 使用者使用手機（視窗 < 768px）
    When 使用者點擊搜尋欄
    Then 搜尋欄全寬顯示
    And 可正常輸入搜尋

  # ==================== 深色模式互動 ====================

  Scenario: 深色模式行事曆
    Given 使用者在深色模式
    When 查看行事曆
    Then 行事曆背景為深色
    And 文字為淺色
    And 配息標示清晰可見

  Scenario: 深色模式列表
    Given 使用者在深色模式
    When 查看列表
    Then 列表背景為深色
    And 文字為淺色
    And 分隔線清晰可見

  Scenario: 深色模式搜尋欄
    Given 使用者在深色模式
    When 使用搜尋欄
    Then 搜尋欄背景為深色
    And 輸入文字為淺色
    And 搜尋結果下拉為深色

  # ==================== 動畫 ====================

  Scenario: 主題切換無閃爍
    Given 使用者在淺色模式
    When 使用者點擊深色模式切換按鈕
    Then 即時切換無閃爍
    And 所有元素同時更新

  Scenario: 佈局切換無重載
    Given 使用者在手機版
    When 使用者旋轉裝置至直向
    Then 佈局即時調整
    And 不重新載入頁面

  # ==================== Edge Cases ====================

  @edge-case
  Scenario: localStorage 不可用
    Given 使用者的瀏覽器不支援 localStorage
    When 使用者切換深色模式
    Then 切換正常運作
    And 關閉後設定不保留

  @edge-case
  Scenario: prefers-reduced-motion 啟用
    Given 使用者的系統設定為減少動畫
    When 開啟網站
    Then 所有動畫停用
    And 切換效果改為瞬間完成
