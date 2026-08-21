"""
TWSE TWT48U 爬蟲 — 除權除息預告表
從臺灣證券交易所抓取未來除權除息預告資料

資料來源：https://www.twse.com.tw/rwd/zh/exRight/TWT48U
方法: GET
參數: response=json
回傳: JSON 格式

注意事項：
- 需要完整的瀏覽器 Headers（TWSE 有 WAF 保護）
- 回傳民國年日期，需轉換為西元年
- 資料範圍為未來 1-2 個月
"""

import requests
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# TWSE TWT48U URL
TWT48U_URL = "https://www.twse.com.tw/rwd/zh/exRight/TWT48U"


class TWT48UCrawler:
    """TWSE TWT48U 爬蟲"""

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
        抓取未來除權除息預告資料

        Returns:
            配息資料列表
        """
        params = {"response": "json"}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(TWT48U_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                records = []
                for row in data.get("data", []):
                    record = self._parse_row(row)
                    if record:
                        records.append(record)

                logger.info("TWT48U 抓取成功：%d 筆", len(records))
                return records

            except Exception as e:
                if attempt < self.max_retries:
                    wait = self.delay * attempt
                    logger.warning(
                        "TWT48U 請求失敗，%s 秒後重試 (%d/%d): %s",
                        wait, attempt, self.max_retries, e,
                    )
                    time.sleep(wait)
                else:
                    logger.error("TWT48U 請求失敗，已達最大重試次數: %s", e)
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
            # 解析日期（民國年 → 西元年）
            ex_date = self._parse_date(row[0])

            # 解析配息金額
            cash_dividend = self._parse_number(row[7])

            # 解析股票股利
            stock_dividend = self._parse_number(row[4])

            return {
                "code": row[1],
                "name": row[2],
                "ex_date": ex_date,
                "type": row[3],  # 權/息/權息
                "cash_dividend": cash_dividend,
                "stock_dividend": stock_dividend,
            }
        except (IndexError, ValueError) as e:
            logger.warning("解析 TWT48U 資料失敗: %s", e)
            return None

    def _parse_date(self, date_str: str) -> str:
        """
        解析民國年日期字串為西元年

        格式：115年08月21日 → 2026-08-21

        Args:
            date_str: 民國年日期字串

        Returns:
            西元年日期字串 (YYYY-MM-DD)
        """
        if not date_str:
            return ""

        # 匹配民國年格式
        match = re.match(r"(\d{2,3})年(\d{1,2})月(\d{1,2})日", date_str)
        if match:
            roc_year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))

            # 民國年轉西元年
            ad_year = roc_year + 1911
            return f"{ad_year:04d}-{month:02d}-{day:02d}"

        return date_str

    @staticmethod
    def _parse_number(text: str) -> float:
        """
        解析數字字串

        Args:
            text: 數字字串（可能包含 HTML 標籤）

        Returns:
            浮點數
        """
        if not text:
            return 0.0

        # 移除 HTML 標籤
        text = re.sub(r"<[^>]+>", "", text)

        # 清理字串
        cleaned = text.strip().replace(",", "").replace("--", "0")
        cleaned = cleaned.replace("\u3000", "")  # 全形空格

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_twt48u() -> List[Dict]:
    """
    抓取 TWT48U 資料（便捷包裝）

    Returns:
        配息資料列表
    """
    crawler = TWT48UCrawler()
    return crawler.fetch()
