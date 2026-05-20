#!/usr/bin/env python3
"""
ニュースデーモン
毎朝 8:00 に news_bot.py を実行するスケジューラー。
Mac 起動時に LaunchAgent (com.ai-secretary.newsdaemon.plist) 経由で自動起動する。
"""

import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

NEWS_BOT = Path(__file__).parent / "news_bot.py"


def next_8am() -> datetime:
    now = datetime.now()
    target = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return target


def log(msg: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def run_bot() -> None:
    log("ニュースボット起動")
    result = subprocess.run([sys.executable, str(NEWS_BOT)])
    if result.returncode == 0:
        log("正常終了")
    else:
        log(f"エラー終了 (code={result.returncode})")


def main() -> None:
    log("ニュースデーモン起動")

    while True:
        nxt = next_8am()
        wait = (nxt - datetime.now()).total_seconds()
        log(f"次回配信: {nxt:%Y-%m-%d %H:%M:%S} ({wait:.0f} 秒後)")
        time.sleep(max(wait, 0))
        run_bot()


if __name__ == "__main__":
    main()
