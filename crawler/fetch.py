"""
StockPayDay++ 主爬蟲腳本
負責協調所有爬蟲模組，抓取配息資料

使用方式：
    python crawler/fetch.py              # 預設只爬取 MoneyDJ（全市場，可取代其他配息來源）
    python crawler/fetch.py --all        # 完整爬取所有來源
    python crawler/fetch.py --twt48u     # 僅執行 TWT48U
    python crawler/fetch.py --mops 114 2 # 僅執行 MOPS（指定年季）
    python crawler/fetch.py --listing    # 僅執行 Listing
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
DATA_MOPS_DIVIDEND_DIR = ROOT_DIR / "data" / "mops_dividend"
DATA_LISTINGS_DIR = ROOT_DIR / "data" / "listings"
DATA_TPEX_ETF_DIR = ROOT_DIR / "data" / "tpex_etf"
DATA_TPEX_EXRIGHT_DIR = ROOT_DIR / "data" / "tpex_exright"
DATA_MONEYDJ_DIR = ROOT_DIR / "data" / "moneydj"


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
    DATA_MOPS_DIVIDEND_DIR.mkdir(parents=True, exist_ok=True)
    DATA_LISTINGS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_TPEX_ETF_DIR.mkdir(parents=True, exist_ok=True)
    DATA_TPEX_EXRIGHT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_MONEYDJ_DIR.mkdir(parents=True, exist_ok=True)
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
# TPEx ETF 配息主流程
# ------------------------------------------------------------------

def save_tpex_etf(records: list, year: int) -> Path:
    """
    儲存 TPEx ETF 配息資料到 data/tpex_etf/{year}.json

    Args:
        records: 配息資料列表
        year: 民國年

    Returns:
        儲存路徑
    """
    filepath = DATA_TPEX_ETF_DIR / f"{year}.json"

    # 讀取舊資料
    old_records: list = []
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            old_records = data.get("records", [])

    # 合併（以 (code, ex_date) 為 key 去重）
    merged = _merge_tpex_etf_records(old_records, records)

    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "records": merged,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("已儲存 %d.json：%d 筆", year, len(merged))
    return filepath


def _merge_tpex_etf_records(old: list, new: list) -> list:
    """
    合併兩筆資料列表，以 (code, ex_date) 為 key 去重
    """
    lookup: dict = {}
    for rec in old:
        key = (rec["code"], rec["ex_date"])
        lookup[key] = rec

    for rec in new:
        key = (rec["code"], rec["ex_date"])
        lookup[key] = rec

    merged = sorted(lookup.values(), key=lambda x: x["ex_date"])
    return merged


def fetch_tpex_etf_dividend() -> None:
    """
    執行 TPEx ETF 配息爬蟲並儲存資料
    """
    from crawler.sources.tpex_etf_dividend import TPExETFDividendCrawler

    logger.info("\n📋 抓取 TPEx ETF 配息資料...")

    crawler = TPExETFDividendCrawler(max_retries=3, delay=2.0)

    try:
        records = crawler.fetch()
    except Exception as exc:
        logger.error("❌ TPEx ETF 爬蟲失敗: %s", exc)
        return

    if not records:
        logger.warning("TPEx ETF 無資料")
        return

    # 取得民國年
    current_year = datetime.now().year - 1911

    # 儲存資料
    saved_path = save_tpex_etf(records, current_year)

    logger.info(
        "✅ TPEx ETF 完成：共 %d 筆，儲存至 %s",
        len(records), saved_path,
    )


# ------------------------------------------------------------------
# TPEx 除權除息計算結果主流程
# ------------------------------------------------------------------
def save_tpex_exright(records: List[Dict]) -> dict[str, Path]:
    """
    儲存 TPEx 除權除息資料到月分檔案

    檔案結構：
    data/tpex_exright/
    └── 2026-08.json    # 8月除權除息

    Args:
        records: 除權除息資料列表

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
        filepath = DATA_TPEX_EXRIGHT_DIR / f"{month}.json"

        # 讀取舊資料
        old_records: List[Dict] = []
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                old_records = data.get("records", [])

        # 合併（以 code + ex_date 為 key 去重）
        merged = _merge_tpex_exright_records(old_records, new_records)

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


