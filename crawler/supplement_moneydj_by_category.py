"""
MoneyDJ 類別頁面補資料腳本
從各產業類別頁面抓取更完整的除權除息資料，合併到 data/moneydj/{YYYY-MM}.json

不修改既有爬蟲，僅借用 MoneyDJExRightCrawler 的解析邏輯。
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# 確保專案根目錄在 sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DATA_MONEYDJ_DIR = ROOT_DIR / "data" / "moneydj"

# 類別頁面 URL 模板
CATEGORY_URL_TEMPLATE = "https://www.moneydj.com/z/ze/zeb/zebb.djhtm?a={category_id}"

# 所有類別清單（從 MoneyDJ 下拉選單萃取）
CATEGORIES = [
    # 上市
    ("EB011000", "上市水泥類股"),
    ("EB012000", "上市食品類股"),
    ("EB013000", "上市塑膠類股"),
    ("EB014000", "上市紡織纖維類股"),
    ("EB015000", "上市電機機械類股"),
    ("EB016000", "上市電器電纜類股"),
    ("EB030000", "上市化工類股"),
    ("EB031000", "上市生技醫療類股"),
    ("EB018000", "上市玻璃陶瓷類股"),
    ("EB019000", "上市造紙類股"),
    ("EB020000", "上市鋼鐵類股"),
    ("EB021000", "上市橡膠類股"),
    ("EB022000", "上市汽車類股"),
    ("EB032000", "上市半導體類股"),
    ("EB033000", "上市電腦及週邊設備類股"),
    ("EB034000", "上市光電類股"),
    ("EB035000", "上市通信網路類股"),
    ("EB036000", "上市電子零組件類股"),
    ("EB037000", "上市電子通路類股"),
    ("EB038000", "上市資訊服務類股"),
    ("EB039000", "上市其他電子類股"),
    ("EB025000", "上市建材營造類股"),
    ("EB026000", "上市航運業類股"),
    ("EB027000", "上市觀光餐旅類股"),
    ("EB028000", "上市金融保險類股"),
    ("EB029000", "上市貿易百貨類股"),
    ("EB040000", "上市油電燃氣類股"),
    ("EB091000", "上市存託憑證類股"),
    ("EB098000", "上市綜合類股"),
    ("EB041000", "上市綠能環保類股"),
    ("EB042000", "上市數位雲端類股"),
    ("EB043000", "上市運動休閒類股"),
    ("EB044000", "上市居家生活類股"),
    ("EB099000", "上市其他類股"),
    ("EB000000", "上市特殊證券類股"),
    ("EB09990R", "上市特別股公司債類股"),
    ("EB095000", "上市創新板類股"),
    # 上櫃
    ("EB142000", "上櫃食品類股"),
    ("EB143000", "上櫃塑膠類股"),
    ("EB144000", "上櫃紡織纖維類股"),
    ("EB145000", "上櫃電機機械類股"),
    ("EB146000", "上櫃電器電纜類股"),
    ("EB147000", "上櫃化工類股"),
    ("EB141000", "上櫃生技醫療類股"),
    ("EB148000", "上櫃玻璃陶瓷類股"),
    ("EB150000", "上櫃鋼鐵類股"),
    ("EB151000", "上櫃橡膠類股"),
    ("EB162000", "上櫃半導體類股"),
    ("EB163000", "上櫃電腦及週邊設備類股"),
    ("EB164000", "上櫃光電類股"),
    ("EB165000", "上櫃通信網路類股"),
    ("EB166000", "上櫃電子零組件類股"),
    ("EB167000", "上櫃電子通路類股"),
    ("EB168000", "上櫃資訊服務類股"),
    ("EB169000", "上櫃其他電子類股"),
    ("EB155000", "上櫃建材營造類股"),
    ("EB156000", "上櫃航運業類股"),
    ("EB157000", "上櫃觀光餐旅類股"),
    ("EB158000", "上櫃金融類股"),
    ("EB161000", "上櫃油電燃氣類股"),
    ("EB170000", "上櫃文化創意類股"),
    ("EB171000", "上櫃農業科技業類股"),
    ("EB187000", "上櫃管理類股"),
    ("EB173000", "上櫃綠能環保類股"),
    ("EB174000", "上櫃數位雲端類股"),
    ("EB175000", "上櫃運動休閒類股"),
    ("EB176000", "上櫃居家生活類股"),
    ("EB188000", "上櫃受益憑證類股"),
    ("EB191000", "上櫃存託憑證類股"),
    ("EB189000", "上櫃其他類股"),
    ("EB18880R", "上櫃特別股公司債類股"),
]


def fetch_category(category_id: str, category_name: str, session) -> list:
    """
    抓取單一類別頁面的除權除息資料

    Args:
        category_id: 類別代號（如 EB011000）
        category_name: 類別名稱
        session: requests.Session

    Returns:
        解析後的資料列表
    """
    from crawler.sources.moneydj_exright import MoneyDJExRightCrawler

    url = CATEGORY_URL_TEMPLATE.format(category_id=category_id)

    try:
        resp = session.get(url, timeout=30, verify=False)
        resp.raise_for_status()
        resp.encoding = "big5"
        html = resp.text

        # 借用既有的解析邏輯
        crawler = MoneyDJExRightCrawler.__new__(MoneyDJExRightCrawler)
        records = crawler._parse_html(html)

        logger.info("  ✅ %s: %d 筆", category_name, len(records))
        return records

    except Exception as e:
        logger.warning("  ⚠️ %s 失敗: %s", category_name, e)
        return []


def split_events(records: list) -> list:
    """借用 fetch.py 的事件拆分邏輯"""
    from crawler.fetch import _split_moneydj_events
    return _split_moneydj_events(records)


def save_moneydj_records(new_records: list, source_label: str = "category") -> dict:
    """
    將事件紀錄合併到 data/moneydj/{YYYY-MM}.json

    Args:
        new_records: 事件級紀錄列表（含 code, name, ex_date, type 等）
        source_label: 日誌標籤

    Returns:
        {月份: 新增筆數} 統計
    """
    from crawler.fetch import _merge_moneydj_records, _merge_same_day_dividend_events

    # 依月份分組
    by_month = {}
    for rec in new_records:
        month = rec["ex_date"][:7]
        by_month.setdefault(month, []).append(rec)

    stats = {}

    for month, new_recs in by_month.items():
        filepath = DATA_MONEYDJ_DIR / f"{month}.json"

        # 讀取舊資料
        old_records = []
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                old_records = data.get("records", [])

        old_count = len(old_records)

        # 合併
        merged = _merge_moneydj_records(old_records, new_recs)

        # 寫入
        output = {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "source": "moneydj",
            "records": merged,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        added = len(merged) - old_count
        stats[month] = {"old": old_count, "new": len(merged), "added": added}
        logger.info("  💾 %s.json: %d → %d (+%d)", month, old_count, len(merged), added)

    return stats


def main():
    """主流程"""
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    logger.info("=" * 60)
    logger.info("📋 MoneyDJ 類別頁面補資料")
    logger.info("=" * 60)

    # 先統計補資料前的數量
    logger.info("\n📊 補資料前：")
    pre_stats = {}
    for f in sorted(DATA_MONEYDJ_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
            recs = data.get("records", [])
            pre_stats[f.name] = len(recs)
            logger.info("  %s: %d 筆", f.name, len(recs))

    # 建立 session
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://www.moneydj.com/",
    })

    # 遍歷所有類別
    all_event_records = []
    total_fetched = 0

    logger.info("\n🔄 開始遍歷 %d 個類別...", len(CATEGORIES))

    for i, (cat_id, cat_name) in enumerate(CATEGORIES, 1):
        logger.info("\n[%d/%d] %s (%s)", i, len(CATEGORIES), cat_name, cat_id)

        records = fetch_category(cat_id, cat_name, session)
        total_fetched += len(records)

        if records:
            events = split_events(records)
            all_event_records.extend(events)

        # 禮貌延遲，避免被擋
        if i < len(CATEGORIES):
            time.sleep(1.5)

    logger.info("\n" + "=" * 60)
    logger.info("📊 抓取完成：%d 個類別，共 %d 筆原始紀錄，%d 筆事件紀錄",
                len(CATEGORIES), total_fetched, len(all_event_records))

    # 合併儲存
    logger.info("\n💾 合併儲存...")
    stats = save_moneydj_records(all_event_records, "category")

    # 統計補資料後的數量
    logger.info("\n📊 補資料後：")
    for f in sorted(DATA_MONEYDJ_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
            recs = data.get("records", [])
            old = pre_stats.get(f.name, 0)
            diff = len(recs) - old
            sign = "+" if diff > 0 else ""
            logger.info("  %s: %d 筆 (%s%d)", f.name, len(recs), sign, diff)

    logger.info("\n" + "=" * 60)
    logger.info("✅ 補資料完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
