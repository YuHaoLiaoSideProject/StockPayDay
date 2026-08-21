"""
StockPayDay++ 主爬蟲腳本
負責協調所有爬蟲模組，抓取 TWSE 配息資料

使用方式：
    python crawler/fetch.py              # 自動使用當前年季
    python crawler/fetch.py 114 2        # 指定民國年 114 Q2
"""

import sys
import json
import logging
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


# ------------------------------------------------------------------
# 目錄管理
# ------------------------------------------------------------------

def ensure_dirs() -> None:
    """確保資料目錄存在（含 etfs、preferred）"""
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "stocks").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "etfs").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "preferred").mkdir(parents=True, exist_ok=True)
    logger.info("資料目錄已確認: %s", DATA_DIR)


# ------------------------------------------------------------------
# 資料儲存
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
# 主流程
# ------------------------------------------------------------------

def main(year: int | None = None, quarter: int | None = None) -> None:
    """
    主執行流程：呼叫 twse_stock.py 抓取並儲存個股配息資料。

    Args:
        year: 民國年（None 則自動取得當前年）
        quarter: 季度 1-4（None 則自動取得當前季度）
    """
    from crawler.sources.twse_stock import TWSEStockCrawler

    # 確定年季
    if year is None or quarter is None:
        year, quarter = get_current_year_quarter()
        logger.info("自動偵測: 民國 %d 年第 %d 季", year, quarter)
    else:
        logger.info("指定: 民國 %d 年第 %d 季", year, quarter)

    # 確保目錄存在
    ensure_dirs()

    # 初始化爬蟲
    crawler = TWSEStockCrawler(max_retries=3, delay=2.0)

    # 抓取資料
    logger.info("🕷️ 開始抓取配息資料...")
    raw_data, stocks = crawler.fetch_stock_dividends(year, quarter)

    if not raw_data:
        logger.warning("本次抓取無資料（可能尚未公告或 API 回傳空表格）")
        return

    # 儲存原始資料
    raw_filename = f"twse_dividend_{year}Q{quarter}"
    save_raw(raw_data, raw_filename)

    # 儲存個股基底資料
    saved_count = 0
    for stock in stocks:
        try:
            save_stock(stock, "stocks")
            saved_count += 1
        except Exception as exc:
            logger.error("儲存個股 %s 失敗: %s", stock.get("code", "?"), exc)

    logger.info(
        "✅ 個股完成：共儲存 %d 支（原始 %d 筆）",
        saved_count, len(raw_data),
    )

    # ------------------------------------------------------------------
    # 2. 抓取 ETF
    # ------------------------------------------------------------------
    etfs_saved = 0
    etfs_raw_count = 0
    try:
        from crawler.sources.twse_etf import TWSEETFCrawler

        logger.info("\n📋 抓取 ETF 資料...")
        etf_crawler = TWSEETFCrawler(max_retries=3, delay=2.0)
        etf_raw, etfs = etf_crawler.fetch_etf_dividends(year, quarter)

        etfs_raw_count = len(etf_raw)
        if etf_raw:
            etf_raw_filename = f"twse_etf_dividend_{year}Q{quarter}"
            save_raw(etf_raw, etf_raw_filename)

        for etf in etfs:
            try:
                save_stock(etf, "etfs")
                etfs_saved += 1
            except Exception as exc:
                logger.error("儲存 ETF %s 失敗: %s", etf.get("code", "?"), exc)

        logger.info("✅ ETF 完成：共儲存 %d 支（原始 %d 筆）", etfs_saved, etfs_raw_count)
    except Exception as exc:
        logger.error("❌ ETF 爬蟲失敗: %s", exc)

    # ------------------------------------------------------------------
    # 3. 抓取特別股
    # ------------------------------------------------------------------
    preferred_saved = 0
    preferred_raw_count = 0
    try:
        from crawler.sources.twse_preferred import TWSEPreferredCrawler

        logger.info("\n📋 抓取特別股資料...")
        pref_crawler = TWSEPreferredCrawler(max_retries=3, delay=2.0)
        pref_raw, preferred = pref_crawler.fetch_preferred_dividends(year, quarter)

        preferred_raw_count = len(pref_raw)
        if pref_raw:
            pref_raw_filename = f"twse_preferred_dividend_{year}Q{quarter}"
            save_raw(pref_raw, pref_raw_filename)

        for pref in preferred:
            try:
                save_stock(pref, "preferred")
                preferred_saved += 1
            except Exception as exc:
                logger.error("儲存特別股 %s 失敗: %s", pref.get("code", "?"), exc)

        logger.info(
            "✅ 特別股完成：共儲存 %d 支（原始 %d 筆）",
            preferred_saved, preferred_raw_count,
        )
    except Exception as exc:
        logger.error("❌ 特別股爬蟲失敗: %s", exc)

    # ------------------------------------------------------------------
    # 4. 總計
    # ------------------------------------------------------------------
    total = saved_count + etfs_saved + preferred_saved
    logger.info(
        "\n" + "=" * 50
        + "\n📊 爬蟲完成總計"
        + f"\n   個股：{saved_count} 支"
        + f"\n   ETF：{etfs_saved} 支"
        + f"\n   特別股：{preferred_saved} 支"
        + f"\n   總計：{total} 支"
        + "\n" + "=" * 50
    )


# ------------------------------------------------------------------
# CLI 入口
# ------------------------------------------------------------------

if __name__ == "__main__":
    yr: int | None = None
    qtr: int | None = None

    if len(sys.argv) >= 2:
        try:
            yr = int(sys.argv[1])
        except ValueError:
            print(f"錯誤：年份必須是整數，收到 '{sys.argv[1]}'")
            sys.exit(1)

    if len(sys.argv) >= 3:
        try:
            qtr = int(sys.argv[2])
            if qtr not in (1, 2, 3, 4):
                raise ValueError
        except ValueError:
            print(f"錯誤：季度必須是 1-4，收到 '{sys.argv[2]}'")
            sys.exit(1)

    main(year=yr, quarter=qtr)
