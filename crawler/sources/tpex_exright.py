"""
TPEx 上櫃除權除息預告爬蟲
從證券櫃檯買賣中心（TPEx）OpenAPI 抓取上櫃除權除息預告資料

資料來源：https://www.tpex.org.tw/openapi/v1/tpex_exright_daily
方法: GET
回傳: JSON 陣列

Schema 欄位：
- Date: 除權息日期（民國年格式 1150824）
- SecuritiesCompanyCode: 股票代號
- CompanyName: 名稱
- ExRightsDiviend: 除權息（除息/除權/除權息）
- CashDividend: 現金股利
- StockDividend: 權值
- StockDividendPlusCashDividend: 權值加息值
- ClosePriceBeforeExRightsDiviend: 除權息前收盤價
- ExRightsDiviendQuote: 除權息參考價
- ...

注意事項：
- API 可能需要特定 Headers 或參數
- 回傳民國年日期，需轉換為西元年
- 資料範圍為未來除權除息預告
"""

import requests
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# TPEx OpenAPI 端點（需要 /v1/ 前綴）
TPEX_EXRIGHT_DAILY_URL = "https://www.tpex.org.tw/openapi/v1/tpex_exright_daily"

# 民國年日期格式：115年07月16日 → (115, 07, 16)
ROC_DATE_RE = re.compile(r"(\d{2,3})年(\d{1,2})月(\d{1,2})日")

# 簡易民國年格式：1150716 → (115, 07, 16)
ROC_DATE_SHORT_RE = re.compile(r"^(\d{2,3})(\d{2})(\d{2})$")


class TPExExRightCrawler:
    """TPEx 上櫃除權除息預告爬蟲"""

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
            "Referer": "https://www.tpex.org.tw/openapi/",
        })
        self.max_retries = max_retries
        self.delay = delay

    def fetch(self) -> List[Dict]:
        """
        抓取上櫃除權除息預告資料

        Returns:
            配息預告資料列表
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(
                    TPEX_EXRIGHT_DAILY_URL,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                # 處理可能的回應格式
                if isinstance(data, list):
                    records = self._parse_records(data)
                elif isinstance(data, dict):
                    # 可能包裝在某個 key 裡
                    records = self._parse_records(data.get("data", []))
                else:
                    logger.warning("TPEx API 回傳格式異常: %s", type(data))
                    return []

                logger.info("TPEx 除權除息預告抓取成功：%d 筆", len(records))
                return records

            except requests.exceptions.Timeout:
                logger.warning(
                    "TPEx API 請求逾時，%s 秒後重試 (%d/%d)",
                    self.delay * attempt, attempt, self.max_retries,
                )
            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    "TPEx API 連線失敗，%s 秒後重試 (%d/%d): %s",
                    self.delay * attempt, attempt, self.max_retries, e,
                )
            except Exception as e:
                logger.warning(
                    "TPEx API 請求失敗，%s 秒後重試 (%d/%d): %s",
                    self.delay * attempt, attempt, self.max_retries, e,
                )

            if attempt < self.max_retries:
                time.sleep(self.delay * attempt)

        logger.error("TPEx 除權除息預告抓取失敗，已達最大重試次數")
        return []

    def _parse_records(self, raw_data: List[Dict]) -> List[Dict]:
        """
        解析原始資料陣列

        Args:
            raw_data: API 回傳的原始資料陣列

        Returns:
            解析後的資料列表
        """
        records = []
        for item in raw_data:
            record = self._parse_single_record(item)
            if record:
                records.append(record)
        return records

    def _parse_single_record(self, item: Dict) -> Optional[Dict]:
        """
        解析單筆資料

        Args:
            item: 單筆原始資料

        Returns:
            解析後的資料字典，或 None（格式異常時）
        """
        try:
            # 取得股票代號
            code = item.get("SecuritiesCompanyCode", "").strip()
            if not code:
                return None

            # 取得名稱
            name = item.get("CompanyName", "").strip()
            if not name:
                return None

            # 解析除權息日期（格式：1150824 → 2026-08-24）
            ex_date_str = item.get("Date", "")
            ex_date = self._parse_date(ex_date_str)
            if not ex_date:
                logger.warning("無法解析日期: %s", ex_date_str)
                return None

            # 取得除權息類型
            ex_type = item.get("ExRightsDiviend", "").strip()

            # 解析現金股利
            cash_dividend = self._parse_number(item.get("CashDividend", "0"))

            # 解析股票股利（權值）
            stock_dividend = self._parse_number(item.get("StockDividend", "0"))

            return {
                "code": code,
                "name": name,
                "ex_date": ex_date,
                "type": ex_type,
                "cash_dividend": cash_dividend,
                "stock_dividend": stock_dividend,
                "source": "TPEx",
            }
        except (KeyError, ValueError, TypeError) as e:
            logger.warning("解析 TPEx 除權除息資料失敗: %s", e)
            return None

    def _parse_date(self, date_str: str) -> str:
        """
        解析日期字串為西元年

        支援格式：
        - 115年07月16日 → 2026-07-16
        - 1150716 → 2026-07-16
        - 2026-07-16 → 2026-07-16（已是西元年）

        Args:
            date_str: 日期字串

        Returns:
            西元年日期字串 (YYYY-MM-DD)，解析失敗回傳空字串
        """
        if not date_str:
            return ""

        date_str = date_str.strip()

        # 格式：115年07月16日
        match = ROC_DATE_RE.match(date_str)
        if match:
            roc_year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            ad_year = roc_year + 1911
            return f"{ad_year:04d}-{month:02d}-{day:02d}"

        # 格式：1150716
        match = ROC_DATE_SHORT_RE.match(date_str)
        if match:
            roc_year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            ad_year = roc_year + 1911
            return f"{ad_year:04d}-{month:02d}-{day:02d}"

        # 格式：2026-07-16（已是西元年）
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str

        logger.warning("無法解析日期格式: %s", date_str)
        return ""

    @staticmethod
    def _parse_number(text: str) -> float:
        """
        解析數字字串

        Args:
            text: 數字字串

        Returns:
            浮點數
        """
        if not text:
            return 0.0

        # 清理字串
        cleaned = str(text).strip().replace(",", "").replace("--", "0")
        cleaned = cleaned.replace("\u3000", "")  # 全形空格

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_tpex_exright_daily() -> List[Dict]:
    """
    抓取 TPEx 除權除息計算結果資料（便捷包裝）

    Returns:
        除權除息資料列表
    """
    crawler = TPExExRightCrawler()
    return crawler.fetch()
