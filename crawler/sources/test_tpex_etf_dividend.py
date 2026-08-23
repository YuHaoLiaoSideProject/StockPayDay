"""
單元測試 — TPEx ETF 配息爬蟲（tpex_etf_dividend）

覆蓋：
- _roc_date_to_ad 民國年日期轉換
- _parse_popup_records 配息紀錄解析
- fetch 正常流程（mock）
"""

from unittest.mock import MagicMock, patch

from crawler.sources.tpex_etf_dividend import TPExETFDividendCrawler


class TestTPExETFDividendCrawler:
    def setup_method(self):
        self.crawler = TPExETFDividendCrawler(max_retries=1, delay=0)

    # ------------------------------------------------------------------
    # _roc_date_to_ad
    # ------------------------------------------------------------------

    def test_roc_date_to_ad_normal(self):
        """正常民國年日期轉換"""
        assert TPExETFDividendCrawler._roc_date_to_ad("115年07月16日") == "2026-07-16"

    def test_roc_date_to_ad_single_digit_month_day(self):
        """單位數月日補零"""
        assert TPExETFDividendCrawler._roc_date_to_ad("114年1月5日") == "2025-01-05"

    def test_roc_date_to_ad_empty(self):
        """空字串回傳空字串"""
        assert TPExETFDividendCrawler._roc_date_to_ad("") == ""

    def test_roc_date_to_ad_none(self):
        """None 回傳空字串"""
        assert TPExETFDividendCrawler._roc_date_to_ad(None) == ""

    def test_roc_date_to_ad_invalid(self):
        """格式異常回傳空字串"""
        assert TPExETFDividendCrawler._roc_date_to_ad("not a date") == ""

    # ------------------------------------------------------------------
    # _parse_popup_records
    # ------------------------------------------------------------------

    def test_parse_popup_records_normal(self):
        """正常解析 popup 資料"""
        popup_data = [
            {
                "amount": "0.317",
                "stockName": "富邦美債1-3",
                "divDate": "115年07月16日",
                "year": "115",
                "inDate": "115年08月10日",
                "inBaseDate": "115年07月22日",
                "stockNo": "00694B",
            }
        ]
        records = self.crawler._parse_popup_records("00694B", "富邦美債1-3", popup_data)
        assert len(records) == 1
        rec = records[0]
        assert rec["code"] == "00694B"
        assert rec["name"] == "富邦美債1-3"
        assert rec["ex_date"] == "2026-07-16"
        assert rec["pay_date"] == "2026-08-10"
        assert rec["cash_dividend"] == 0.317
        assert rec["stock_dividend"] == 0.0
        assert rec["source"] == "TPEx"
        assert rec["year"] == 115

    def test_parse_popup_records_multiple(self):
        """解析多筆 popup 資料"""
        popup_data = [
            {
                "amount": "0.317",
                "stockName": "富邦美債1-3",
                "divDate": "115年07月16日",
                "year": "115",
                "inDate": "115年08月10日",
                "inBaseDate": "115年07月22日",
                "stockNo": "00694B",
            },
            {
                "amount": "0.256",
                "stockName": "富邦美債1-3",
                "divDate": "115年04月20日",
                "year": "115",
                "inDate": "115年05月15日",
                "inBaseDate": "115年04月26日",
                "stockNo": "00694B",
            },
        ]
        records = self.crawler._parse_popup_records("00694B", "富邦美債1-3", popup_data)
        assert len(records) == 2
        assert records[0]["cash_dividend"] == 0.317
        assert records[1]["cash_dividend"] == 0.256

    def test_parse_popup_records_empty(self):
        """空 popup 資料回傳空列表"""
        records = self.crawler._parse_popup_records("00694B", "富邦美債1-3", [])
        assert records == []

    def test_parse_popup_records_invalid_amount(self):
        """配息金額異常時回傳 0.0"""
        popup_data = [
            {
                "amount": "N/A",
                "stockName": "測試ETF",
                "divDate": "115年07月16日",
                "year": "115",
                "inDate": "115年08月10日",
                "inBaseDate": "115年07月22日",
                "stockNo": "9999",
            }
        ]
        records = self.crawler._parse_popup_records("9999", "測試ETF", popup_data)
        assert records[0]["cash_dividend"] == 0.0

    # ------------------------------------------------------------------
    # fetch（mock）
    # ------------------------------------------------------------------

    @patch("crawler.sources.tpex_etf_dividend.TPExETFDividendCrawler._fetch_popup")
    @patch("crawler.sources.tpex_etf_dividend.TPExETFDividendCrawler._fetch_calendar")
    def test_fetch_filters_by_year(self, mock_calendar, mock_popup):
        """fetch 只回傳指定民國年的紀錄"""
        mock_calendar.return_value = {
            "07": [
                {"stockName": "富邦美債1-3", "stockNo": "00694B"},
            ],
            "08": [
                {"stockName": "元大台灣50", "stockNo": "0050"},
            ],
        }

        def fake_popup(stock_no):
            if stock_no == "00694B":
                return [
                    {
                        "amount": "0.317",
                        "stockName": "富邦美債1-3",
                        "divDate": "115年07月16日",
                        "year": "115",
                        "inDate": "115年08月10日",
                        "inBaseDate": "115年07月22日",
                        "stockNo": "00694B",
                    },
                    {
                        "amount": "0.256",
                        "stockName": "富邦美債1-3",
                        "divDate": "114年04月20日",
                        "year": "114",
                        "inDate": "114年05月15日",
                        "inBaseDate": "114年04月26日",
                        "stockNo": "00694B",
                    },
                ]
            elif stock_no == "0050":
                return [
                    {
                        "amount": "1.5",
                        "stockName": "元大台灣50",
                        "divDate": "115年08月25日",
                        "year": "115",
                        "inDate": "115年09月15日",
                        "inBaseDate": "115年09月05日",
                        "stockNo": "0050",
                    },
                ]
            return []

        mock_popup.side_effect = fake_popup

        records = self.crawler.fetch(target_year=115)

        # 只有 115 年的紀錄（2 筆）
        assert len(records) == 2
        codes = {r["code"] for r in records}
        assert codes == {"00694B", "0050"}

        # 確認 year 欛位已被移除
        for r in records:
            assert "year" not in r

    @patch("crawler.sources.tpex_etf_dividend.TPExETFDividendCrawler._fetch_popup")
    @patch("crawler.sources.tpex_etf_dividend.TPExETFDividendCrawler._fetch_calendar")
    def test_fetch_deduplicates_etfs(self, mock_calendar, mock_popup):
        """同一 ETF 出現在多個月時只查詢一次"""
        mock_calendar.return_value = {
            "07": [
                {"stockName": "國泰20年美債", "stockNo": "00687B"},
            ],
            "08": [
                {"stockName": "國泰20年美債", "stockNo": "00687B"},
            ],
        }
        mock_popup.return_value = []

        self.crawler.fetch(target_year=115)

        # 只呼叫一次 popup
        assert mock_popup.call_count == 1
        mock_popup.assert_called_with("00687B")

    @patch("crawler.sources.tpex_etf_dividend.TPExETFDividendCrawler._fetch_popup")
    @patch("crawler.sources.tpex_etf_dividend.TPExETFDividendCrawler._fetch_calendar")
    def test_fetch_handles_popup_failure(self, mock_calendar, mock_popup):
        """個別 ETF popup 失敗不影響其他 ETF"""
        mock_calendar.return_value = {
            "07": [
                {"stockName": "富邦美債1-3", "stockNo": "00694B"},
                {"stockName": "元大台灣50", "stockNo": "0050"},
            ],
        }

        def fake_popup(stock_no):
            if stock_no == "00694B":
                raise Exception("Network error")
            return [
                {
                    "amount": "1.5",
                    "stockName": "元大台灣50",
                    "divDate": "115年08月25日",
                    "year": "115",
                    "inDate": "115年09月15日",
                    "inBaseDate": "115年09月05日",
                    "stockNo": "0050",
                },
            ]

        mock_popup.side_effect = fake_popup

        records = self.crawler.fetch(target_year=115)

        # 只有 0050 的紀錄
        assert len(records) == 1
        assert records[0]["code"] == "0050"