def _merge_tpex_exright_records(old: List[Dict], new: List[Dict]) -> List[Dict]:
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


def fetch_tpex_exright_daily() -> None:
    """
    執行 TPEx 除權除息計算結果爬蟲並儲存資料
    """
    from crawler.sources.tpex_exright import TPExExRightCrawler

    logger.info("\n📋 抓取 TPEx 除權除息計算結果資料...")

    crawler = TPExExRightCrawler(max_retries=3, delay=2.0)

    try:
        records = crawler.fetch()
    except Exception as exc:
        logger.error("❌ TPEx 除權除息爬蟲失敗: %s", exc)
        return

    if not records:
        logger.warning("TPEx 除權除息無資料")
        return

    # 依日期分組儲存
    saved_files = save_tpex_exright(records)

    logger.info(
        "✅ TPEx 除權除息完成：共 %d 筆，儲存 %d 個檔案",
        len(records), len(saved_files),
    )


# ------------------------------------------------------------------
# MOPS Dividend 主流程（使用新 API t05st09_2）
# ------------------------------------------------------------------

def save_mops_dividend(records: list, year: int, quarter: int) -> Path:
    """
    儲存 MOPS 配息資料到 data/mops_dividend/{year}Q{quarter}.json

    Args:
        records: 配息資料列表
        year: 民國年
        quarter: 季度

    Returns:
        儲存路徑
    """
    filepath = DATA_MOPS_DIVIDEND_DIR / f"{year}Q{quarter}.json"

    # 讀取舊資料
    old_records: list = []
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            old_records = data.get("records", [])

    # 合併（以 (code, ex_date) 為 key 去重）
    merged = _merge_mops_dividend_records(old_records, records)

    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "year": year,
        "quarter": quarter,
        "records": merged,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("已儲存 %dQ%d.json：%d 筆", year, quarter, len(merged))
    return filepath


def _merge_mops_dividend_records(old: list, new: list) -> list:
    """
    合併兩筆資料列表，以 (code, ex_date) 為 key 去重
    """
    lookup: dict = {}
    for rec in old:
        key = (rec["code"], rec.get("ex_date", ""))
        lookup[key] = rec

    for rec in new:
        key = (rec["code"], rec.get("ex_date", ""))
        lookup[key] = rec

    merged = sorted(lookup.values(), key=lambda x: x.get("ex_date", ""))
    return merged


def fetch_mops_dividend(year: int, quarter: int) -> None:
    """
    執行 MOPS 配息爬蟲（使用新 API t05st09_2）並儲存資料

    從 data/listings/ 讀取股票清單（上市+上櫃），
    逐支查詢配息資料，儲存到 data/mops_dividend/{year}Q{quarter}.json

    Args:
        year: 民國年
        quarter: 季度 1-4
    """
    from crawler.sources.mops_dividend import MOPSDividendCrawler

    logger.info("\n📋 抓取 MOPS 配息資料（新 API t05st09_2）...")

    # 從 listings 讀取股票清單
    codes = _load_stock_codes_from_listings()
    if not codes:
        logger.warning("找不到股票清單，請先執行 fetch_listing()")
        return

    logger.info("📊 共 %d 支股票需要查詢", len(codes))

    # 初始化爬蟲
    crawler = MOPSDividendCrawler(max_retries=3, delay=2.0)

    try:
        records = crawler.fetch_stock_dividends(codes, year, quarter)
    except Exception as exc:
        logger.error("❌ MOPS 配息爬蟲失敗: %s", exc)
        return

    if not records:
        logger.warning("MOPS 配息無資料（可能尚未公告）")
        return

    # 儲存資料
    saved_path = save_mops_dividend(records, year, quarter)

    logger.info(
        "✅ MOPS 配息完成：共 %d 筆，儲存至 %s",
        len(records), saved_path,
    )


def _load_stock_codes_from_listings() -> list:
    """
    從 data/listings/ 讀取所有股票代號（上市+上櫃）

    Returns:
        股票代號列表
    """
    codes = []
    listings_dir = DATA_LISTINGS_DIR

    if not listings_dir.exists():
        return codes

    for json_file in listings_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for record in data.get("records", []):
                code = record.get("code", "")
                if code:
                    codes.append(code)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)

    # 去重
    codes = list(set(codes))
    codes.sort()

    logger.info("從 listings 讀取 %d 支股票代號", len(codes))
    return codes


