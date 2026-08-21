"""
TWSE MOPS 配息爬蟲基底類別
抽取三個爬蟲共用的邏輯，子類別只需實作型別判斷與公開 API。
"""

import time
import logging
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# MOPS 配息公告 URL（三個爬蟲共用）
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"


class BaseCrawler:
    """TWSE MOPS 配息爬蟲基底類別"""

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
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        self.max_retries = max_retries
        self.delay = delay
        self._csrf_token: Optional[str] = None

    # ------------------------------------------------------------------
    # CSRF Token
    # ------------------------------------------------------------------

    def _get_csrf_token(self) -> str:
        """
        從 MOPS 頁面取得 CSRF Token。

        Returns:
            CSRF Token 字串（取不到則回傳空字串）
        """
        response = self._request_with_retry(MOPS_DIVIDEND_URL)
        soup = BeautifulSoup(response.text, "html.parser")

        for name in ("csrf_token", "_token", "token", "csrf"):
            tag = soup.find("input", {"name": name})
            if tag and tag.get("value"):
                token = tag["value"].strip()
                logger.info("CSRF token 取得成功 (%s)", name)
                return token

        logger.warning("未找到 CSRF token 欄位，嘗試繼續執行")
        return ""

    # ------------------------------------------------------------------
    # HTTP 請求（帶重試）
    # ------------------------------------------------------------------

    def _request_with_retry(
        self,
        url: str,
        method: str = "GET",
        data: Optional[dict] = None,
    ) -> requests.Response:
        """
        帶有重試機制的 HTTP 請求。

        Args:
            url: 請求 URL
            method: GET / POST
            data: POST 表單資料

        Returns:
            Response 物件

        Raises:
            RequestException: 超過最大重試次數後拋出最後一次例外
        """
        last_exception: Optional[RequestException] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if method.upper() == "POST":
                    resp = self.session.post(url, data=data, timeout=30)
                else:
                    resp = self.session.get(url, timeout=30)

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

        # max_retries >= 1 保證 last_exception 一定被賦值，但仍加守衛以防禦
        if last_exception is None:
            raise RuntimeError(
                "_request_with_retry: 所有重試均未拋出例外，但仍未成功"
            )
        raise last_exception

    # ------------------------------------------------------------------
    # 編碼偵測
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_encoding(response: requests.Response) -> str:
        """
        偵測回應編碼，優先使用 apparent_encoding（chardet 自動偵測）。

        Args:
            response: Response 物件

        Returns:
            編碼名稱字串
        """
        if response.apparent_encoding:
            return response.apparent_encoding

        content_type = response.headers.get("Content-Type", "")
        if "charset=" in content_type:
            return content_type.split("charset=")[-1].strip()

        return "utf-8"

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_number(text: str) -> float:
        """
        解析數字字串，處理逗號、空白、 '--' 等。

        Args:
            text: 原始文字

        Returns:
            浮點數（解析失敗回 0.0）
        """
        if not text:
            return 0.0
        cleaned = text.strip().replace(",", "").replace("--", "0").replace("\u3000", "")
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _roc_to_ad(roc_date: str) -> str:
        """
        民國年日期字串轉西元年。

        MOPS 格式常見：114/06/01 或 2025/06/01
        """
        if not roc_date:
            return ""

        normalized = roc_date.strip().replace("-", "/")
        parts = normalized.split("/")
        if len(parts) != 3:
            return roc_date

        try:
            year = int(parts[0])
        except ValueError:
            return roc_date

        if year > 1911:
            return f"{year:04d}-{parts[1]}-{parts[2]}"

        ad_year = year + 1911
        return f"{ad_year:04d}-{parts[1]}-{parts[2]}"

    # ------------------------------------------------------------------
    # HTML 表格解析（共用骨架，子類別可覆寫篩選邏輯）
    # ------------------------------------------------------------------

    def _is_target(self, code: str) -> bool:  # noqa: ARG002 — 子類別覆寫
        """
        判斷代號是否為本爬蟲的目標型別。
        預設回傳 True（全部通過），子類別應覆寫。
        """
        return True

    def _parse_html_table(self, html: str) -> List[Dict]:
        """
        解析 MOPS 回傳 HTML 中的配息資料表格，依 _is_target() 篩選。

        Args:
            html: MOPS 回傳的 HTML 內容

        Returns:
            配息資料列表
        """
        soup = BeautifulSoup(html, "html.parser")
        records: List[Dict] = []

        # 嘗試多種表格選擇器
        table = (
            soup.find("table", {"id": "table01"})
            or soup.find("table", class_="tableTF")
            or soup.find("table", class_=" tabel498")
        )
        if not table:
            logger.warning("找不到資料表格，嘗試掃描所有 <table>")
            tables = soup.find_all("table")
            for t in tables:
                rows = t.find_all("tr")
                if len(rows) > 2:
                    table = t
                    break

        if not table:
            logger.warning("HTML 中找不到任何可用表格")
            return records

        rows = table.find_all("tr")
        for row in rows[1:]:  # 跳過標題列
            cells = row.find_all("td")
            if len(cells) < 7:
                continue

            code = cells[0].get_text(strip=True)
            if not code or code == "合計":
                continue

            if not self._is_target(code):
                continue

            record = {
                "code": code,
                "name": cells[1].get_text(strip=True),
                "announce_date": cells[2].get_text(strip=True),
                "ex_date": cells[3].get_text(strip=True),
                "pay_date": cells[4].get_text(strip=True),
                "cash_dividend": self._parse_number(cells[5].get_text(strip=True)),
                "stock_dividend": self._parse_number(cells[6].get_text(strip=True)),
            }
            records.append(record)

        return records

    # ------------------------------------------------------------------
    # 通用 fetch（子類別實作 fetch_xxx_dividends_for_quarter 取得 raw 後呼叫）
    # ------------------------------------------------------------------

    def _fetch_raw_records(
        self, year: int, quarter: int, label: str,
    ) -> List[Dict]:
        """
        通用 fetch 邏輯：CSRF → POST → 編碼修正 → 解析表格。

        Args:
            year: 民國年
            quarter: 季度 1-4
            label: 用於 log 的標籤（如 "ETF"、"特別股"）

        Returns:
            原始配息紀錄列表
        """
        if not self._csrf_token:
            self._csrf_token = self._get_csrf_token()

        form_data = {
            "csrf_token": self._csrf_token,
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "keyword4": "",
            "code1": "",
            "ESSION": str(year),
            "ession1": str(quarter),
        }

        resp = self._request_with_retry(
            MOPS_DIVIDEND_URL, method="POST", data=form_data,
        )

        encoding = self._detect_encoding(resp)
        resp.encoding = encoding

        records = self._parse_html_table(resp.text)
        logger.info(
            "fetch_raw_records(%d, Q%d) [%s] — 解析到 %d 筆",
            year, quarter, label, len(records),
        )
        return records

    @staticmethod
    def _group_raw_records(
        raw_records: List[Dict],
        year: int,
        quarter: int,
        record_type: str,
    ) -> List[Dict]:
        """
        將原始紀錄依 code 分組並轉換格式。

        Args:
            raw_records: _fetch_raw_records 回傳的紀錄列表
            year: 民國年
            quarter: 季度
            record_type: 型別標籤（"stock"、"etf"、"preferred"）

        Returns:
            以 code 為 key 的字典列表
        """
        grouped: Dict[str, Dict] = {}
        for rec in raw_records:
            code = rec["code"]
            if code not in grouped:
                grouped[code] = {
                    "code": code,
                    "name": rec["name"],
                    "market": "TWSE",
                    "type": record_type,
                    "dividend_history": [],
                }

            announce = BaseCrawler._roc_to_ad(rec.get("announce_date", ""))
            ex = BaseCrawler._roc_to_ad(rec.get("ex_date", ""))
            pay = BaseCrawler._roc_to_ad(rec.get("pay_date", ""))

            entry = {
                "year": year + 1911 if year < 1000 else year,
                "quarter": quarter,
                "announce_date": announce,
                "ex_date": ex,
                "pay_date": pay,
                "cash_dividend": rec["cash_dividend"],
                "stock_dividend": rec["stock_dividend"],
            }
            grouped[code]["dividend_history"].append(entry)

        for item in grouped.values():
            item["dividend_history"].sort(
                key=lambda x: (x["year"], x["quarter"]), reverse=True,
            )

        return list(grouped.values())
