"""
TWSE 個股配息爬蟲
從公開資訊觀測站（MOPS）抓取個股配息資料

資料來源：https://mops.twse.com.tw/mops/web/t05st09_ifrs

注意事項：
- 需要先 GET 取得 CSRF Token
- 使用 POST 發送請求
- 回應為 HTML，需解析表格
- 有 WAF 保護，需正確 Headers
"""

import logging
from typing import Dict, List, Tuple, Optional

from crawler.sources.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class TWSEStockCrawler(BaseCrawler):
    """TWSE 個股配息爬蟲"""

    # 個股：所有純數字 4 碼代號均通過（ETF、特別股由其他爬蟲篩選）
    def _is_target(self, code: str) -> bool:
        """個股代號判斷：4 位數字且非 ETF、非特別股範圍。"""
        if len(code) != 4 or not code.isdigit():
            return False
        code_num = int(code)
        # 排除 ETF（0001-0999）與特別股（>= 7000）
        return not (1 <= code_num <= 999) and code_num < 7000

    def fetch_dividend_list(self, year: int, quarter: int) -> List[Dict]:
        """
        抓取指定民國年、季度的配息公告。

        Args:
            year: 民國年（例如 114）
            quarter: 季度 1-4

        Returns:
            原始配息紀錄列表
        """
        return self._fetch_raw_records(year, quarter, label="個股")

    def fetch_stock_dividends(
        self, year: int, quarter: int,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        對外 API — 抓取指定年季的個股配息資料並轉換格式。

        Args:
            year: 民國年
            quarter: 季度 1-4

        Returns:
            (raw_data, processed_stocks)
        """
        raw_records = self.fetch_dividend_list(year, quarter)
        processed = self._group_raw_records(raw_records, year, quarter, record_type="stock")
        logger.info(
            "fetch_stock_dividends(%d, Q%d) — 共 %d 支股票",
            year, quarter, len(processed),
        )
        return raw_records, processed
