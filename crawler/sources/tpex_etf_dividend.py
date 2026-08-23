"""
TPEx 上櫃 ETF 配息爬蟲
從證券櫃檯買賣中心（TPEx）抓取上櫃 ETF 配息資料

資料來源：
- Calendar: POST https://info.tpex.org.tw/api/etfExDivCalendar (data=lang:zh-tw)
- Popup:    POST https://info.tpex.org.tw/api/etfExDivPopup (data=stkNo:XXX, lang:zh-tw)

流程：
1. 查 calendar 取得每月配息 ETF 列表
2. 查 popup 取得各 ETF 詳細配息資訊

注意事項：
- info.tpex.org.tw SSL 憑證可能有問題，需 verify=False
- Popup 回傳歷史配息紀錄，需篩選當年度資料
"""

import re
import time
import logging
import urllib3
from typing import Dict, List, Optional

import requests
from requests.exceptions import RequestException

# 禁用 SSL 警告（info.tpex.org.tw 憑證有問題）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# TPEx API URLs
CALENDAR_URL = "https://info.tpex.org.tw/api/etfExDivCalendar"
POPUP_URL = "https://info.tpex.org.tw/api/etfExDivPopup"

# 民國年日期格式：115年07月16日 → (115, 07, 16)
ROC_DATE_RE = re.compile(r"(\d{2,3})年(\d{1,2})月(\d{1,2})日")


