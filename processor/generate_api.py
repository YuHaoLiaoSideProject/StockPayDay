"""
資料處理器 — 將 data/ 基底資料轉換為 api/ 前端用 JSON

職責：
1. 讀取 data/twses/*.json（TWT48U 除息預告）
2. 讀取 data/mops/*.json（MOPS 配息日）
3. 產生 api/upcoming.json（未來配息清單）
4. 產生 api/securities-index.json（證券清單）
5. 產生 api/securities/{code}.json（單股歷史）

使用方式：
    python processor/generate_api.py
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# 專案路徑
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
API_DIR = ROOT_DIR / "api"

# 資料子目錄
TWT48U_DIR = DATA_DIR / "twses"
MOPS_DIR = DATA_DIR / "mops"


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
    if not TWT48U_DIR.exists():
        logger.warning("TWT48U 資料目錄不存在: %s", TWT48U_DIR)
        return records

    for json_file in sorted(TWT48U_DIR.glob("*.json")):
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
    從 data/mops/ 讀取 MOPS 配息日資料

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
    if not MOPS_DIR.exists():
        logger.warning("MOPS 資料目錄不存在: %s", MOPS_DIR)
        return records

    for json_file in sorted(MOPS_DIR.glob("*.json")):
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
                "cash_dividend": rec.get("cash_dividend", 0),
                "stock_dividend": rec.get("stock_dividend", 0),
            })

    # 依 ex_date 升冪排序
    upcoming.sort(key=lambda x: x["ex_date"])
    return upcoming


def generate_securities_index(records: List[Dict]) -> List[Dict]:
    """
    產生證券清單索引（去重）

    每筆包含 code, name，供前端搜尋功能使用。

    Args:
        records: 合併後的紀錄列表

    Returns:
        證券索引列表（已去重）
    """
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
    return index


def generate_securities_history(
    records: List[Dict],
    output_dir: Optional[Path] = None,
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

    Args:
        records: 合併後的紀錄列表
        output_dir: 輸出目錄，預設為 api/securities/

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

    # 產出每個檔案
    for code, code_records in by_code.items():
        # 取得 name（用第一筆的）
        name = code_records[0]["name"] if code_records else ""

        # 建立 history（跳過沒有 ex_date 的紀錄）
        history = []
        for rec in code_records:
            ex_date = rec.get("ex_date", "")
            if not ex_date:
                continue

            # 從 ex_date 提取年份
            year = int(ex_date[:4])

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

def main():
    """
    主執行流程

    流程：
    1. 讀取 TWT48U 資料
    2. 讀取 MOPS 資料
    3. 合併資料
    4. 產生 upcoming.json
    5. 產生 securities-index.json
    6. 產生 securities/*.json
    7. 輸出統計資訊
    """
    print("🔄 開始產生 API 資料...")

    # 1. 讀取 TWT48U
    print("📋 讀取 TWT48U 除息預告...")
    twses = load_twses()
    print(f"   TWT48U: {len(twses)} 筆")

    # 2. 讀取 MOPS
    print("📋 讀取 MOPS 配息日...")
    mops = load_mops()
    print(f"   MOPS: {len(mops)} 筆")

    # 3. 合併
    records = merge_twses_and_mops(twses, mops)
    if not records:
        print("❌ 找不到任何資料，請先執行爬蟲")
        return

    print(f"📊 合併後共 {len(records)} 筆紀錄")

    # 4. 產生 upcoming.json
    print("📅 篩選未來配息...")
    upcoming = generate_upcoming(records)
    save_api_file(upcoming, "upcoming.json")
    print(f"   ✅ upcoming.json: {len(upcoming)} 筆未來配息")

    # 5. 產生 securities-index.json
    print("📋 產生證券清單...")
    index = generate_securities_index(records)
    save_api_file(index, "securities-index.json")
    print(f"   ✅ securities-index.json: {len(index)} 支證券")

    # 6. 產生 securities/*.json
    print("📁 產生單股歷史...")
    sec_count = generate_securities_history(records)
    print(f"   ✅ securities/: {sec_count} 個檔案")

    # 7. 統計
    print(f"\n{'='*50}")
    print(f"✅ API 資料產生完成")
    print(f"   未來配息：{len(upcoming)} 筆")
    print(f"   證券總數：{len(index)} 支")
    print(f"   輸出目錄：{API_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
