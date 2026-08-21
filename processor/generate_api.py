"""
資料處理器 — 將 data/ 基底資料轉換為 api/ 前端用 JSON

職責：
1. 讀取 data/{stocks,etfs,preferred}/*.json
2. 產生 api/upcoming.json（未來配息清單）
3. 產生 api/securities-index.json（證券清單）
4. 產生 api/securities/{code}.json（單股歷史）

使用方式：
    python processor/generate_api.py
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 專案路徑
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
API_DIR = ROOT_DIR / "api"

# 子目錄
DATA_SUBDIRS = ["stocks", "etfs", "preferred"]


def load_all_securities() -> List[Dict]:
    """
    從 data/ 目錄讀取所有證券基底資料

    遍歷 data/stocks/、data/etfs/、data/preferred/，
    讀取每個 JSON 檔案，合併為單一列表。
    自動依據子目錄推斷 type 欄位（若不存在）。

    Returns:
        證券資料列表，每筆包含 code, name, type, dividend_history 等欄位
    """
    securities = []
    for subdir in DATA_SUBDIRS:
        dir_path = DATA_DIR / subdir
        if not dir_path.exists():
            continue

        # 根據子目錄映射 type
        type_map = {
            "stocks": "stock",
            "etfs": "etf",
            "preferred": "preferred",
        }
        default_type = type_map.get(subdir, "stock")

        for json_file in sorted(dir_path.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 若 data 中沒有 type 欄位，從子目錄推斷
                if "type" not in data:
                    data["type"] = default_type
                securities.append(data)
    return securities


def generate_upcoming(securities: List[Dict], today: Optional[str] = None) -> List[Dict]:
    """
    篩選未來配息，產生 upcoming 清單

    業務規則：
    - ex_date >= today（今天或未來）才納入
    - 每筆包含 code, name, type, ex_date, pay_date, dividend
    - 依 ex_date 升冪排序

    Args:
        securities: load_all_securities() 回傳的完整列表
        today: 用於測試覆蓋，預設為 datetime.now().strftime("%Y-%m-%d")

    Returns:
        upcoming 配息列表（已排序）
    """
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")

    upcoming = []
    for sec in securities:
        for record in sec.get("dividend_history", []):
            ex_date = record.get("ex_date", "")
            if ex_date >= today:
                upcoming.append({
                    "code": sec["code"],
                    "name": sec["name"],
                    "type": sec.get("type", "stock"),
                    "ex_date": ex_date,
                    "pay_date": record.get("pay_date", ""),
                    "dividend": record.get("cash_dividend", 0),
                })

    # 依 ex_date 升冪排序
    upcoming.sort(key=lambda x: x["ex_date"])
    return upcoming


def generate_securities_index(securities: List[Dict]) -> List[Dict]:
    """
    產生證券清單索引

    每筆包含 code, name，供前端搜尋功能使用。

    Args:
        securities: 完整證券列表

    Returns:
        證券索引列表
    """
    index = []
    for sec in securities:
        index.append({
            "code": sec["code"],
            "name": sec["name"],
        })
    return index


def generate_securities_history(
    securities: List[Dict],
    output_dir: Optional[Path] = None,
) -> None:
    """
    產出每支證券的歷史配息檔案

    每支證券一個 JSON 檔案：
    api/securities/{code}.json

    檔案格式：
    {
        "code": "2330",
        "name": "台積電",
        "history": [
            {"year": 2026, "ex_date": "2026-07-25", "dividend": 3.5},
            ...
        ]
    }

    Args:
        securities: 完整證券列表
        output_dir: 輸出目錄，預設為 api/securities/
    """
    if output_dir is None:
        output_dir = API_DIR / "securities"
    output_dir.mkdir(parents=True, exist_ok=True)

    for sec in securities:
        history = []
        for record in sec.get("dividend_history", []):
            history.append({
                "year": record.get("year"),
                "ex_date": record.get("ex_date", ""),
                "dividend": record.get("cash_dividend", 0),
            })

        # 依年份降冪排序
        history.sort(key=lambda x: x["year"] or 0, reverse=True)

        data = {
            "code": sec["code"],
            "name": sec["name"],
            "history": history,
        }

        filepath = output_dir / f"{sec['code']}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


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


def main():
    """
    主執行流程

    流程：
    1. 讀取所有基底資料
    2. 產生 upcoming.json
    3. 產生 securities-index.json
    4. 產生 securities/*.json
    5. 輸出統計資訊
    """
    print("🔄 開始產生 API 資料...")

    # 1. 讀取基底資料
    securities = load_all_securities()
    if not securities:
        print("❌ 找不到基底資料，請先執行爬蟲")
        return

    print(f"📊 讀取到 {len(securities)} 支證券")

    # 2. 產生 upcoming.json
    print("📅 篩選未來配息...")
    upcoming = generate_upcoming(securities)
    save_api_file(upcoming, "upcoming.json")
    print(f"   ✅ upcoming.json: {len(upcoming)} 筆未來配息")

    # 3. 產生 securities-index.json
    print("📋 產生證券清單...")
    index = generate_securities_index(securities)
    save_api_file(index, "securities-index.json")
    print(f"   ✅ securities-index.json: {len(index)} 支證券")

    # 4. 產生 securities/*.json
    print("📁 產生單股歷史...")
    generate_securities_history(securities)
    print(f"   ✅ securities/: {len(index)} 個檔案")

    # 5. 統計
    print(f"\n{'='*50}")
    print(f"✅ API 資料產生完成")
    print(f"   未來配息：{len(upcoming)} 筆")
    print(f"   證券總數：{len(index)} 支")
    print(f"   輸出目錄：{API_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