class TPExETFDividendCrawler:
    """TPEx 上櫃 ETF 配息爬蟲"""

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
            "Referer": "https://www.tpex.org.tw/",
            "X-Requested-With": "XMLHttpRequest",
        })
        self.max_retries = max_retries
        self.delay = delay

    # ------------------------------------------------------------------
    # HTTP 請求（帶重試）
    # ------------------------------------------------------------------

    def _request_with_retry(
        self, url: str, data: Optional[dict] = None,
    ) -> requests.Response:
        """
        帶有重試機制的 HTTP POST 請求。

        Args:
            url: 請求 URL
            data: POST 表單資料

        Returns:
            Response 物件

        Raises:
            RequestException: 超過最大重試次數後拋出最後一次例外
        """
        last_exception: Optional[RequestException] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(url, data=data, timeout=30, verify=False)
                resp.raise_for_status()
                return resp
            except RequestException as exc:
                last_exception = exc
                if attempt < self.max_retries:
                    wait = self.delay * attempt
                    logger.warning(
                        "請求失敗 (%s)，%s 秒後重試 (%d/%d): %s",
                        url, wait, attempt, self.max_retries, exc,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "請求失敗，已達最大重試次數 (%d): %s",
                        self.max_retries, exc,
                    )

        if last_exception is None:
            raise RuntimeError(
                "_request_with_retry: 所有重試均未拋出例外，但仍未成功"
            )
        raise last_exception

    # ------------------------------------------------------------------
    # 民國年日期解析
    # ------------------------------------------------------------------

    @staticmethod
    def _roc_date_to_ad(roc_date_str: str) -> str:
        """
        將民國年日期字串轉為西元年日期。

        格式：115年07月16日 → 2026-07-16

        Args:
            roc_date_str: 民國年日期字串

        Returns:
            西元年日期字串（YYYY-MM-DD），解析失敗回傳空字串
        """
        if not roc_date_str:
            return ""

        match = ROC_DATE_RE.search(roc_date_str)
        if not match:
            return ""

        roc_year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        ad_year = roc_year + 1911
        return f"{ad_year:04d}-{month:02d}-{day:02d}"

    # ------------------------------------------------------------------
    # Calendar API
    # ------------------------------------------------------------------

    def _fetch_calendar(self) -> Dict[str, List[Dict]]:
        """
        查詢配息月曆，取得每月配息的 ETF 列表。

        Returns:
            {月份: [{stockNo, stockName}, ...]} 字典
        """
        resp = self._request_with_retry(CALENDAR_URL, data={"lang": "zh-tw"})
        data = resp.json()

        calendar: Dict[str, List[Dict]] = {}
        for month_key, etf_list in data.items():
            calendar[month_key] = etf_list

        total = sum(len(v) for v in calendar.values())
        logger.info("Calendar 查詢成功：共 %d 個月份，%d 支 ETF", len(calendar), total)
        return calendar

    # ------------------------------------------------------------------
    # Popup API
    # ------------------------------------------------------------------

    def _fetch_popup(self, stock_no: str) -> List[Dict]:
        """
        查詢單一 ETF 的詳細配息資訊（含歷史紀錄）。

        Args:
            stock_no: ETF 代號（如 "00694B"）

        Returns:
            配息紀錄列表（原始格式）
        """
        resp = self._request_with_retry(
            POPUP_URL, data={"stkNo": stock_no, "lang": "zh-tw"},
        )
        return resp.json()

    # ------------------------------------------------------------------
    # Popup 解析
    # ------------------------------------------------------------------

    def _parse_popup_records(
        self, stock_no: str, stock_name: str, popup_data: List[Dict],
    ) -> List[Dict]:
        """
        將 popup 回傳的歷史配息紀錄轉為標準格式。

        標準格式：
        {
            "code": "00694B",
            "name": "富邦美債1-3",
            "ex_date": "2026-07-16",
            "pay_date": "2026-08-10",
            "cash_dividend": 0.317,
            "stock_dividend": 0.0,
            "source": "TPEx"
        }

        Args:
            stock_no: ETF 代號
            stock_name: ETF 名稱
            popup_data: popup API 回傳的配息紀錄列表

        Returns:
            標準化後的配息紀錄列表
        """
        records: List[Dict] = []

        for item in popup_data:
            ex_date = self._roc_date_to_ad(item.get("divDate", ""))
            pay_date = self._roc_date_to_ad(item.get("inDate", ""))
            amount_str = item.get("amount", "0")
            year_str = item.get("year", "")

            # 解析配息金額
            try:
                cash_dividend = float(amount_str)
            except (ValueError, TypeError):
                cash_dividend = 0.0

            # 取得民國年（用於篩選）
            try:
                roc_year = int(year_str)
            except (ValueError, TypeError):
                roc_year = 0

            records.append({
                "code": stock_no,
                "name": stock_name,
                "ex_date": ex_date,
                "pay_date": pay_date,
                "cash_dividend": cash_dividend,
                "stock_dividend": 0.0,
                "year": roc_year,
                "source": "TPEx",
            })

        return records

    # ------------------------------------------------------------------
    # 主 fetch 方法
    # ------------------------------------------------------------------

    def fetch(self, target_year: Optional[int] = None) -> List[Dict]:
        """
        抓取 TPEx 上櫃 ETF 配息資料。

        流程：
        1. 查 calendar 取得每月配息 ETF 列表
        2. 去重（同一 ETF 可能出現在多個月）
        3. 查 popup 取得各 ETF 歷史配息
        4. 篩選指定年份（民國年）的紀錄

        Args:
            target_year: 篩選的民國年（None 則取當前年度）。

        Returns:
            配息紀錄列表（標準格式）
        """
        # 取得當前民國年（作為預設篩選）
        from datetime import datetime
        if target_year is None:
            target_year = datetime.now().year - 1911

        # Step 1: 查 calendar
        calendar = self._fetch_calendar()

        # Step 2: 去重 ETF 列表（以 stockNo 為 key）
        etf_map: Dict[str, str] = {}
        for month_key, etf_list in calendar.items():
            for etf in etf_list:
                stock_no = etf.get("stockNo", "")
                stock_name = etf.get("stockName", "")
                if stock_no and stock_no not in etf_map:
                    etf_map[stock_no] = stock_name

        logger.info("Calendar 去重後共 %d 支 ETF", len(etf_map))

        # Step 3: 逐一查 popup 取得配息紀錄
        all_records: List[Dict] = []
        fetched = 0
        for stock_no, stock_name in etf_map.items():
            try:
                popup_data = self._fetch_popup(stock_no)
                records = self._parse_popup_records(
                    stock_no, stock_name, popup_data,
                )
                all_records.extend(records)
                fetched += 1

                if fetched % 20 == 0:
                    logger.info("已查詢 %d/%d 支 ETF", fetched, len(etf_map))

            except Exception as exc:
                logger.warning("查詢 ETF %s (%s) 失敗: %s", stock_no, stock_name, exc)

        logger.info("Popup 查詢完成：%d 支 ETF，共 %d 筆紀錄", fetched, len(all_records))

        # Step 4: 篩選指定民國年
        filtered = [r for r in all_records if r.get("year") == target_year]

        # 移除臨時 year 欄位
        for r in filtered:
            r.pop("year", None)

        logger.info(
            "篩選民國 %d 年：%d 筆（原始 %d 筆）",
            target_year, len(filtered), len(all_records),
        )

        return filtered


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_tpex_etf_dividend(target_year: Optional[int] = None) -> List[Dict]:
    """
    抓取 TPEx ETF 配息資料（便捷包裝）

    Args:
        target_year: 篩選的民國年（None 則取當前年度）

    Returns:
        配息紀錄列表
    """
    crawler = TPExETFDividendCrawler()
    return crawler.fetch(target_year=target_year)
