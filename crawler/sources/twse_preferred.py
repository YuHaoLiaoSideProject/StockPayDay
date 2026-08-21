"""
TWSE 特別股配息爬蟲
從公開資訊觀測站（MOPS）抓取特別股配息資料

資料來源：https://mops.twse.com.tw/mops/web/t05st09_ifrs

注意事項：
- 與個股/ETF 共用相同 MOPS 端點
- 透過代號格式篩選特別股（>= 7000 或帶字母後綴如 2330A）
- 需要先 GET 取得 CSRF Token
- 使用 POST 發送請求
- 回應為 HTML，需解析表格
"""

import logging
from typing import Dict, List, Tuple, Optional

from crawler.sources.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class TWSEPreferredCrawler(BaseCrawler):
    """TWSE 特別股配息爬蟲"""

    @staticmethod
    def _is_preferred_stock(code: str) -> bool:
        """
        判斷是否為特別股。

        特別股代號特徵：
        - 4 位數字且 >= 7000（如 7654）
        - 或帶字母後綴（如 2330A、2330B）
        """
        # 帶字母後綴（如 2330A）：5 碼，前 4 碼數字 + 第 5 碼字母
        if len(code) == 5 and code[:4].isdigit() and code[4].isalpha():
            return True

        # 4 位數字且 >= 7000（特別股常見範圍）
        if len(code) == 4 and code.isdigit():
            code_num = int(code)
            if code_num >= 7000:
                return True

        return False

    def _is_target(self, code: str) -> bool:
        return self._is_preferred_stock(code)

    def fetch_preferred_dividends_for_quarter(
        self, year: int, quarter: int,
    ) -> List[Dict]:
        """
        抓取指定民國年、季度的特別股配息公告。

        Args:
            year: 民國年（例如 114）
            quarter: 季度 1-4

        Returns:
            特別股配息紀錄列表
        """
        return self._fetch_raw_records(year, quarter, label="特別股")

    def fetch_preferred_dividends(
        self, year: int, quarter: int,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        對外 API — 抓取指定年季的特別股配息資料並轉換格式。

        Args:
            year: 民國年
            quarter: 季度 1-4

        Returns:
            (raw_data, processed_preferred)
        """
        raw_records = self.fetch_preferred_dividends_for_quarter(year, quarter)
        processed = self._group_raw_records(raw_records, year, quarter, record_type="preferred")
        logger.info(
            "fetch_preferred_dividends(%d, Q%d) — 共 %d 支特別股",
            year, quarter, len(processed),
        )
        return raw_records, processed


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_preferred_dividends(
    year: int, quarter: int,
) -> Tuple[List[Dict], List[Dict]]:
    """
    抓取所有特別股配息資料（便捷包裝）。

    Args:
        year: 民國年
        quarter: 季度 1-4

    Returns:
        (raw_data, processed_preferred)
    """
    crawler = TWSEPreferredCrawler()
    return crawler.fetch_preferred_dividends(year, quarter)
