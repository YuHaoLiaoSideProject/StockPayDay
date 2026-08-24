"""
資料處理器 — 將 data/ 基底資料轉換為 api/ 前端用 JSON

職責：
1. 讀取配息公告來源（可切換，預設 data/moneydj/*.json）：
   - moneydj     MoneyDJ 除權除息（預設）
   - twses-mops  TWT48U + MOPS + TPEx ETF（原組合邏輯）
   - twses       TWT48U 除息預告
   - mops        MOPS 配息（新 API t05st09_2）
   - tpex-etf    TPEx ETF 配息
   - mops-legacy MOPS 配息日（舊格式，供 reference）
2. 讀取 data/{stocks,etfs,preferred}/*.json（各證券完整配息歷史）
3. 讀取 data/listings/*.json（證券清單）
4. 產生 frontend/public/api/dividends/YYYY-MM.json（月份配息）
5. 產生 frontend/public/api/securities-index.json（證券清單）
6. 產生 frontend/public/api/securities/{code}.json（單股歷史）

使用方式：
    python processor/generate_api.py                       # 預設來源 moneydj
    python processor/generate_api.py --source twses-mops   # 切換來源
    python processor/generate_api.py --list-sources        # 列出可用來源
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Dict, Optional

logger = logging.getLogger(__name__)

# 專案路徑
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
API_DIR = ROOT_DIR / "frontend" / "public" / "api"

# 證券基底資料子目錄（phase-3 規格）
DATA_SUBDIRS = ["stocks", "etfs", "preferred"]

# 配息公告來源子目錄：
#   moneydj      data/moneydj/（MoneyDJ 除權除息，預設來源）
#   twses        data/twses/（TWT48U 除息預告）
#   mops         data/mops_dividend/（MOPS 配息，新 API t05st09_2）
#   tpex_etf     data/tpex_etf/（TPEx ETF 配息）
#   mops-legacy  data/mops/（MOPS 配息日，舊格式，供 reference）
# 各 loader 在呼叫時以 DATA_DIR 動態組出路徑，便於測試替換 DATA_DIR。




# ------------------------------------------------------------------
# 資料讀取
# ------------------------------------------------------------------

def load_twses() -> List[Dict]:
    """
    從 data/twses/ 讀取 TWT48U 除息預告資料

    檔案格式：
    {
        "last_updated": "2026-08-21",
        "records": [
            {
                "code": "2330",
                "name": "台積電",
                "ex_date": "2026-07-25",
                "type": "息",
                "cash_dividend": 3.5,
                "stock_dividend": 0.0
            }
        ]
    }

    Returns:
        所有除息預告紀錄列表
    """
    records = []
    twses_dir = DATA_DIR / "twses"
    if not twses_dir.exists():
        logger.warning("TWT48U 資料目錄不存在: %s", twses_dir)
        return records

    for json_file in sorted(twses_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_records = data.get("records", [])
            records.extend(file_records)
            logger.debug("讀取 %s: %d 筆", json_file.name, len(file_records))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)

    logger.info("TWT48U 共讀取 %d 筆紀錄", len(records))
    return records


def load_mops() -> List[Dict]:
    """
    從 data/mops/ 讀取 MOPS 配息日資料（舊 API，保留供 reference）

    檔案格式（預期）：
    {
        "year": 114,
        "quarter": 2,
        "records": [
            {
                "code": "2330",
                "name": "台積電",
                "ex_date": "2026-07-25",
                "pay_date": "2026-08-15",
                "cash_dividend": 3.5
            }
        ]
    }

    Returns:
        所有配息日紀錄列表
    """
    records = []
    mops_dir = DATA_DIR / "mops"
    if not mops_dir.exists():
        logger.warning("MOPS 資料目錄不存在: %s", mops_dir)
        return records

    for json_file in sorted(mops_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_records = data.get("records", [])
            records.extend(file_records)
            logger.debug("讀取 %s: %d 筆", json_file.name, len(file_records))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)

    logger.info("MOPS 共讀取 %d 筆紀錄", len(records))
    return records


def load_mops_dividend() -> List[Dict]:
    """
    從 data/mops_dividend/ 讀取 MOPS 配息資料（新 API t05st09_2）

    檔案格式：
    {
        "last_updated": "2026-08-23",
        "year": 114,
        "quarter": 2,
        "records": [
            {
                "code": "2330",
                "name": "台積電",
                "ex_date": "2025-07-25",
                "pay_date": "2025-08-15",
                "cash_dividend": 3.5,
                "stock_dividend": 0.0,
                "source": "MOPS"
            }
        ]
    }

    Returns:
        所有配息紀錄列表
    """
    records = []
    mops_dir = DATA_DIR / "mops_dividend"
    if not mops_dir.exists():
        logger.warning("MOPS 配息資料目錄不存在: %s", mops_dir)
        return records

    for json_file in sorted(mops_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_records = data.get("records", [])
            records.extend(file_records)
            logger.debug("讀取 %s: %d 筆", json_file.name, len(file_records))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)

    logger.info("MOPS 配息共讀取 %d 筆紀錄", len(records))
    return records


def load_tpex_etf() -> List[Dict]:
    """
    從 data/tpex_etf/ 讀取 TPEx ETF 配息資料

    檔案格式：
    {
        "last_updated": "2026-08-22",
        "records": [
            {
                "code": "00694B",
                "name": "富邦美債1-3",
                "ex_date": "2026-07-16",
                "pay_date": "2026-08-10",
                "cash_dividend": 0.317,
                "stock_dividend": 0.0,
                "source": "TPEx"
            }
        ]
    }

    Returns:
        所有 TPEx ETF 配息紀錄列表
    """
    records = []
    tpex_dir = DATA_DIR / "tpex_etf"
    if not tpex_dir.exists():
        logger.warning("TPEx ETF 資料目錄不存在: %s", tpex_dir)
        return records

    for json_file in sorted(tpex_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_records = data.get("records", [])
            records.extend(file_records)
            logger.debug("讀取 %s: %d 筆", json_file.name, len(file_records))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)

    logger.info("TPEx ETF 共讀取 %d 筆紀錄", len(records))
    return records


def load_moneydj() -> List[Dict]:
    """
    從 data/moneydj/ 讀取 MoneyDJ 除權除息資料

    檔案格式（crawler/fetch.py save_moneydj 依月份寫入）：
    {
        "last_updated": "2026-08-23",
        "source": "moneydj",
        "records": [
            {
                "code": "00679B",
                "name": "元大美債20年",
                "ex_date": "2026-08-21",
                "type": "息",
                "pay_date": "2026-09-11",
                "cash_dividend": 0.28,
                "stock_dividend": 0.0,
                "earnings_dividend": 0.28,
                "reserve_dividend": 0.0,
                "earnings_stock": 0.0,
                "reserve_stock": 0.0
            }
        ]
    }

    跨月份以 (code, ex_date, type) 去重（與 crawler 合併用的 key 一致）。

    Returns:
        所有 MoneyDJ 除權除息紀錄列表
    """
    records = []
    moneydj_dir = DATA_DIR / "moneydj"
    if not moneydj_dir.exists():
        logger.warning("MoneyDJ 資料目錄不存在: %s", moneydj_dir)
        return records

    seen = set()
    for json_file in sorted(moneydj_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)
            continue

        file_records = data.get("records", [])
        for rec in file_records:
            key = (rec.get("code", ""), rec.get("ex_date", ""),
                   rec.get("type", "息"))
            if key in seen:
                logger.debug("跳過重複紀錄: %s", key)
                continue
            seen.add(key)
            records.append(rec)
        logger.debug("讀取 %s: %d 筆", json_file.name, len(file_records))

    logger.info("MoneyDJ 共讀取 %d 筆紀錄", len(records))
    return records


def merge_twses_and_mops(twses: List[Dict], mops: List[Dict]) -> List[Dict]:
    """
    合併 TWT48U 和 MOPS 資料

    TWT48U 有：code, name, ex_date, type, cash_dividend, stock_dividend
    MOPS 有：code, name, ex_date, pay_date, cash_dividend

    合併邏輯：
    - 以 (code, ex_date) 為 key
    - TWT48U 為主體，MOPS 補充 pay_date

    Args:
        twses: TWT48U 紀錄列表
        mops: MOPS 紀錄列表

    Returns:
        合併後的紀錄列表
    """
    # 建立 TWT48U lookup
    lookup: Dict[tuple, Dict] = {}
    for rec in twses:
        key = (rec["code"], rec["ex_date"])
        lookup[key] = rec

    # 用 MOPS 資料補充 pay_date
    for rec in mops:
        key = (rec["code"], rec.get("ex_date", ""))
        if key in lookup:
            lookup[key]["pay_date"] = rec.get("pay_date", "")

    return list(lookup.values())


def load_securities() -> List[Dict]:
    """
    從 data/{stocks,etfs,preferred}/ 讀取證券基底資料，
    並將每支證券的 dividend_history 攤平為紀錄列表。

    檔案格式（crawler/fetch.py save_stock 寫入）：
    {
        "code": "2330",
        "name": "台積電",
        "type": "stock",
        "dividend_history": [
            {"year": 2026, "quarter": 2, "ex_date": "2026-07-25",
             "pay_date": "2026-08-15", "cash_dividend": 3.5,
             "stock_dividend": 0.0}
        ]
    }

    Returns:
        攤平後的紀錄列表（code, name, type, ex_date, pay_date,
        cash_dividend, stock_dividend）
    """
    records: List[Dict] = []
    for subdir in DATA_SUBDIRS:
        dir_path = DATA_DIR / subdir
        if not dir_path.exists():
            continue

        for json_file in sorted(dir_path.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)
                continue

            code = data.get("code", json_file.stem)
            name = data.get("name", "")
            sec_type = data.get("type", "stock")
            for h in data.get("dividend_history", []):
                records.append({
                    "code": code,
                    "name": name,
                    "type": sec_type,
                    "ex_date": h.get("ex_date", ""),
                    "pay_date": h.get("pay_date", ""),
                    "cash_dividend": h.get("cash_dividend", 0),
                    "stock_dividend": h.get("stock_dividend", 0),
                })

    logger.info("基底證券共讀取 %d 筆紀錄", len(records))
    return records


def merge_securities_and_announcements(
    securities: List[Dict], announcements: List[Dict],
) -> List[Dict]:
    """
    合併基底證券歷史與最新公告（TWT48U + MOPS）紀錄。

    以 (code, ex_date) 為 key 去重：
    - 基底證券歷史為主體（保留 type 為 stock/etf/preferred）
    - 公告紀錄補充/更新 pay_date 與配息金額
    - 僅存在於公告的 (code, ex_date) 直接納入

    Args:
        securities: load_securities() 回傳的攤平紀錄
        announcements: merge_twses_and_mops() 回傳的公告紀錄

    Returns:
        合併後的紀錄列表
    """
    lookup: Dict[tuple, Dict] = {}

    for rec in securities:
        ex_date = rec.get("ex_date", "")
        if not ex_date:
            continue
        lookup[(rec["code"], ex_date)] = rec

    for rec in announcements:
        ex_date = rec.get("ex_date", "")
        if not ex_date:
            continue
        key = (rec["code"], ex_date)
        if key in lookup:
            base = lookup[key]
            if rec.get("pay_date"):
                base["pay_date"] = rec["pay_date"]
            base["cash_dividend"] = rec.get(
                "cash_dividend", base.get("cash_dividend", 0))
            base["stock_dividend"] = rec.get(
                "stock_dividend", base.get("stock_dividend", 0))
        else:
            lookup[key] = rec

    return list(lookup.values())


# ------------------------------------------------------------------
# 資料來源切換（可插拔來源）
# ------------------------------------------------------------------

@dataclass
class DataSource:
    """
    資料來源定義

    每個來源只需提供「讀取配息公告紀錄」的 build_announcements，
    下游處理（合併基底歷史、產生 upcoming / index / history）共用同一套。
    新增來源 = 在 SOURCE_REGISTRY 註冊一筆。
    """
    name: str
    label: str
    description: str
    build_announcements: Callable[[], List[Dict]]


def _build_moneydj_announcements() -> List[Dict]:
    """MoneyDJ 除權除息（data/moneydj/*.json）"""
    return load_moneydj()


def _build_twses_mops_announcements() -> List[Dict]:
    """
    原組合邏輯：TWT48U 為主體，MOPS（新 API）補充 pay_date，
    再併入 TPEx ETF。
    """
    twses = load_twses()
    mops = load_mops_dividend()
    tpex_etf = load_tpex_etf()
    announcements = merge_twses_and_mops(twses, mops)
    announcements.extend(tpex_etf)
    return announcements


def _build_twses_announcements() -> List[Dict]:
    """TWT48U 除息預告（data/twses/*.json）"""
    return load_twses()


def _build_mops_announcements() -> List[Dict]:
    """MOPS 配息（新 API t05st09_2，data/mops_dividend/*.json）"""
    return load_mops_dividend()


def _build_tpex_etf_announcements() -> List[Dict]:
    """TPEx ETF 配息（data/tpex_etf/*.json）"""
    return load_tpex_etf()


def _build_mops_legacy_announcements() -> List[Dict]:
    """MOPS 配息日（舊格式，data/mops/*.json，保留供 reference）"""
    return load_mops()


SOURCE_REGISTRY: Dict[str, DataSource] = {
    "moneydj": DataSource(
        name="moneydj",
        label="MoneyDJ 除權除息",
        description="data/moneydj/*.json（含 pay_date 與 現金/股票股利）",
        build_announcements=_build_moneydj_announcements,
    ),
    "twses-mops": DataSource(
        name="twses-mops",
        label="TWT48U + MOPS + TPEx ETF",
        description="原組合邏輯：TWT48U 為主體，MOPS 補 pay_date，併入 TPEx ETF",
        build_announcements=_build_twses_mops_announcements,
    ),
    "twses": DataSource(
        name="twses",
        label="TWT48U 除息預告",
        description="data/twses/*.json（無 pay_date）",
        build_announcements=_build_twses_announcements,
    ),
    "mops": DataSource(
        name="mops",
        label="MOPS 配息（新 API）",
        description="data/mops_dividend/*.json（含 pay_date）",
        build_announcements=_build_mops_announcements,
    ),
    "tpex-etf": DataSource(
        name="tpex-etf",
        label="TPEx ETF 配息",
        description="data/tpex_etf/*.json（含 pay_date）",
        build_announcements=_build_tpex_etf_announcements,
    ),
    "mops-legacy": DataSource(
        name="mops-legacy",
        label="MOPS 配息日（舊格式）",
        description="data/mops/*.json（供 reference）",
        build_announcements=_build_mops_legacy_announcements,
    ),
}

# 預設資料來源
DEFAULT_SOURCE = "moneydj"


def get_source(name: str) -> DataSource:
    """
    依名稱取得資料來源，未知名稱拋出 ValueError

    Args:
        name: 來源名稱（SOURCE_REGISTRY 的 key）

    Returns:
        對應的 DataSource

    Raises:
        ValueError: 名稱不在 SOURCE_REGISTRY 中
    """
    if name not in SOURCE_REGISTRY:
        available = ", ".join(sorted(SOURCE_REGISTRY))
        raise ValueError(f"未知資料來源: {name}（可用: {available}）")
    return SOURCE_REGISTRY[name]


def list_sources() -> None:
    """印出所有可用資料來源"""
    print("可用資料來源：")
    for name in sorted(SOURCE_REGISTRY):
        src = SOURCE_REGISTRY[name]
        default = "（預設）" if name == DEFAULT_SOURCE else ""
        print(f"  - {name:<12} {src.label}{default}")
        print(f"      {src.description}")


def build_records(source: DataSource) -> List[Dict]:
    """
    依指定來源讀取並合併配息紀錄

    流程（與原邏輯一致）：
    1. 讀取基底證券歷史（data/{stocks,etfs,preferred}）
    2. 讀取指定來源的公告紀錄
    3. 以 (code, ex_date) 合併（基底為主體，公告更新/補充 pay_date 與金額）

    Args:
        source: 資料來源

    Returns:
        合併後的紀錄列表（可直接餵給 generate_* 系列）
    """
    securities = load_securities()
    announcements = source.build_announcements()
    records = merge_securities_and_announcements(securities, announcements)
    return records


# ------------------------------------------------------------------
# API 產生
# ------------------------------------------------------------------

def generate_upcoming(records: List[Dict], today: Optional[str] = None) -> List[Dict]:
    """
    篩選未來配息，產生 upcoming 清單

    業務規則：
    - ex_date >= today（今天或未來）才納入
    - 依 ex_date 升冪排序

    Args:
        records: 合併後的紀錄列表
        today: 用於測試覆蓋，預設為 datetime.now().strftime("%Y-%m-%d")

    Returns:
        upcoming 配息列表（已排序）
    """
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")

    upcoming = []
    for rec in records:
        ex_date = rec.get("ex_date", "")
        if ex_date >= today:
            upcoming.append({
                "code": rec["code"],
                "name": rec["name"],
                "type": rec.get("type", "息"),
                "ex_date": ex_date,
                "pay_date": rec.get("pay_date", ""),
                "cash_dividend": rec.get("cash_dividend", 0),
                "stock_dividend": rec.get("stock_dividend", 0),
            })

    # 依 ex_date 升冪排序
    upcoming.sort(key=lambda x: x["ex_date"])
    return upcoming


def load_listings() -> List[Dict]:
    """
    從 data/listings/ 讀取證券完整清單

    檔案格式：
    {
        "last_updated": "2026-08-22",
        "source": "TWSE",
        "records": [
            {"code": "1101", "name": "台泥", "market": "TWSE"},
            ...
        ]
    }

    Returns:
        所有證券清單紀錄列表
    """
    listings = []
    listings_dir = DATA_DIR / "listings"
    if not listings_dir.exists():
        logger.warning("證券清單目錄不存在: %s", listings_dir)
        return listings

    for json_file in sorted(listings_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_records = data.get("records", [])
            listings.extend(file_records)
            logger.debug("讀取 %s: %d 筆", json_file.name, len(file_records))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("跳過無法讀取的檔案 %s: %s", json_file.name, exc)

    logger.info("證券清單共讀取 %d 筆", len(listings))
    return listings


def generate_securities_index(
    records: List[Dict],
    listings: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    產生證券清單索引（去重）

    合併邏輯：
    1. 從配息紀錄建立索引（以此為主，名稱可能更準確）
    2. 從 listings 補充尚未在索引中的股票
    3. 去重後輸出

    Args:
        records: 合併後的紀錄列表
        listings: 證券清單（可選）

    Returns:
        證券索引列表（已去重）
    """
    # 從配息紀錄建立索引（以此為主）
    seen = set()
    index = []
    for rec in records:
        code = rec["code"]
        if code not in seen:
            seen.add(code)
            index.append({
                "code": code,
                "name": rec["name"],
            })

    # 從 listings 補充尚未在索引中的股票
    if listings:
        for rec in listings:
            code = rec.get("code", "")
            if code and code not in seen:
                seen.add(code)
                index.append({
                    "code": code,
                    "name": rec.get("name", ""),
                })

    # 排序（依代號）
    index.sort(key=lambda x: x["code"])
    return index


def generate_securities_history(
    records: List[Dict],
    output_dir: Optional[Path] = None,
    listings: Optional[List[Dict]] = None,
) -> int:
    """
    產出每支證券的歷史配息檔案

    每支證券一個 JSON 檔案：
    api/securities/{code}.json

    檔案格式：
    {
        "code": "2330",
        "name": "台積電",
        "history": [
            {"year": 2026, "ex_date": "2026-07-25", "cash_dividend": 3.5, "stock_dividend": 0},
            ...
        ]
    }

    僅存在於 listings（證券清單）而無配息紀錄的證券，
    也會產出 history 為空陣列的檔案，避免前端詳情頁 404。

    Args:
        records: 合併後的紀錄列表
        output_dir: 輸出目錄，預設為 api/securities/
        listings: 證券清單（可選，用於補上無配息歷史的證券）

    Returns:
        產出的檔案數量
    """
    if output_dir is None:
        output_dir = API_DIR / "securities"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 依 code 分組
    by_code: Dict[str, List[Dict]] = {}
    for rec in records:
        code = rec["code"]
        by_code.setdefault(code, []).append(rec)

    # 從 listings 補上無配息歷史的證券（history 空陣列）
    listing_names: Dict[str, str] = {}
    if listings:
        for listing in listings:
            code = listing.get("code", "")
            if not code:
                continue
            listing_names[code] = listing.get("name", "")
            if code not in by_code:
                by_code[code] = []

    # 產出每個檔案
    for code, code_records in by_code.items():
        # 取得 name（用第一筆的；無紀錄時用清單名稱）
        name = (
            code_records[0]["name"]
            if code_records
            else listing_names.get(code, "")
        )

        # 建立 history（跳過沒有 ex_date 的紀錄）
        history = []
        for rec in code_records:
            ex_date = rec.get("ex_date", "")
            if not ex_date:
                continue

            # 從 ex_date 提取年份
            try:
                year = int(ex_date[:4])
            except (ValueError, IndexError):
                year = 0

            history.append({
                "year": year,
                "ex_date": ex_date,
                "cash_dividend": rec.get("cash_dividend", 0),
                "stock_dividend": rec.get("stock_dividend", 0),
            })

        # 依年份降冪排序
        history.sort(key=lambda x: x["year"] or 0, reverse=True)

        data = {
            "code": code,
            "name": name,
            "history": history,
        }

        filepath = output_dir / f"{code}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return len(by_code)


def generate_monthly_dividends(records: List[Dict]) -> Dict[str, List[Dict]]:
    """
    依月份分組產生配息清單，寫入 api/dividends/YYYY-MM.json。

    每個檔案包含該月所有配息紀錄（含過去與未來），供行事曆與列表使用。
    業務規則：
    - 以 ex_date 的年月分組
    - 每月內依 ex_date 升冪排序

    Args:
        records: 合併後的紀錄列表

    Returns:
        {"2026-03": [...], "2026-04": [...], ...}（已排序）
    """
    by_month: Dict[str, List[Dict]] = {}

    for rec in records:
        ex_date = rec.get("ex_date", "")
        if not ex_date or len(ex_date) < 7:
            continue
        month_key = ex_date[:7]  # "2026-03"
        entry = {
            "code": rec["code"],
            "name": rec["name"],
            "type": rec.get("type", "息"),
            "ex_date": ex_date,
            "pay_date": rec.get("pay_date", ""),
            "cash_dividend": rec.get("cash_dividend", 0),
            "stock_dividend": rec.get("stock_dividend", 0),
        }
        by_month.setdefault(month_key, []).append(entry)

    # 每月內依 ex_date 排序
    for month_key in by_month:
        by_month[month_key].sort(key=lambda x: x["ex_date"])

    return dict(sorted(by_month.items()))


def save_api_file(data, filename: str, output_dir: Optional[Path] = None) -> Path:
    """
    將資料寫入 api/ 目錄的 JSON 檔案

    Args:
        data: 要序列化的 Python 物件
        filename: 檔案名稱（如 upcoming.json）
        output_dir: 輸出目錄，預設為 api/

    Returns:
        寫入的檔案路徑
    """
    if output_dir is None:
        output_dir = API_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


# ------------------------------------------------------------------
# 主執行流程
# ------------------------------------------------------------------

def main(source_name: str = DEFAULT_SOURCE):
    """
    主執行流程

    流程：
    1. 讀取基底證券歷史（data/{stocks,etfs,preferred}）
    2. 讀取指定來源的公告紀錄（預設 moneydj，可切換）
    3. 合併資料
    4. 產生 upcoming.json
    5. 產生 securities-index.json
    6. 產生 securities/*.json
    7. 輸出統計資訊

    Args:
        source_name: 資料來源名稱（SOURCE_REGISTRY 的 key），
            預設為 DEFAULT_SOURCE（moneydj）

    Raises:
        ValueError: 未知的資料來源名稱
    """
    source = get_source(source_name)
    print(f"🔄 開始產生 API 資料（來源: {source.label} [{source.name}]）...")

    # 1. 讀取基底證券歷史
    print("📋 讀取基底證券歷史...")
    securities = load_securities()
    print(f"   基底證券: {len(securities)} 筆")

    # 2. 讀取指定來源的公告紀錄
    print(f"📋 讀取公告紀錄（{source.label}）...")
    announcements = source.build_announcements()
    print(f"   公告紀錄: {len(announcements)} 筆")

    # 3. 合併（基底為主體，公告更新/補充 pay_date 與金額）
    records = merge_securities_and_announcements(securities, announcements)
    if not records:
        print("❌ 找不到任何資料，請先執行爬蟲（或改用其他來源）")
        return

    print(f"📊 合併後共 {len(records)} 筆紀錄")

    # 4. 產生月份配息（api/dividends/YYYY-MM.json）
    print("📅 產生月份配息資料...")
    monthly = generate_monthly_dividends(records)
    dividends_dir = API_DIR / "dividends"
    dividends_dir.mkdir(parents=True, exist_ok=True)
    total_dividends = 0
    month_keys = []  # 用於產生 index.json
    for month_key, month_records in monthly.items():
        save_api_file(month_records, f"{month_key}.json", dividends_dir)
        month_keys.append(month_key)
        total_dividends += len(month_records)
        print(f"   ✅ dividends/{month_key}.json: {len(month_records)} 筆")
    print(f"   共 {len(monthly)} 個月份，{total_dividends} 筆配息")

    # 4.1 產生 index.json（記錄有哪些月份檔案）
    index_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "months": month_keys,
    }
    save_api_file(index_data, "dividends/index.json")
    print(f"   ✅ dividends/index.json: {len(month_keys)} 個月份")

    # 5. 產生 securities-index.json
    print("📋 產生證券清單...")
    listings = load_listings()
    print(f"   證券清單: {len(listings)} 筆")
    index = generate_securities_index(records, listings)
    save_api_file(index, "securities-index.json")
    print(f"   ✅ securities-index.json: {len(index)} 支證券")

    # 6. 產生 securities/*.json
    print("📁 產生單股歷史...")
    sec_count = generate_securities_history(records, listings=listings)
    print(f"   ✅ securities/: {sec_count} 個檔案")

    # 7. 統計
    print(f"\n{'='*50}")
    print(f"✅ API 資料產生完成（來源: {source.name}）")
    print(f"   月份配息：{total_dividends} 筆（{len(monthly)} 個月份）")
    print(f"   證券總數：{len(index)} 支")
    print(f"   輸出目錄：{API_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="產生 API 靜態 JSON（配息資料來源可切換）")
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help=(
            f"資料來源（預設: {DEFAULT_SOURCE}）；"
            f"可用: {', '.join(sorted(SOURCE_REGISTRY))}"
        ),
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="列出所有可用資料來源後離開",
    )
    args = parser.parse_args()

    if args.list_sources:
        list_sources()
    else:
        main(args.source)
