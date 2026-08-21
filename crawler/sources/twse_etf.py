"""
TWSE ETF 配息爬蟲
從公開資訊觀測站（MOPS）抓取 ETF 配息資料

資料來源：https://mops.twse.com.tw/mops/web/t05st09_ifrs

注意事項：
- 與個股/特別股共用相同 MOPS 端點
- 透過代號格式篩選 ETF（0001-0999 範圍的 4 位數字）
- 需要先 GET 取得 CSRF Token
- 使用 POST 發送請求
- 回應為 HTML，需解析表格
"""

import logging
from typing import Dict, List, Tuple, Optional

from crawler.sources.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class TWSEETFCrawler(BaseCrawler):
    """TWSE ETF 配息爬蟲"""

    @staticmethod
    def _is_etf(code: str) -> bool:
        """
        判斷是否為 ETF。

        ETF 代號特徵：
        - 4 位數字，範圍 0001-0999（如 0050、0056、00878）
        """
        if len(code) != 4 or not code.isdigit():
            return False
        code_num = int(code)
        return 1 <= code_num <= 999

    def _is_target(self, code: str) -> bool:
        return self._is_etf(code)

    def fetch_etf_dividends_for_quarter(self, year: int, quarter: int) -> List[Dict]:
        """
        抓取指定民國年、季度的 ETF 配息公告。

        Args:
            year: 民國年（例如 114）
            quarter: 季度 1-4

        Returns:
            ETF 配息紀錄列表
        """
        return self._fetch_raw_records(year, quarter, label="ETF")

    def fetch_etf_dividends(
        self, year: int, quarter: int,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        對外 API — 抓取指定年季的 ETF 配息資料並轉換格式。

        Args:
            year: 民國年
            quarter: 季度 1-4

        Returns:
            (raw_data, processed_etfs)
        """
        raw_records = self.fetch_etf_dividends_for_quarter(year, quarter)
        processed = self._group_raw_records(raw_records, year, quarter, record_type="etf")
        logger.info(
            "fetch_etf_dividends(%d, Q%d) — 共 %d 支 ETF",
            year, quarter, len(processed),
        )
        return raw_records, processed


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_etf_dividends(
    year: int, quarter: int,
) -> Tuple[List[Dict], List[Dict]]:
    """
    抓取所有 ETF 配息資料（便捷包裝）。

    Args:
        year: 民國年
        quarter: 季度 1-4

    Returns:
        (raw_data, processed_etfs)
    """
    crawler = TWSEETFCrawler()
    return crawler.fetch_etf_dividends(year, quarter)
