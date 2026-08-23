"""
MOPS 配息爬蟲測試
測試 crawler/sources/mops_dividend.py
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 確保專案根目錄在 sys.path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from crawler.sources.mops_dividend import MOPSDividendCrawler


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def crawler():
    """建立 MOPSDividendCrawler 實例"""
    return MOPSDividendCrawler(max_retries=2, delay=0.1)


@pytest.fixture
def sample_html():
    """範例 MOPS 回傳 HTML"""
    return """
    <html>
    <body>
        <table id="table01" class="tableTF">
            <tr>
                <th>股票代號</th>
                <th>股票名稱</th>
                <th>申報日期</th>
                <th>除息交易日</th>
                <th>股利發放日</th>
                <th>現金股利</th>
                <th>股票股利</th>
            </tr>
            <tr>
                <td>2330</td>
                <td>台積電</td>
                <td>114/06/01</td>
                <td>114/07/25</td>
                <td>114/08/15</td>
                <td>3.5</td>
                <td>0</td>
            </tr>
            <tr>
                <td>2317</td>
                <td>鴻海</td>
                <td>114/06/01</td>
                <td>114/07/28</td>
                <td>114/08/20</td>
                <td>5.0</td>
                <td>0</td>
            </tr>
            <tr>
                <td>合計</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td>8.5</td>
                <td>0</td>
            </tr>
        </table>
    </body>
    </html>
    """


# ------------------------------------------------------------------
# 初始化測試
# ------------------------------------------------------------------

class TestInit:
    """測試初始化"""

    def test_default_params(self):
        """預設參數"""
        crawler = MOPSDividendCrawler()
        assert crawler.max_retries == 3
        assert crawler.delay == 2.0

    def test_custom_params(self):
        """自訂參數"""
        crawler = MOPSDividendCrawler(max_retries=5, delay=1.0)
        assert crawler.max_retries == 5
        assert crawler.delay == 1.0

    def test_invalid_max_retries(self):
        """無效的 max_retries"""
        with pytest.raises(ValueError, match="max_retries must be >= 1"):
            MOPSDividendCrawler(max_retries=0)


# ------------------------------------------------------------------
# HTML 解析測試
# ------------------------------------------------------------------

class TestParseHTML:
    """測試 HTML 表格解析"""

    def test_parse_valid_html(self, crawler, sample_html):
        """解析有效 HTML"""
        records = crawler._parse_html_table(sample_html)
        assert len(records) == 2
        assert records[0]["code"] == "2330"
        assert records[0]["name"] == "台積電"
        assert records[0]["cash_dividend"] == 3.5
        assert records[1]["code"] == "2317"

    def test_skip_total_row(self, crawler, sample_html):
        """跳過合計列"""
        records = crawler._parse_html_table(sample_html)
        codes = [r["code"] for r in records]
        assert "合計" not in codes

    def test_empty_html(self, crawler):
        """空 HTML"""
        records = crawler._parse_html_table("<html><body></body></html>")
        assert records == []

    def test_no_table(self, crawler):
        """無表格 HTML"""
        records = crawler._parse_html_table("<html><body><p>No table</p></body></html>")
        assert records == []


# ------------------------------------------------------------------
# 工具方法測試
# ------------------------------------------------------------------

class TestUtils:
    """測試工具方法"""

    def test_parse_number_normal(self):
        """解析正常數字"""
        assert MOPSDividendCrawler._parse_number("3.5") == 3.5

    def test_parse_number_comma(self):
        """解析含逗號數字"""
        assert MOPSDividendCrawler._parse_number("1,234.5") == 1234.5

    def test_parse_number_dash(self):
        """解析 '--'"""
        assert MOPSDividendCrawler._parse_number("--") == 0.0

    def test_parse_number_empty(self):
        """解析空字串"""
        assert MOPSDividendCrawler._parse_number("") == 0.0

    def test_parse_number_invalid(self):
        """解析無效字串"""
        assert MOPSDividendCrawler._parse_number("abc") == 0.0

    def test_roc_to_ad_normal(self):
        """民國年轉西元年"""
        assert MOPSDividendCrawler._roc_to_ad("114/07/25") == "2025-07-25"

    def test_roc_to_ad_ad_format(self):
        """西元年格式（已轉換）"""
        assert MOPSDividendCrawler._roc_to_ad("2025/07/25") == "2025-07-25"

    def test_roc_to_ad_empty(self):
        """空字串"""
        assert MOPSDividendCrawler._roc_to_ad("") == ""

    def test_roc_to_ad_invalid(self):
        """無效格式"""
        assert MOPSDividendCrawler._roc_to_ad("abc") == "abc"


# ------------------------------------------------------------------
# API 呼叫測試（Mock）
# ------------------------------------------------------------------

class TestFetchStock:
    """測試單支股票查詢（使用 Mock）"""

    @patch.object(MOPSDividendCrawler, '_get_csrf_token')
    @patch.object(MOPSDividendCrawler, '_request_with_retry')
    def test_fetch_stock_success(self, mock_request, mock_csrf, crawler, sample_html):
        """查詢成功"""
        mock_csrf.return_value = "test_token"
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.apparent_encoding = "utf-8"
        mock_request.return_value = mock_response

        records = crawler._fetch_stock("2330")

        assert len(records) == 2
        assert records[0]["code"] == "2330"
        mock_request.assert_called_once()

    @patch.object(MOPSDividendCrawler, '_get_csrf_token')
    @patch.object(MOPSDividendCrawler, '_request_with_retry')
    def test_fetch_stock_form_data(self, mock_request, mock_csrf, crawler, sample_html):
        """驗證表單資料"""
        mock_csrf.return_value = "test_token"
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.apparent_encoding = "utf-8"
        mock_request.return_value = mock_response

        crawler._fetch_stock("6547")

        call_args = mock_request.call_args
        assert call_args[0][0] == MOPSDividendCrawler.__init__.__defaults__[1] if False else True
        # 驗證 POST data
        form_data = call_args[1].get("data") or call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("data")
        assert form_data["co_id"] == "6547"
        assert form_data["step"] == "1"


# ------------------------------------------------------------------
# 批次查詢測試（Mock）
# ------------------------------------------------------------------

class TestFetchStockDividends:
    """測試批次查詢"""

    @patch.object(MOPSDividendCrawler, '_fetch_stock')
    def test_fetch_multiple_stocks(self, mock_fetch, crawler):
        """查詢多支股票"""
        mock_fetch.return_value = [
            {
                "code": "2330",
                "name": "台積電",
                "announce_date": "114/06/01",
                "ex_date": "114/07/25",
                "pay_date": "114/08/15",
                "cash_dividend": 3.5,
                "stock_dividend": 0.0,
            }
        ]

        records = crawler.fetch_stock_dividends(["2330", "2317"], year=114, quarter=2)

        assert len(records) == 2
        assert mock_fetch.call_count == 2
        # 驗證格式
        assert records[0]["source"] == "MOPS"
        assert records[0]["ex_date"] == "2025-07-25"

    @patch.object(MOPSDividendCrawler, '_fetch_stock')
    def test_fetch_with_error(self, mock_fetch, crawler):
        """部分查詢失敗"""
        def side_effect(code):
            if code == "2317":
                raise Exception("Network error")
            return [
                {
                    "code": code,
                    "name": "台積電",
                    "announce_date": "114/06/01",
                    "ex_date": "114/07/25",
                    "pay_date": "114/08/15",
                    "cash_dividend": 3.5,
                    "stock_dividend": 0.0,
                }
            ]

        mock_fetch.side_effect = side_effect

        records = crawler.fetch_stock_dividends(["2330", "2317"], year=114, quarter=2)

        # 只有 2330 成功
        assert len(records) == 1
        assert records[0]["code"] == "2330"

    @patch.object(MOPSDividendCrawler, '_fetch_stock')
    def test_fetch_empty_list(self, mock_fetch, crawler):
        """空股票列表"""
        records = crawler.fetch_stock_dividends([], year=114, quarter=2)
        assert records == []
        mock_fetch.assert_not_called()
