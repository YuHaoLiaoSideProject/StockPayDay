"""
TWSE 上市證券清單爬蟲
從臺灣證券交易所抓取完整上市股票清單

資料來源：https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX
方法: GET
參數: response=json, date=YYYYMMDD, type=ALLBUT0999
回傳: JSON 格式，包含每日收盤行情（含所有上市股票）

注意事項：
- 需要完整的瀏覽器 Headers（TWSE 有 WAF 保護）
- 回傳的表格中，「每日收盤行情」包含所有上市股票代號與名稱
- 資料為每日更新，取最新交易日資料
"""

import requests
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# TWSE MI_INDEX URL
MI_INDEX_URL = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"


class TWSEListingCrawler:
    """TWSE 上市證券清單爬蟲"""

    def __init__(self, max_retries: int = 3, delay: float = 2.0):
        """
        初始化爬蟲

        Args:
            max_retries: 最大重試次數（必須 >= 1）
            delay: 重試間隔秒數（會遞增）

        Raises:
            ValueError: max_retries < 1
        """
        if max_retries < 1:
            raise ValueError(f"max_retries must be >= 1, got {max_retries}")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": "https://www.twse.com.tw/zh/trading/exRight/TWT48U.html",
        })
        self.max_retries = max_retries
        self.delay = delay

    def fetch(self) -> List[Dict]:
        """
        抓取上市證券清單

        Returns:
            證券清單列表（code, name, market）
        """
        # 嘗試最近 7 天的資料（避免假日無資料）
        today = datetime.now()
        for days_back in range(7):
            date = today - timedelta(days=days_back)
            date_str = date.strftime("%Y%m%d")
            records = self._fetch_date(date_str)
            if records:
                logger.info("TWSE 上市清單抓取成功（%s）：%d 筆", date_str, len(records))
                return records

        logger.warning("TWSE 上市清單抓取失敗：最近 7 天均無資料")
        return []

    def _fetch_date(self, date_str: str) -> List[Dict]:
        """
        抓取指定日期的上市證券清單

        Args:
            date_str: 日期字串（YYYYMMDD）

        Returns:
            證券清單列表
        """
        params = {
            "response": "json",
            "date": date_str,
            "type": "ALLBUT0999",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(MI_INDEX_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                records = []
                for table in data.get("tables", []):
                    title = table.get("title", "")
                    # 找到「每日收盤行情」表格
                    if "收盤行情" in title:
                        for row in table.get("data", []):
                            record = self._parse_row(row)
                            if record:
                                records.append(record)
                        break

                return records

            except Exception as e:
                if attempt < self.max_retries:
                    wait = self.delay * attempt
                    logger.warning(
                        "TWSE 清單請求失敗，%s 秒後重試 (%d/%d): %s",
                        wait, attempt, self.max_retries, e,
                    )
                    time.sleep(wait)
                else:
                    logger.error("TWSE 清單請求失敗，已達最大重試次數: %s", e)
                    raise

        return []

    def _parse_row(self, row: List) -> Optional[Dict]:
        """
        解析一筆資料

        Args:
            row: 原始資料陣列

        Returns:
            解析後的資料字典，或 None（格式異常時）
        """
        try:
            code = row[0].strip()
            name = row[1].strip()

            # 驗證代號格式（4-5 碼數字或字母）
            if not re.match(r"^[0-9A-Z]{4,6}$", code):
                return None

            # 驗證名稱非空
            if not name:
                return None

            return {
                "code": code,
                "name": name,
                "market": "TWSE",
            }
        except (IndexError, ValueError) as e:
            logger.warning("解析 TWSE 清單資料失敗: %s", e)
            return None


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_twse_listing() -> List[Dict]:
    """
    抓取 TWSE 上市證券清單（便捷包裝）

    Returns:
        證券清單列表
    """
    crawler = TWSEListingCrawler()
    return crawler.fetch()
