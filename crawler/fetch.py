"""
StockPayDay++ 主爬蟲腳本
負責協調所有爬蟲模組，抓取 TWSE 配息資料

使用方式：
    python crawler/fetch.py              # 執行所有爬蟲
    python crawler/fetch.py --twt48u     # 僅執行 TWT48U
    python crawler/fetch.py --mops 114 2 # 僅執行 MOPS（指定年季）
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 確保專案根目錄在 sys.path，讓 `from crawler.xxx` 能正確解析
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = ROOT_DIR / "data"
DATA_TWT48U_DIR = ROOT_DIR / "data" / "twses"
DATA_MOPS_DIR = ROOT_DIR / "data" / "mops"
DATA_LISTINGS_DIR = ROOT_DIR / "data" / "listings"


# ------------------------------------------------------------------
# 目錄管理
# ------------------------------------------------------------------

def ensure_dirs() -> None:
    """確保資料目錄存在"""
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "stocks").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "etfs").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "preferred").mkdir(parents=True, exist_ok=True)
    DATA_TWT48U_DIR.mkdir(parents=True, exist_ok=True)
    DATA_MOPS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_LISTINGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("資料目錄已確認: %s", DATA_DIR)


# ------------------------------------------------------------------
# MOPS 資料儲存
# ------------------------------------------------------------------

def save_raw(data: list, filename: str) -> Path:
    """
    儲存原始資料到 data/raw/{date}/

    Args:
        data: 原始配息紀錄列表
        filename: 檔名（不含副檔名，自動加 .json）

    Returns:
        儲存路徑
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    raw_dir = DATA_DIR / "raw" / date_str
    raw_dir.mkdir(parents=True, exist_ok=True)

    if not filename.endswith(".json"):
        filename += ".json"

    filepath = raw_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("原始資料已儲存: %s (%d 筆)", filepath, len(data))
    return filepath


def save_stock(stock_data: dict, subfolder: str = "stocks") -> Path:
    """
    儲存證券基底資料到 data/{subfolder}/{code}.json。
    自動合併已有歷史資料，避免重複。

    Args:
        stock_data: 證券資料字典（需含 code, dividend_history）
        subfolder: 子目錄名稱（stocks / etfs / preferred）

    Returns:
        儲存路徑
    """
    code = stock_data["code"]
    filepath = DATA_DIR / subfolder / f"{code}.json"

    # 讀取舊資料
    existing: Dict = {}
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)

    # 合併歷史：以 (year, quarter) 為 key 去重
    history_map: Dict[tuple, Dict] = {}
    for h in existing.get("dividend_history", []):
        key = (h["year"], h["quarter"])
        history_map[key] = h

    for h in stock_data.get("dividend_history", []):
        key = (h["year"], h["quarter"])
        history_map[key] = h

    # 排序（新到舊）
    merged_history = sorted(
        history_map.values(),
        key=lambda x: (x["year"], x["quarter"]),
        reverse=True,
    )

    stock_data["dividend_history"] = merged_history
    stock_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(stock_data, f, ensure_ascii=False, indent=2)

    logger.info("個股資料已儲存: %s (%d 筆歷史)", filepath, len(merged_history))
    return filepath


# ------------------------------------------------------------------
# TWT48U 資料儲存
# ------------------------------------------------------------------

def save_twt48u(records: List[Dict]) -> dict[str, Path]:
    """
    儲存 TWT48U 資料到月分檔案

    檔案結構：
    data/twses/
    ├── 2026-08.json    # 8月除息預告
    ├── 2026-09.json    # 9月除息預告
    └── 2026-10.json    # 10月除息預告

    Args:
        records: 配息資料列表

    Returns:
        {月份: 檔案路徑} 字典
    """
    saved_files: Dict[str, Path] = {}

    # 依月份分組
    by_month: Dict[str, List[Dict]] = {}
    for rec in records:
        month = rec["ex_date"][:7]  # "2026-08"
        by_month.setdefault(month, []).append(rec)

    # 合併到各月檔案
    for month, new_records in by_month.items():
        filepath = DATA_TWT48U_DIR / f"{month}.json"

        # 讀取舊資料
        old_records: List[Dict] = []
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                old_records = data.get("records", [])

        # 合併（以 code + ex_date 為 key 去重）
        merged = _merge_twt48u_records(old_records, new_records)

        # 寫入
        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "records": merged,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        saved_files[month] = filepath
        logger.info("已儲存 %s.json：%d 筆", month, len(merged))

    return saved_files


def _merge_twt48u_records(old: List[Dict], new: List[Dict]) -> List[Dict]:
    """
    合併兩筆資料列表，以 (code, ex_date) 為 key 去重

    Args:
        old: 舊資料
        new: 新資料

    Returns:
        合併後的資料列表
    """
    # 建立 lookup
    lookup: Dict[tuple, Dict] = {}
    for rec in old:
        key = (rec["code"], rec["ex_date"])
        lookup[key] = rec

    # 新資料覆蓋舊資料
    for rec in new:
        key = (rec["code"], rec["ex_date"])
        lookup[key] = rec

    # 排序（依 ex_date）
    merged = sorted(lookup.values(), key=lambda x: x["ex_date"])
    return merged