# ------------------------------------------------------------------
# MoneyDJ 除權除息主流程
# ------------------------------------------------------------------

def save_moneydj(records: list) -> dict[str, Path]:
    """
    儲存 MoneyDJ 除權除息資料到 data/moneydj/{YYYY-MM}.json

    比照 data/twses/ 的格式：依除權除息日（ex_date）分月儲存。
    每筆紀錄含 twses 欄位（code, name, ex_date, type,
    cash_dividend, stock_dividend），並擴充 MoneyDJ 明細欄位
    （earnings_dividend, reserve_dividend, pay_date,
    earnings_stock, reserve_stock）。

    同日除息+除權 → 一筆 type=權息；不同日 → 拆成兩筆（息、權）。

    Args:
        records: 除權除息資料列表

    Returns:
        {月份: 檔案路徑} 字典
    """
    saved_files: Dict[str, Path] = {}

    # 拆分成事件級紀錄（除息 / 除權）
    event_records = _split_moneydj_events(records)

    # 依月份分組
    by_month: Dict[str, List[Dict]] = {}
    for rec in event_records:
        month = rec["ex_date"][:7]  # "2026-08"
        by_month.setdefault(month, []).append(rec)

    # 合併到各月檔案
    for month, new_records in by_month.items():
        filepath = DATA_MONEYDJ_DIR / f"{month}.json"

        # 讀取舊資料
        old_records: List[Dict] = []
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                old_records = data.get("records", [])

        # 合併（以 code + ex_date + type 為 key 去重，並把同日 息+權 併成權息）
        merged = _merge_moneydj_records(old_records, new_records)

        # 寫入
        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "source": "moneydj",
            "records": merged,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        saved_files[month] = filepath
        logger.info("已儲存 moneydj/%s.json：%d 筆", month, len(merged))

    return saved_files


def _split_moneydj_events(records: list) -> List[Dict]:
    """
    將 MoneyDJ 一列多事件（除息+除權）拆成事件級紀錄

    - 僅除息 → type=息（含現金股利明細）
    - 僅除權 → type=權（含股票股利明細）
    - 同日除息+除權 → type=權息（一筆）
    - 不同日除息+除權 → 拆成息、權兩筆

    Args:
        records: MoneyDJ 爬蟲原始紀錄（每支股票一筆）

    Returns:
        事件級紀錄列表
    """
    events: List[Dict] = []

    for rec in records:
        ex_date = rec.get("ex_date", "")
        ex_rights_date = rec.get("ex_rights_date", "")
        code = rec["code"]
        name = rec["name"]

        base = {
            "code": code,
            "name": name,
            "earnings_dividend": rec.get("earnings_dividend", 0),
            "reserve_dividend": rec.get("reserve_dividend", 0),
            "cash_dividend": rec.get("cash_dividend", 0),
            "pay_date": rec.get("pay_date", ""),
            "earnings_stock": rec.get("earnings_stock", 0),
            "reserve_stock": rec.get("reserve_stock", 0),
            "stock_dividend": rec.get("stock_dividend", 0),
        }

        if ex_date and ex_rights_date:
            if ex_date == ex_rights_date:
                # 同日除息+除權 → 一筆權息
                events.append({**base, "ex_date": ex_date, "type": "權息"})
            else:
                # 不同日 → 拆兩筆：除息、除權
                events.append({
                    **base,
                    "ex_date": ex_date,
                    "type": "息",
                    "earnings_stock": 0,
                    "reserve_stock": 0,
                    "stock_dividend": 0,
                })
                events.append({
                    "code": code,
                    "name": name,
                    "ex_date": ex_rights_date,
                    "type": "權",
                    "earnings_dividend": 0,
                    "reserve_dividend": 0,
                    "cash_dividend": 0,
                    "pay_date": "",
                    "earnings_stock": rec.get("earnings_stock", 0),
                    "reserve_stock": rec.get("reserve_stock", 0),
                    "stock_dividend": rec.get("stock_dividend", 0),
                })
        elif ex_date:
            # 僅除息
            events.append({**base, "ex_date": ex_date, "type": "息"})
        elif ex_rights_date:
            # 僅除權
            events.append({
                "code": code,
                "name": name,
                "ex_date": ex_rights_date,
                "type": "權",
                "earnings_dividend": 0,
                "reserve_dividend": 0,
                "cash_dividend": 0,
                "pay_date": "",
                "earnings_stock": rec.get("earnings_stock", 0),
                "reserve_stock": rec.get("reserve_stock", 0),
                "stock_dividend": rec.get("stock_dividend", 0),
            })

    return events


