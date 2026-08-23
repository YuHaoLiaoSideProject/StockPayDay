"""
MoneyDJ 除權除息表爬蟲
從 MoneyDJ 理財網抓取除權除息資料（上市 + 上櫃 + ETF）

資料來源：https://www.moneydj.com/Z/ZE/ZEB/ZEB.djhtm
方法: GET
編碼: Big5 → UTF-8
表格結構:
  - 股票名稱藏在 GenLink2stk('代號','名稱') JS 函式中
  - 每列 14 個 <td>，包含除息日、現金股利、股票股利、現金增資等

技術細節：
  - 網頁用 Big5 編碼，需轉碼
  - 股票名稱需從 JS 函式中提取
  - 資料包含 ETF、個股、特別股等
"""

import re
import time
import logging
import urllib3
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

# MoneyDJ SSL 憑證有問題（Missing Subject Key Identifier），需停用驗證
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# MoneyDJ 除權除息表 URL
MONEYDJ_EXRIGHT_URL = "https://www.moneydj.com/Z/ZE/ZEB/ZEB.djhtm"


class MoneyDJExRightCrawler:
    """MoneyDJ 除權除息表爬蟲"""

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
            "Referer": "https://www.moneydj.com/",
        })
        self.max_retries = max_retries
        self.delay = delay

    def fetch(self) -> List[Dict]:
        """
        抓取除權除息資料

        Returns:
            除權除息資料列表
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(MONEYDJ_EXRIGHT_URL, timeout=30, verify=False)
                resp.raise_for_status()

                # MoneyDJ 使用 Big5 編碼，需轉碼
                resp.encoding = "big5"
                html = resp.text

                records = self._parse_html(html)

                # MoneyDJ 偶發回傳無資料頁面，解析到 0 筆時視為失敗重試
                if len(records) == 0:
                    raise RuntimeError("解析到 0 筆資料（可能為空頁面）")

                logger.info("MoneyDJ 除權除息抓取成功：%d 筆", len(records))
                return records

            except Exception as e:
                if attempt < self.max_retries:
                    wait = self.delay * attempt
                    logger.warning(
                        "MoneyDJ 請求失敗，%s 秒後重試 (%d/%d): %s",
                        wait, attempt, self.max_retries, e,
                    )
                    time.sleep(wait)
                else:
                    logger.error("MoneyDJ 請求失敗，已達最大重試次數: %s", e)
                    raise

        return []

    def _parse_html(self, html: str) -> List[Dict]:
        """
        解析 HTML 表格，提取除權除息資料

        Args:
            html: Big5 轉碼後的 HTML 內容

        Returns:
            除權除息資料列表
        """
        soup = BeautifulSoup(html, "html.parser")
        records: List[Dict] = []

        # 直接找所有包含 GenLink2stk 的 script，從其父 td 追溯到 tr
        scripts = soup.find_all("script", string=lambda s: s and "GenLink2stk" in s)
        for script in scripts:
            # script → td → tr
            td = script.parent
            if not td or td.name != "td":
                continue
            tr = td.parent
            if not tr or tr.name != "tr":
                continue

            record = self._parse_row(tr)
            if record:
                records.append(record)

        return records

    def _parse_row(self, row) -> Optional[Dict]:
        """
        解析一筆資料列

        HTML 結構：
        <tr>
          <td class="t3t1">
            <script>GenLink2stk('AP00679B','元大美債20年');</script>
          </td>
          <td class="t3n1">2026/08/21</td>  <!-- 除息日 -->
          <td class="t3n1">0.28</td>          <!-- 盈餘發放 -->
          <td class="t3n1">0</td>             <!-- 公積發放 -->
          <td class="t3n1">0.28</td>          <!-- 小計（現金股利） -->
          <td class="t3n1">2026/09/11</td>    <!-- 股利發放日 -->
          <td class="t3n1">&nbsp;</td>        <!-- 除權日 -->
          <td class="t3n1">&nbsp;</td>        <!-- 盈餘配股 -->
          <td class="t3n1">&nbsp;</td>        <!-- 公積配股 -->
          <td class="t3n1">0</td>             <!-- 小計（股票股利） -->
          <td class="t3n1">&nbsp;</td>        <!-- 現增除權日 -->
          <td class="t3n1">&nbsp;</td>        <!-- 現增股數 -->
          <td class="t3n1">&nbsp;</td>        <!-- 承銷價 -->
          <td class="t3n1">&nbsp;</td>        <!-- 現增股上市日 -->
        </tr>

        Args:
            row: BeautifulSoup <tr> 元素

        Returns:
            解析後的資料字典，或 None（非資料列時）
        """
        cells = row.find_all("td")
        if len(cells) < 6:
            return None

        # 從第一個 <td> 的 <script> 中提取代號和名稱
        first_cell = cells[0]
        script = first_cell.find("script")
        if not script:
            return None

        script_text = script.string or ""
        code, name = self._extract_code_name(script_text)
        if not code:
            return None

        # 解析各欄位
        try:
            # 現金股利（欄位 1-5）
            ex_date = self._normalize_date(cells[1].get_text(strip=True))
            earnings_dividend = self._parse_number(cells[2].get_text(strip=True))
            reserve_dividend = self._parse_number(cells[3].get_text(strip=True))
            cash_dividend = self._parse_number(cells[4].get_text(strip=True))
            pay_date = self._normalize_date(cells[5].get_text(strip=True))

            # 股票股利（欄位 6-9）
            ex_rights_date = self._normalize_date(cells[6].get_text(strip=True)) if len(cells) > 6 else ""
            earnings_stock = self._parse_number(cells[7].get_text(strip=True)) if len(cells) > 7 else 0.0
            reserve_stock = self._parse_number(cells[8].get_text(strip=True)) if len(cells) > 8 else 0.0
            stock_dividend = self._parse_number(cells[9].get_text(strip=True)) if len(cells) > 9 else 0.0

            # 排除僅有現金增資、无除權除息資料的紀錄
            has_dividend = ex_date or ex_rights_date
            if not has_dividend:
                return None

            # MoneyDJ 內部代號 → 實際證券代號（AP/AS/AR 前綴 + R 新上市標記）
            real_code = self._convert_code(code)

            # 除權除息類型：息 / 權 / 權息
            if ex_date and ex_rights_date:
                typ = "權息"
            elif ex_date:
                typ = "息"
            else:
                typ = "權"

            return {
                "code": real_code,
                "name": name,
                # 現金股利
                "ex_date": ex_date,
                "earnings_dividend": earnings_dividend,
                "reserve_dividend": reserve_dividend,
                "cash_dividend": cash_dividend,
                "pay_date": pay_date,
                # 股票股利
                "ex_rights_date": ex_rights_date,
                "earnings_stock": earnings_stock,
                "reserve_stock": reserve_stock,
                "stock_dividend": stock_dividend,
                "type": typ,
            }

        except (IndexError, ValueError) as e:
            logger.warning("解析 MoneyDJ 資料失敗 (%s): %s", code, e)
            return None

    @staticmethod
    def _convert_code(code: str) -> str:
        """
        MoneyDJ 內部代號 → 實際證券代號

        MoneyDJ 代號格式（市場前綴 + 實際代號）：
        - AP00679B → 00679B（ETF，P = 基金）
        - AS1453   → 1453（個股，S = 股票）
        - ASR7857  → 7857（近期掛牌個股，R 為 MoneyDJ 新上市標記）
        - AR9941A  → 9941A（特別股，R = 特別股）

        Args:
            code: MoneyDJ 內部代號

        Returns:
            實際證券代號
        """
        if code.startswith("AP"):
            return code[2:]
        if code.startswith("AR"):
            return code[2:]
        if code.startswith("AS"):
            return code[2:].lstrip("R")
        return code

    @staticmethod
    def _extract_code_name(script_text: str) -> tuple:
        """
        從 GenLink2stk JS 函式中提取代號和名稱

        格式: GenLink2stk('AP00679B','元大美債20年');

        Args:
            script_text: JS 函式文字

        Returns:
            (code, name) 元組，失敗則回傳 ("", "")
        """
        if not script_text:
            return "", ""

        # 匹配 GenLink2stk('代號','名稱')
        match = re.search(r"GenLink2stk\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)", script_text)
        if match:
            return match.group(1), match.group(2)

        return "", ""

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """
        標準化日期格式

        MoneyDJ 格式: 2026/08/21 → 2026-08-21

        Args:
            date_str: 原始日期字串

        Returns:
            標準化後的日期字串 (YYYY-MM-DD)，無效則回傳 ""
        """
        if not date_str or date_str == "&nbsp;":
            return ""

        # 移除空白和 &nbsp;
        cleaned = date_str.strip().replace("\u00a0", "").replace("&nbsp;", "")

        # 匹配 YYYY/MM/DD 格式
        match = re.match(r"(\d{4})/(\d{1,2})/(\d{1,2})", cleaned)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return f"{year:04d}-{month:02d}-{day:02d}"

        return ""

    @staticmethod
    def _parse_number(text: str) -> float:
        """
        解析數字字串

        Args:
            text: 數字字串（可能包含 &nbsp;、空白等）

        Returns:
            浮點數（解析失敗回 0.0）
        """
        if not text:
            return 0.0

        # 移除 &nbsp; 和空白
        cleaned = text.strip().replace("\u00a0", "").replace("&nbsp;", "")
        cleaned = cleaned.replace(",", "").replace("--", "0")

        if not cleaned or cleaned == "0":
            return 0.0

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0


# ------------------------------------------------------------------
# 模組級便捷函式
# ------------------------------------------------------------------

def fetch_moneydj_exright() -> List[Dict]:
    """
    抓取 MoneyDJ 除權除息資料（便捷包裝）

    Returns:
        除權除息資料列表
    """
    crawler = MoneyDJExRightCrawler()
    return crawler.fetch()