# ------------------------------------------------------------------
# 年季工具
# ------------------------------------------------------------------

def get_current_year_quarter() -> tuple:
    """
    取得當前民國年和季度。

    Returns:
        (roc_year, quarter)
        roc_year: 民國年（整數）
        quarter: 季度 1-4
    """
    now = datetime.now()
    ad_year = now.year
    roc_year = ad_year - 1911
    quarter = (now.month - 1) // 3 + 1
    return roc_year, quarter


# ------------------------------------------------------------------
# TWT48U 主流程
# ------------------------------------------------------------------

def fetch_twt48u() -> None:
    """
    執行 TWT48U 爬蟲並儲存資料

    從 TWSE 抓取未來除權除息預告資料，儲存到 data/twses/{YYYY-MM}.json
    """
    from crawler.sources.twse_twt48u import TWT48UCrawler

    logger.info("\n📋 抓取 TWT48U 除息預告資料...")

    crawler = TWT48UCrawler(max_retries=3, delay=2.0)

    try:
        records = crawler.fetch()
    except Exception as exc:
        logger.error("❌ TWT48U 爬蟲失敗: %s", exc)
        return

    if not records:
        logger.warning("TWT48U 無資料（可能尚無除息預告）")
        return

    # 儲存資料
    saved_files = save_twt48u(records)

    logger.info(
        "✅ TWT48U 完成：共 %d 筆，儲存 %d 個月分檔案",
        len(records), len(saved_files),
    )


# ------------------------------------------------------------------
# MOPS 主流程（個股/ETF/特別股）
# ------------------------------------------------------------------

