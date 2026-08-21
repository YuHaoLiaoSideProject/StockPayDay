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

import time
import logging
from typing import Dict, List, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# MOPS 配息公告 URL
MOPS_DIVIDEND_URL = "https://mops.twse.com.tw/mops/web/t05st09_ifrs"


class TWSEPreferredCrawler:
    """TWSE 特別股配息爬蟲"""

    def __init__(self, max_retries: int = 3, delay: float = 2.0):
        """
        初始化爬蟲

        Args:
            max_retries: 最大重試次數
            delay: 重試間隔秒數（會遞增）
        """
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

        raise last_exception  # type: ignore[misc]

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
    # 特別股判斷
    # ------------------------------------------------------------------

    @staticmethod
    def _is_preferred_stock(code: str) -> bool:
        """
        判斷是否為特別股。

        特別股代號特徵：
        - 4 位數字且 >= 7000（如 7654）
        - 或帶字母後綴（如 2330A、2330B）

        Args:
            code: 證券代號字串

        Returns:
            是否為特別股
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

    # ------------------------------------------------------------------
    # 抓取配息列表
    # ------------------------------------------------------------------

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
        # 1. 取得 CSRF Token
        if not self._csrf_token:
            self._csrf_token = self._get_csrf_token()

        # 2. 組裝 POST 表單
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

        # 3. POST 請求
        resp = self._request_with_retry(
            MOPS_DIVIDEND_URL, method="POST", data=form_data,
        )

        # 4. 編碼修正
        encoding = self._detect_encoding(resp)
        resp.encoding = encoding

        # 5. 解析 HTML 表格，篩選特別股
        records = self._parse_html_table_for_preferred(resp.text)
        logger.info(
            "fetch_preferred_dividends_for_quarter(%d, Q%d) — 解析到 %d 筆特別股",
            year, quarter, len(records),
        )
        return records

    # ------------------------------------------------------------------
    # HTML 表格解析
    # ------------------------------------------------------------------

    def _parse_html_table_for_preferred(self, html: str) -> List[Dict]:
        """
        解析 MOPS 回傳 HTML 中的配息資料表格，篩選特別股。

        Args:
            html: MOPS 回傳的 HTML 內容

        Returns:
            特別股配息資料列表
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

            # 篩選特別股
            if not self._is_preferred_stock(code):
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
            return f"{year:04d}-{parts[1]:02d}-{parts[2]:02d}"

        ad_year = year + 1911
        return f"{ad_year:04d}-{parts[1]:02d}-{parts[2]:02d}"

    # ------------------------------------------------------------------
    # 對外 API：抓取並轉換
    # ------------------------------------------------------------------

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
            - raw_data: 原始紀錄列表（直接來自 MOPS）
            - processed_preferred: 以 code 為 key 的字典列表，
              符合 data/preferred/{code}.json 格式
        """
        raw_records = self.fetch_preferred_dividends_for_quarter(year, quarter)

        # 依 code 分組
        grouped: Dict[str, Dict] = {}
        for rec in raw_records:
            code = rec["code"]
            if code not in grouped:
                grouped[code] = {
                    "code": code,
                    "name": rec["name"],
                    "market": "TWSE",
                    "type": "preferred",
                    "dividend_history": [],
                }

            announce = self._roc_to_ad(rec.get("announce_date", ""))
            ex = self._roc_to_ad(rec.get("ex_date", ""))
            pay = self._roc_to_ad(rec.get("pay_date", ""))

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

        # 排序 dividend_history（新到舊）
        for pref in grouped.values():
            pref["dividend_history"].sort(
                key=lambda x: (x["year"], x["quarter"]), reverse=True,
            )

        processed = list(grouped.values())
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