def _merge_moneydj_records(old: list, new: list) -> list:
    """
    合併兩筆資料列表，以 (code, ex_date, type) 為 key 去重，
    並將同日的 息+權 事件合併為單筆「權息」。

    Args:
        old: 舊資料
        new: 新資料

    Returns:
        合併後的資料列表
    """
    lookup: dict = {}
    for rec in old:
        key = (rec["code"], rec["ex_date"], rec.get("type", "息"))
        lookup[key] = rec

    for rec in new:
        key = (rec["code"], rec["ex_date"], rec.get("type", "息"))
        lookup[key] = rec

    # 同日 息+權 → 單筆權息（也一併修正舊檔案中的殘留資料）
    merged = _merge_same_day_dividend_events(list(lookup.values()))

    # 排序（依 ex_date，同日期再依 code）
    merged = sorted(merged, key=lambda x: (x["ex_date"], x["code"]))
    return merged


def _merge_same_day_dividend_events(records: list) -> list:
    """
    將同一 (code, ex_date) 的多筆事件合併為單筆「權息」

    背景：MoneyDJ 頁面有時會以兩列呈現同日的除息、除權
    （一列僅有除息日、另一列僅有除權日），經 _split_moneydj_events
    會被拆成兩筆事件（type=息、type=權）。此函式把它們合併回一筆 權息：
    現金股利取自 息、股票股利取自 權、pay_date 取自 息。

    規則（同一 code + ex_date）：
    - 已有 權息 → 保留 權息，其餘（部分重複的 息/權）捨棄
    - 僅有 息 + 權 → 合併為一筆 權息
    - 其他組合 → 原樣保留

    Args:
        records: 事件紀錄列表（已依 code + ex_date + type 去重）

    Returns:
        合併後的紀錄列表
    """
    # 依 (code, ex_date) 分組
    by_date: Dict[tuple, List[Dict]] = {}
    for rec in records:
        by_date.setdefault((rec["code"], rec.get("ex_date", "")), []).append(rec)

    merged: List[Dict] = []
    for group in by_date.values():
        types = {r.get("type") for r in group}

        # 已有完整的權息 → 保留權息即可
        if "權息" in types:
            merged.append(
                next(r for r in group if r.get("type") == "權息")
            )
            continue

        # 同日的 息 + 權 → 合併為權息
        if "息" in types and "權" in types:
            combined: Dict = {"type": "權息"}
            for r in group:
                if r.get("type") == "息":
                    combined.update({
                        "code": r["code"],
                        "name": r["name"],
                        "ex_date": r["ex_date"],
                        "earnings_dividend": r.get("earnings_dividend", 0),
                        "reserve_dividend": r.get("reserve_dividend", 0),
                        "cash_dividend": r.get("cash_dividend", 0),
                        "pay_date": r.get("pay_date", ""),
                    })
                elif r.get("type") == "權":
                    combined.update({
                        "code": r["code"],
                        "name": r["name"],
                        "ex_date": r["ex_date"],
                        "earnings_stock": r.get("earnings_stock", 0),
                        "reserve_stock": r.get("reserve_stock", 0),
                        "stock_dividend": r.get("stock_dividend", 0),
                    })
            merged.append(combined)
            continue

        # 其餘組合 → 原樣保留
        merged.extend(group)

    return merged