def save_mops_aggregated(stocks: List[Dict], year: int, quarter: int) -> Path:
    """
    將 MOPS 資料寫入 data/mops/{year}Q{quarter}.json（供 processor 讀取）。

    輸出格式：
    {
        "year": 114,
        "quarter": 2,
        "records": [
            {
                "code": "2330",
                "name": "台積電",
                "ex_date": "2025-07-25",
                "pay_date": "2025-08-15",
                "cash_dividend": 3.5,
                "stock_dividend": 0.0
            }
        ]
    }

    Args:
        stocks: 由 _group_raw_records 產出的分組資料列表
        year: 民國年
        quarter: 季度

    Returns:
        儲存路徑
    """
    records: List[Dict] = []
    for stock in stocks:
        for entry in stock.get("dividend_history", []):
            # 只保留與本次 fetch 年季相符的紀錄
            if entry.get("year") == year and entry.get("quarter") == quarter:
                records.append({
                    "code": stock["code"],
                    "name": stock["name"],
                    "ex_date": entry.get("ex_date", ""),
                    "pay_date": entry.get("pay_date", ""),
                    "cash_dividend": entry.get("cash_dividend", 0),
                    "stock_dividend": entry.get("stock_dividend", 0),
                })

    filepath = DATA_MOPS_DIR / f"{year}Q{quarter}.json"
    output = {
        "year": year,
        "quarter": quarter,
        "records": records,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("MOPS 聚合資料已儲存: %s (%d 筆)", filepath, len(records))
    return filepath


def fetch_mops(year: int, quarter: int) -> None:
    """
    執行 MOPS 爬蟲（個股/ETF/特別股）並儲存資料

    Args:
        year: 民國年
        quarter: 季度 1-4
    """
    from crawler.sources.twse_stock import TWSEStockCrawler

    logger.info("\n📋 抓取 MOPS 配息資料...")

    # 初始化爬蟲
    crawler = TWSEStockCrawler(max_retries=3, delay=2.0)

    # 抓取資料
    logger.info("🕷️ 開始抓取個股配息資料...")
    raw_data, stocks = crawler.fetch_stock_dividends(year, quarter)

    if not raw_data:
        logger.warning("本次抓取無資料（可能尚未公告或 API 回傳空表格）")
        return

    # 儲存原始資料
    raw_filename = f"twse_dividend_{year}Q{quarter}"
    save_raw(raw_data, raw_filename)

    # 儲存個股基底資料（data/stocks/{code}.json）
    saved_count = 0
    for stock in stocks:
        try:
            save_stock(stock, "stocks")
            saved_count += 1
        except Exception as exc:
            logger.error("儲存個股 %s 失敗: %s", stock.get("code", "?"), exc)

    # 儲存聚合資料供 processor 使用（data/mops/{year}Q{quarter}.json）
    try:
        save_mops_aggregated(stocks, year, quarter)
    except Exception as exc:
        logger.error("儲存 MOPS 聚合資料失敗: %s", exc)

    logger.info(
        "✅ 個股完成：共儲存 %d 支（原始 %d 筆）",
        saved_count, len(raw_data),
    )


def fetch_listing() -> None:
    """
    執行上市（TWSE）+ 上櫃（TPEx）證券清單爬蟲並儲存資料

    - TWSE 上市清單 → data/listings/{YYYY-MM}.json
    - TPEx 上櫃清單 → data/listings/{YYYY-MM}-tpex.json

    兩者分開寫檔，任一爬蟲失敗不會覆蓋另一份既有資料。
    """
    from crawler.sources.twse_listing import TWSEListingCrawler
    from crawler.sources.tpex_listing import TPExListingCrawler

    logger.info("\n📋 抓取上市（TWSE）+ 上櫃（TPEx）證券清單...")

    month_str = datetime.now().strftime("%Y-%m")
    last_updated = datetime.now().strftime("%Y-%m-%d")

    # 1. TWSE 上市清單
    twse_records = []
    try:
        twse_crawler = TWSEListingCrawler(max_retries=3, delay=2.0)
        twse_records = twse_crawler.fetch()
    except Exception as exc:
        logger.error("❌ TWSE 清單爬蟲失敗: %s", exc)

    if twse_records:
        filepath = DATA_LISTINGS_DIR / f"{month_str}.json"
        output = {
            "last_updated": last_updated,
            "source": "TWSE",
            "records": twse_records,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info(
            "✅ TWSE 清單完成：%d 筆，儲存至 %s",
            len(twse_records), filepath,
        )
    else:
        logger.warning("TWSE 清單無資料（保留既有檔案）")

    # 2. TPEx 上櫃清單
    tpex_records = []
    try:
        tpex_crawler = TPExListingCrawler(max_retries=3, delay=2.0)
        tpex_records = tpex_crawler.fetch()
    except Exception as exc:
        logger.error("❌ TPEx 清單爬蟲失敗: %s", exc)

    if tpex_records:
        filepath = DATA_LISTINGS_DIR / f"{month_str}-tpex.json"
        output = {
            "last_updated": last_updated,
            "source": "TPEx",
            "records": tpex_records,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info(
            "✅ TPEx 清單完成：%d 筆，儲存至 %s",
            len(tpex_records), filepath,
        )
    else:
        logger.warning("TPEx 清單無資料（保留既有檔案）")


# ------------------------------------------------------------------
# 主執行流程
# ------------------------------------------------------------------

def main(year: int | None = None, quarter: int | None = None,
         twt48u_only: bool = False, mops_only: bool = False,
         listing_only: bool = False) -> None:
    """
    主執行流程：
    1. TWT48U — 抓取未來除息預告
    2. MOPS — 抓取配息日資料（個股）
    3. Listing — 抓取上市（TWSE）+ 上櫃（TPEx）證券清單

    Args:
        year: 民國年（None 則自動取得當前年）
        quarter: 季度 1-4（None 則自動取得當前季度）
        twt48u_only: 僅執行 TWT48U
        mops_only: 僅執行 MOPS
        listing_only: 僅執行 Listing
    """
    # 確保目錄存在
    ensure_dirs()

    # 根據參數決定執行哪些爬蟲
    if listing_only:
        # 僅執行 Listing
        fetch_listing()
    elif not mops_only:
        # 1. TWT48U — 除息預告
        fetch_twt48u()

        # 2. Listing — 上市證券清單
        fetch_listing()

    if not twt48u_only and not listing_only:
        # 3. MOPS — 配息日（個股）
        if year is None or quarter is None:
            year, quarter = get_current_year_quarter()
            logger.info("自動偵測: 民國 %d 年第 %d 季", year, quarter)
        else:
            logger.info("指定: 民國 %d 年第 %d 季", year, quarter)

        fetch_mops(year, quarter)

    logger.info("\n" + "=" * 50 + "\n✅ 所有爬蟲完成\n" + "=" * 50)


# ------------------------------------------------------------------
# CLI 入口
# ------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StockPayDay++ 爬蟲")
    parser.add_argument("year", type=int, nargs="?", default=None,
                        help="民國年（如 114）")
    parser.add_argument("quarter", type=int, nargs="?", default=None,
                        help="季度 1-4")
    parser.add_argument("--twt48u", action="store_true",
                        help="僅執行 TWT48U 爬蟲")
    parser.add_argument("--mops", action="store_true",
                        help="僅執行 MOPS 爬蟲")
    parser.add_argument("--listing", action="store_true",
                        help="僅執行 Listing 爬蟲")

    args = parser.parse_args()

    # 驗證參數
    if (args.year is None) != (args.quarter is None):
        parser.error("年份與季度必須同時指定")

    if args.quarter is not None and args.quarter not in (1, 2, 3, 4):
        parser.error("季度必須是 1-4")

    main(
        year=args.year,
        quarter=args.quarter,
        twt48u_only=args.twt48u,
        mops_only=args.mops,
        listing_only=args.listing,
    )
