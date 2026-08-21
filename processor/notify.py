"""
LINE Notify 推播模組 — 篩選即將配息的證券並推播提醒

業務規則：
- 篩選 ex_date 在 3 天內的證券
- 推播格式：代號、名稱、除權息日、配息金額
- 無符合條件時不推播

使用方式：
    python processor/notify.py
    需設定環境變數 LINE_NOTIFY_TOKEN
"""
import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"


def filter_upcoming_3days(upcoming: List[Dict], today: Optional[str] = None) -> List[Dict]:
    """
    篩選 3 天內即將配息的證券

    Args:
        upcoming: upcoming.json 的內容
        today: 用於測試覆蓋

    Returns:
        符合條件的配息列表
    """
    if today is None:
        today_dt = datetime.now()
    else:
        today_dt = datetime.strptime(today, "%Y-%m-%d")

    deadline = today_dt + timedelta(days=3)
    today_str = today_dt.strftime("%Y-%m-%d")
    deadline_str = deadline.strftime("%Y-%m-%d")

    return [
        item for item in upcoming
        if today_str <= item["ex_date"] <= deadline_str
    ]


def format_notify_message(items: List[Dict]) -> str:
    """
    格式化 LINE 推播訊息

    格式範例：
    📢 配息提醒

    以下證券即將除權息：

    • 0056 元大高股息
      除權息日：2026-07-20
      配息金額：$1.80

    • 2330 台積電
      除權息日：2026-07-25
      配息金額：$3.50

    Args:
        items: 符合條件的配息列表

    Returns:
        格式化後的訊息字串
    """
    if not items:
        return ""

    lines = ["📢 配息提醒\n", "以下證券即將除權息：\n"]
    for item in items:
        lines.append(f"• {item['code']} {item['name']}")
        lines.append(f"  除權息日：{item['ex_date']}")
        lines.append(f"  配息金額：${item['dividend']:.2f}")
        lines.append("")

    return "\n".join(lines)


def send_line_notify(message: str, token: str) -> bool:
    """
    發送 LINE Notify 推播

    Args:
        message: 推播訊息
        token: LINE Notify Token

    Returns:
        是否成功
    """
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}

    try:
        response = requests.post(LINE_NOTIFY_API, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"❌ LINE 推播失敗: {e}")
        return False


def main():
    """
    主執行流程

    1. 讀取 api/upcoming.json
    2. 篩選 3 天內配息
    3. 有符合條件則推播，無則略過
    """
    token = os.environ.get("LINE_NOTIFY_TOKEN")
    if not token:
        print("⚠️ 未設定 LINE_NOTIFY_TOKEN，跳過推播")
        return

    api_dir = Path(__file__).resolve().parent.parent / "api"
    upcoming_file = api_dir / "upcoming.json"

    if not upcoming_file.exists():
        print("⚠️ upcoming.json 不存在，請先執行 generate_api.py")
        return

    with open(upcoming_file, "r", encoding="utf-8") as f:
        upcoming = json.load(f)

    items = filter_upcoming_3days(upcoming)

    if not items:
        print("ℹ️ 無符合條件的配息（3 天內），不推播")
        return

    message = format_notify_message(items)
    success = send_line_notify(message, token)

    if success:
        print(f"✅ LINE 推播成功：{len(items)} 支證券")
    else:
        print("❌ LINE 推播失敗")


if __name__ == "__main__":
    main()