def fetch_moneydj_exright() -> None:
    """
    執行 MoneyDJ 除權除息爬蟲並儲存資料
    """
    from crawler.sources.moneydj_exright import MoneyDJExRightCrawler

    logger.info("\n📋 抓取 MoneyDJ 除權除息資料...")

    crawler = MoneyDJExRightCrawler(max_retries=3, delay=2.0)

    try:
        records = crawler.fetch()
    except Exception as exc:
        logger.error("❌ MoneyDJ 爬蟲失敗: %s", exc)
        return

    if not records:
        logger.warning("MoneyDJ 除權除息無資料")
        return

    # 依日期分組儲存
    saved_files = save_moneydj(records)

    logger.info(
        "✅ MoneyDJ 除權除息完成：共 %d 筆，儲存 %d 個月份檔案",
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
         listing_only: bool = False, all_sources: bool = False) -> None:
    """
    主執行流程

    預設只爬取 MoneyDJ 除權除息：MoneyDJ 除權除息表涵蓋全市場
    （上市 + 上櫃 + ETF），且含現金/股票股利與 pay_date，
    可取代 TWT48U / MOPS / TPEx ETF / TPEx 除權除息等配息來源。

    需要完整爬取時請指定 all_sources=True：
    1. TWT48U — 抓取未來除息預告
    2. TPEx ETF — 抓取上櫃 ETF 配息
    3. TPEx 除權除息 — 上櫃除權除息計算結果
    4. MoneyDJ — 全市場除權除息表
    5. MOPS Dividend — 配息日資料（使用新 API t05st09_2）
    6. Listing — 抓取上市（TWSE）+ 上櫃（TPEx）證券清單

    Args:
        year: 民國年（None 則自動取得當前年）
        quarter: 季度 1-4（None 則自動取得當前季度）
        twt48u_only: 僅執行 TWT48U
        mops_only: 僅執行 MOPS
        listing_only: 僅執行 Listing
        all_sources: 完整爬取所有來源（原預設行為）
    """
    # 確保目錄存在
    ensure_dirs()

    if all_sources:
        # 完整爬取（原預設行為）
        fetch_twt48u()
        fetch_tpex_etf_dividend()
        fetch_tpex_exright_daily()
        fetch_moneydj_exright()
        fetch_listing()
        if year is None or quarter is None:
            year, quarter = get_current_year_quarter()
            logger.info("自動偵測: 民國 %d 年第 %d 季", year, quarter)
        else:
            logger.info("指定: 民國 %d 年第 %d 季", year, quarter)
        fetch_mops_dividend(year, quarter)
    elif listing_only:
        # 僅執行 Listing
        fetch_listing()
    elif twt48u_only:
        # 僅執行 TWT48U
        fetch_twt48u()
    elif mops_only:
        # 僅執行 MOPS
        if year is None or quarter is None:
            year, quarter = get_current_year_quarter()
            logger.info("自動偵測: 民國 %d 年第 %d 季", year, quarter)
        else:
            logger.info("指定: 民國 %d 年第 %d 季", year, quarter)
        fetch_mops_dividend(year, quarter)
    else:
        # 預設：只爬 MoneyDJ（可取代其他配息來源）
        fetch_moneydj_exright()

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
    parser.add_argument("--all", action="store_true",
                        help="完整爬取所有來源（TWT48U + TPEx + MoneyDJ + MOPS + Listing）")
    parser.add_argument("--twt48u", action="store_true",
                        help="僅執行 TWT48U 爬蟲")
    parser.add_argument("--mops", action="store_true",
                        help="僅執行 MOPS 配息爬蟲（新 API t05st09_2）")
    parser.add_argument("--listing", action="store_true",
                        help="僅執行 Listing 爬蟲")
    parser.add_argument("--tpex-etf", action="store_true",
                        help="僅執行 TPEx ETF 爬蟲")
    parser.add_argument("--moneydj", action="store_true",
                        help="僅執行 MoneyDJ 除權除息爬蟲（預設）")

    args = parser.parse_args()

    # 驗證參數
    if (args.year is None) != (args.quarter is None):
        parser.error("年份與季度必須同時指定")

    if args.quarter is not None and args.quarter not in (1, 2, 3, 4):
        parser.error("季度必須是 1-4")

    if args.tpex_etf:
        ensure_dirs()
        fetch_tpex_etf_dividend()
    elif args.moneydj:
        ensure_dirs()
        fetch_moneydj_exright()
    else:
        main(
            year=args.year,
            quarter=args.quarter,
            twt48u_only=args.twt48u,
            mops_only=args.mops,
            listing_only=args.listing,
            all_sources=args.all,
        )
