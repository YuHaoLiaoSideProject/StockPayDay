# language: zh-TW
@001 @frontend
Feature: 追蹤任意股票（含尚未公布配息的股票）
  作為一個投資人
  我想要直接從搜尋結果加入追蹤，也能追蹤尚未公布配息的股票
  以便快速建立個人追蹤清單，不漏掉任何感興趣的標的

  Background:
    Given 網站已部署至 GitHub Pages
    And 資料已從 TWSE 抓取並處理完成

  # ==================== 導覽列搜尋結果直接追蹤 ====================

  @smoke
  Scenario: 導覽列搜尋結果每列顯示 ❤️ 按鈕
    Given 使用者在首頁
    When 使用者在導覽列搜尋欄輸入股票代號或名稱
    Then 顯示搜尋結果下拉
    And 每列顯示股票代號與名稱
    And 每列右側顯示小型 ❤️ 按鈕

  @smoke
  Scenario: 未追蹤股票的 ❤️ 為空心
    Given 使用者在首頁
    And 該股票未追蹤
    When 使用者在導覽列搜尋欄輸入該股票代號
    Then 搜尋結果顯示該股票
    And 該股票的 ❤️ 按鈕為空心

  @smoke
  Scenario: 點擊搜尋結果 ❤️ 加入追蹤且下拉保持顯示
    Given 使用者在首頁
    And 導覽列搜尋結果已顯示某支未追蹤股票
    When 使用者點擊該股票右側的 ❤️ 按鈕
    Then ❤️ 變為實心紅色
    And 導覽列追蹤清單徽章數字 +1
    And 搜尋結果下拉保持顯示（不關閉）
    And 該股票加入追蹤清單（localStorage）

  @smoke
  Scenario: 再次點擊搜尋結果 ❤️ 移除追蹤
    Given 使用者在首頁
    And 導覽列搜尋結果已顯示某支已追蹤股票
    When 使用者再次點擊該股票右側的 ❤️ 按鈕
    Then ❤️ 變回空心
    And 導覽列追蹤清單徽章數字 -1
    And 搜尋結果下拉保持顯示（不關閉）
    And 該股票從追蹤清單移除

  Scenario: 點擊搜尋結果股票名稱導航至詳情頁
    Given 使用者在首頁
    And 導覽列搜尋結果已顯示
    When 使用者點擊某筆結果的股票名稱
    Then 導航至該股票詳情頁
    And 詳情頁的 ❤️ 追蹤狀態與搜尋結果一致

  @smoke
  Scenario: 重新整理頁面後追蹤狀態保持
    Given 使用者已從導覽列搜尋結果加入追蹤某股票
    When 使用者重新整理頁面
    Then 再次搜尋該股票時 ❤️ 顯示為實心紅色
    And 導覽列徽章數字保持正確

  # ==================== 追蹤清單頁搜尋加入 ====================

  Scenario: 追蹤清單頁頂部顯示搜尋欄
    Given 使用者在追蹤清單頁面（/watchlist）
    When 頁面載入完成
    Then 頁面頂部顯示搜尋欄

  @smoke
  Scenario Outline: 在追蹤清單頁以代號或名稱搜尋
    Given 使用者在追蹤清單頁面（/watchlist）
    When 使用者在搜尋欄輸入 <關鍵字>
    Then 即時顯示搜尋結果下拉（最多 10 筆）
    And 結果包含「2330 台積電」

    Examples:
      | 關鍵字 |
      | 2330   |
      | 台積   |

  @smoke
  Scenario: 追蹤清單頁搜尋結果含 ❤️ 按鈕
    Given 使用者在追蹤清單頁面（/watchlist）
    When 使用者在搜尋欄輸入股票代號
    Then 顯示搜尋結果下拉
    And 每筆結果右側含 ❤️ 按鈕

  @smoke
  Scenario: 從追蹤清單頁搜尋結果加入追蹤且清單立即更新
    # 交叉引用：phase-5a「從追蹤清單頁搜尋加入追蹤」已涵蓋基礎流程，
    # 本場景補強 ❤️ 狀態變化與追蹤清單即時更新
    Given 使用者在追蹤清單頁面（/watchlist）
    And 某支股票未追蹤
    When 使用者在搜尋欄輸入該股票代號
    And 點擊搜尋結果的 ❤️ 按鈕
    Then ❤️ 變為實心紅色
    And 導覽列徽章數字 +1
    And 追蹤清單立即更新顯示該股票

  @edge-case
  Scenario: 追蹤清單為空時搜尋欄仍可使用
    Given 使用者在追蹤清單頁面（/watchlist）
    And 追蹤清單為空（顯示空狀態引導）
    When 使用者在搜尋欄輸入股票代號
    Then 即時顯示搜尋結果下拉
    When 使用者點擊結果的 ❤️ 按鈕
    Then 該股票加入追蹤清單
    And 追蹤清單立即更新顯示（不再為空）

  @edge-case
  Scenario: 追蹤清單頁搜尋無結果
    # 與 phase-5a「搜尋無結果」重疊，本場景為本功能驗收項目 016
    Given 使用者在追蹤清單頁面（/watchlist）
    When 使用者在搜尋欄輸入不存在的代號
    Then 顯示「找不到符合的證券」提示

  # ==================== 追蹤尚未公布配息的股票 ====================

  @smoke
  Scenario: 追蹤未公布配息的股票顯示「無近期配息」
    Given 使用者在導覽列搜尋欄輸入某支不在 upcoming.json 中的股票代號
    When 使用者點擊該股票右側的 ❤️ 按鈕
    Then ❤️ 變為實心紅色
    And 該股票加入追蹤清單
    When 使用者前往追蹤清單頁面
    Then 追蹤清單顯示該股票
    And 該股票配息欄位顯示「無近期配息」

  @edge-case
  Scenario: 已下市股票仍顯示於追蹤清單
    Given 使用者已追蹤一支已下市的股票
    When 使用者前往追蹤清單頁面
    Then 追蹤清單仍顯示該股票
    And 該股票配息欄位顯示「無近期配息」

  Scenario: 股票公布配息後自動顯示配息資訊
    Given 使用者已追蹤一支未公布配息的股票
    And 追蹤清單顯示「無近期配息」
    When 該股票公布配息且下次資料更新（upcoming.json 更新後重新載入）
    Then 追蹤清單自動顯示該股票的配息資訊

  # ==================== 持久化 ====================

  @smoke
  Scenario: 關閉瀏覽器再開啟追蹤清單仍存在
    # 交叉引用：phase-5a「追蹤清單持久化」，本場景聚焦經由搜尋結果加入的股票
    Given 使用者已從導覽列搜尋結果加入追蹤股票
    When 使用者關閉瀏覽器再開啟網站
    Then 追蹤清單仍存在
    And 導覽列徽章顯示正確數量

  @smoke
  Scenario: 切換頁面時追蹤狀態保持一致
    Given 使用者已從導覽列搜尋結果加入追蹤某股票
    When 使用者切換至追蹤清單頁面
    Then 追蹤清單顯示該股票
    When 使用者切換至該股票詳情頁
    Then ❤️ 顯示為實心紅色
    And 導覽列徽章數字不變

  # ==================== 響應式 ====================

  Scenario: 手機版搜尋結果 ❤️ 可正常點擊
    Given 使用者使用手機（視窗 < 768px）
    And 導覽列搜尋結果下拉已顯示
    When 使用者點擊某股票的 ❤️ 按鈕
    Then ❤️ 變為實心紅色
    And 導覽列徽章數字 +1

  Scenario: 手機版追蹤清單頁搜尋欄可正常使用
    Given 使用者使用手機（視窗 < 768px）
    When 使用者在追蹤清單頁面搜尋欄輸入股票代號
    Then 即時顯示搜尋結果下拉
    And 可點擊結果 ❤️ 加入追蹤
    And 追蹤清單立即更新

  # ==================== 異常與邊界 ====================

  @edge-case
  Scenario: 搜尋欄為空不顯示下拉
    # 與 stockpayday.feature「搜尋欄為空時」重疊，本場景聚焦導覽列下拉
    Given 使用者在首頁
    When 導覽列搜尋欄為空
    Then 不顯示搜尋結果下拉

  @edge-case
  Scenario: localStorage 不可用時追蹤操作正常但資料不持久
    Given 使用者瀏覽器禁用 localStorage（如隱私模式）
    When 使用者從導覽列搜尋結果點擊 ❤️ 加入追蹤
    Then 追蹤操作正常執行（❤️ 變實心、徽章 +1）
    But 關閉瀏覽器後追蹤資料不保存

  @edge-case
  Scenario: 點擊外部或按 Escape 關閉搜尋結果下拉
    Given 導覽列搜尋結果下拉已顯示
    When 使用者點擊下拉外部或按下 Escape 鍵
    Then 搜尋結果下拉關閉
    And 已加入的追蹤狀態保持

  @edge-case
  Scenario: 搜尋結果最多顯示 10 筆
    Given 使用者在導覽列搜尋欄輸入符合超過 10 支股票的關鍵字
    When 搜尋結果下拉顯示
    Then 下拉最多顯示 10 筆結果
    And 每筆結果仍含 ❤️ 按鈕

  @edge-case
  Scenario: 追蹤數量無硬性上限
    Given 使用者已追蹤 100 支股票
    When 使用者再從搜尋結果追蹤第 101 支股票
    Then 追蹤操作正常執行
    And 不顯示數量限制提示

  @edge-case
  Scenario: 多裝置追蹤清單各自獨立
    Given 使用者在裝置 A 追蹤某股票
    When 使用者在裝置 B 開啟網站
    Then 裝置 B 的追蹤清單不包含該股票
    And 兩裝置的追蹤狀態互不影響