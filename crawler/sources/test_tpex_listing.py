"""
單元測試 — TPEx 上櫃清單爬蟲（tpex_listing）

覆蓋：
- _to_roc_date 民國日期轉換
- _parse_row 正常解析、權證排除、格式異常排除
"""
from datetime import datetime

from crawler.sources.tpex_listing import TPExListingCrawler


class TestTPExListingCrawler:
    def setup_method(self):
        self.crawler = TPExListingCrawler(max_retries=1, delay=0)

    def test_to_roc_date(self):
        """西元日期轉民國日期"""
        assert TPExListingCrawler._to_roc_date(datetime(2026, 8, 21)) == "115/08/21"
        assert TPExListingCrawler._to_roc_date(datetime(2026, 1, 5)) == "115/01/05"

    def test_parse_row_otc_stock(self):
        """上櫃普通股正常解析"""
        row = ["4126", "太醫", "92.30", "+0.30", "92.10", "92.50", "92.10"]
        assert self.crawler._parse_row(row) == {
            "code": "4126", "name": "太醫", "market": "TPEx",
        }

    def test_parse_row_otc_etf(self):
        """上櫃債券 ETF 正常解析"""
        row = ["00687B", "國泰20年美債", "27.19", "-0.24"]
        assert self.crawler._parse_row(row) == {
            "code": "00687B", "name": "國泰20年美債", "market": "TPEx",
        }

    def test_skip_warrant(self):
        """7 開頭 6 位純數字的上櫃權證應排除"""
        row = ["739986", "廣明國票5B購01", "0.50", "+0.02"]
        assert self.crawler._parse_row(row) is None

    def test_skip_invalid_code(self):
        """格式異常的代號應排除"""
        row = ["ABC", "名稱"]
        assert self.crawler._parse_row(row) is None

    def test_skip_empty_name(self):
        """名稱為空應排除"""
        row = ["4126", ""]
        assert self.crawler._parse_row(row) is None

    def test_skip_short_row(self):
        """欄位不足應排除（不拋例外）"""
        row: list = []
        assert self.crawler._parse_row(row) is None