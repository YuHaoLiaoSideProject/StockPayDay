"""
TPEx 上櫃證券清單爬蟲
從證券櫃檯買賣中心（TPEx）抓取完整上櫃證券清單（含上櫃股票、ETF、特別股）

資料來源：https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php
方法: GET
參數: l=zh-tw, d=民國日期(115/08/21), se=AL(所有證券), s=i0
回傳: JSON 格式，含上櫃股票每日收盤行情（所有上櫃證券）

注意事項：
- 需要 X-Requested-With + Referer Header（TPEx 有 WAF 保護）
- 日期使用民國年（西元年 - 1911），如 115/08/21
- 代號為「7 開頭 6 位純數字」的是上櫃認購（售）權證，予以排除
- 資料為每日更新，取最新交易日資料
"""

import requests
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# TPEx 上櫃股票每日收盤行情 API
TPEX_QUOTES_URL = (
    "https://www.tpex.org.tw/web/stock/aftertrading/"
    "otc_quotes_no1430/stk_wn1430_result.php"
)

# 上櫃權證代號：7 開頭 6 位純數字（如 739986 廣明國票5B購01）
WARRANT_CODE_RE = re.compile(r"^7\d{5}$")


class TPExListingCrawler:
    """TPEx 上櫃證券清單爬蟲"""

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
            "Referer": "https://www.tpex.org.tw/web/stock/aftertrading/otc_BS/otc_BS.htm",
            "X-Requested-With": "XMLHttpRequest",
        })
        self.max_retries = max_retries
        self.delay = delay

    def fetch(self) -> List[Dict]:
        """
        抓取上櫃證券清單

        Returns:
            證券清單列表（code, name, market）
        """
        # 嘗試最近 7 天的資料（避免假日無資料）
        today = datetime.now()
        for days_back in range(7):
            date = today - timedelta(days=days_back)
            date_str = self._to_roc_date(date)
            records = self._fetch_date(date_str)
            if records:
                logger.info(
                    "TPEx 上櫃清單抓取成功（%s）：%d 筆", date_str, len(records),
                )
                return records

        logger.warning("TPEx 上櫃清單抓取失敗：最近 7 天均無資料")
        return []

    @staticmethod
    def _to_roc_date(date: datetime) -> str:
        """
        轉換為 TPEx 使用的民國日期格式

        Args:
            date: 西元日期

        Returns:
            民國日期字串（如 115/08/21）
        """
        return f"{date.year - 1911}/{date.month:02d}/{date.day:02d}"

    def _fetch_date(self, date_str: str) -> List[Dict]:
        """
        抓取指定日期的上櫃證券清單

        Args:
            date_str: 民國日期字串（115/08/21）

        Returns:
            證券清單列表
        """
        params = {
            "l": "zh-tw",
            "d": date_str,
            "se": "AL",  # 所有證券
            "s": "i0",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(TPEX_QUOTES_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                records = []
                for table in data.get("tables", []):
                    for row in table.get("data", []):
                        record = self._parse_row(row)
                        if record:
                            records.append(record)

                return records

            except Exception as e:
                if attempt < self.max_retries:
                    wait = self.delay * attempt
                    logger.warning(
                        "TPEx 清單請求失敗，%s 秒後重試 (%d/%d): %s",
                        wait, attempt, self.max_retries, e,
                    )
                    time.sleep(wait)
                else:
                    logger.error("TPEx 清單請求失敗，已達最大重試次數: %s", e)
                    raise

        return []

    def _parse_row(self, row: List) -> Optional[Dict]:
        """
        解析一筆資料

        Args:
            row: 原始資料陣列（代號、名稱、收盤…）

        Returns:
            解析後的資料字典，或 None（權證或格式異常時）
        """
        try:
            code = row[0].strip()
            name = row[1].strip()

            # 驗證代號格式（4-6 碼數字或字母）
            if not re.match(r"^[0-9A-Z]{4,6}$", code):
                return None

            # 排除上櫃認購（售）權證（7 開頭 6 位純數字）
            if WARRANT_CODE_RE.match(code):
                return None

            # 驗證名稱非空
            if not name:
                return None

            return {
                "code": code,
                "name": name,
                "market": "TPEx",
            }
        except (IndexError, ValueError) as e:
            logger.warning("解析 TPEx 清單資料失敗: %s", e)
            return None


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_tpex_listing() -> List[Dict]:
    """
    抓取 TPEx 上櫃證券清單（便捷包裝）

    Returns:
        證券清單列表
    """
    crawler = TPExListingCrawler()
    return crawler.fetch()