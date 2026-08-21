# language: zh-TW
Feature: 股市配息行事曆
  作為一個投資人
  我想要快速查看台股未來配息日期
  以便掌握領息時程，不錯過任何配息機會

  Background:
    Given 網站已部署至 GitHub Pages
    And 資料已從 TWSE 抓取並處理完成

  # ==================== 首頁顯示 ====================

  Scenario: 開啟網站顯示行事曆模式
    Given 使用者開啟網站
    When 頁面載入完成
    Then 顯示行事曆模式
    And 預設顯示當前月份
    And 有配息的日期有視覺標示

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

  # ==================== 單股歷史 ====================

  Scenario: 從行事曆查看單股歷史
    Given 使用者在行事曆模式
    And 使用者已點擊某日期
    And 顯示該日配息股票列表
    When 使用者點擊某支股票
    Then 導航至單股歷史頁面
    And 顯示股票代號與名稱
    And 歷史配息表格顯示：年份、除權息日、配息金額

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

  Scenario: 搜尋股票代號
    Given 使用者在首頁
    When 使用者在搜尋欄輸入「2330」
    Then 即時顯示符合的搜尋結果
    And 結果包含「2330 台積電」

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

  Scenario: 搜尋無結果
    Given 使用者在首頁
    When 使用者在搜尋欄輸入「XXXXX」
    Then 顯示「找不到符合的證券」提示

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

  # ==================== 響應式設計 ====================

  Scenario: 手機版顯示
    Given 使用者使用手機（視窗 < 768px）
    When 開啟網站
    Then 顯示適合手機的佈局
    And 所有功能可正常使用

  Scenario: 平板版顯示
    Given 使用者使用平板（視窗 768px - 1024px）
    When 開啟網站
    Then 顯示適合平板的佈局
    And 所有功能可正常使用

  Scenario: 桌機版顯示
    Given 使用者使用桌機（視窗 > 1024px）
    When 開啟網站
    Then 顯示適合桌機的佈局
    And 所有功能可正常使用

  # ==================== 深色模式 ====================

  Scenario: 偵測系統深色模式偏好
    Given 使用者的作業系統設定為深色模式
    When 開啟網站
    Then 自動套用深色模式主題

  Scenario: 偵測系統淺色模式偏好
    Given 使用者的作業系統設定為淺色模式
    When 開啟網站
    Then 自動套用淺色模式主題

  Scenario: 手動切換深色模式
    Given 使用者在淺色模式
    When 使用者點擊深色模式切換按鈕
    Then 即時切換為深色模式
    And 主題設定持久化（localStorage）

  Scenario: 手動切換淺色模式
    Given 使用者在深色模式
    When 使用者點擊淺色模式切換按鈕
    Then 即時切換為淺色模式

  # ==================== LINE 通知 ====================

  Scenario: 接收配息提醒通知
    Given 使用者已設定 LINE Notify Token
    And 有證券即將在 3 天內除權息
    When 系統執行通知腳本
    Then 推播 LINE 訊息
    And 訊息包含：代號、名稱、除權息日、配息金額

  Scenario: 無符合條件的配息
    Given 使用者已設定 LINE Notify Token
    And 沒有證券在 3 天內除權息
    When 系統執行通知腳本
    Then 不推播任何訊息

  # ==================== 自動化部署 ====================

  Scenario: GitHub Actions 每日自動執行
    Given GitHub Actions cron 排程設定為每日 UTC 08:00
    When 到達排程時間
    Then 自動執行爬蟲
    And 自動執行處理器
    And 自動執行通知
    And 自動部署至 GitHub Pages

  Scenario: GitHub Actions 手動觸發
    Given 開發者在 GitHub repo
    When 開發者點擊 "Run workflow"
    Then 手動觸發 GitHub Actions
    And 執行完整流程

  # ==================== 追蹤清單 ====================

  Scenario: 從股票詳情頁加入追蹤
    Given 使用者在股票詳情頁（/stock/:code）
    And 該股票未追蹤
    When 使用者點擊右上角 ❤️ 按鈕
    Then ❤️ 圖示變為實心紅色
    And 導覽列追蹤清單徽章數字 +1
    And 該股票加入追蹤清單（localStorage）

  Scenario: 從股票詳情頁移除追蹤
    Given 使用者在股票詳情頁（/stock/:code）
    And 該股票已追蹤
    When 使用者點擊右上角 ❤️ 按鈕
    Then ❤️ 圖示變為空心
    And 導覽列追蹤清單徽章數字 -1
    And 該股票從追蹤清單移除

  Scenario: 從列表模式加入追蹤
    Given 使用者在列表模式
    And 某支股票未追蹤
    When 使用者點擊該列表項目右側的小型 ❤️ 按鈕
    Then ❤️ 圖示變為實心紅色
    And 導覽列徽章數字 +1

  Scenario: 從追蹤清單頁搜尋加入追蹤
    Given 使用者在追蹤清單頁面（/watchlist）
    When 使用者在搜尋欄輸入股票代號或名稱
    Then 即時顯示搜尋結果下拉列表（最多 10 筆）
    When 使用者點擊搜尋結果的 ❤️ 按鈕
    Then 該股票加入追蹤清單
    And 追蹤清單立即更新顯示

  Scenario: 查看追蹤清單
    Given 使用者有追蹤的股票
    When 使用者點擊導覽列「❤️ 追蹤清單」連結
    Then 導航至 /watchlist
    And 顯示追蹤清單頁面
    And 預設顯示行事曆模式

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

  Scenario: 追蹤清單持久化
    Given 使用者已加入追蹤股票
    When 使用者關閉瀏覽器再開啟
    Then 追蹤清單仍存在
    And 導覽列徽章顯示正確數量

  Scenario: 搜尋無結果
    Given 使用者在追蹤清單頁面
    When 使用者在搜尋欄輸入不存在的代號
    Then 顯示「找不到符合的證券」提示

  Scenario: 導覽列追蹤徽章
    Given 使用者有追蹤的股票
    When 任何頁面載入
    Then 導覽列顯示追蹤清單連結
    And 連結顯示追蹤數量徽章

  Scenario: 導覽列徽章為空
    Given 使用者無追蹤的股票
    When 任何頁面載入
    Then 導覽列追蹤清單連結不顯示徽章

  # ==================== Edge Cases ====================

  Scenario: 網路斷線時顯示錯誤
    Given 使用者開啟網站
    When 網路斷線無法載入資料
    Then 顯示錯誤訊息「資料載入失敗，請檢查網路後重試」

  Scenario: 單股資料不存在
    Given 使用者點擊某支股票
    When 該股票資料不存在
    Then 顯示錯誤訊息「找不到該證券資料」
    And 顯示返回按鈕

  Scenario: 搜尋欄為空時
    Given 使用者在首頁
    When 搜尋欄為空
    Then 不顯示搜尋結果下拉

  Scenario: 歷史資料為空
    Given 使用者在單股歷史頁面
    When 該股票無歷史配息資料
    Then 顯示「暫無歷史配息資料」提示
