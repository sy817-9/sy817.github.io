#!/usr/bin/env python3
"""
ニュースボット
デザインニュースと Claude/AI プロンプト記事を Claude web_search で収集し、
Chatwork ルーム 437135676 に配信する。

必要な環境変数:
  ANTHROPIC_API_KEY   - Anthropic API キー
  CHATWORK_API_TOKEN  - Chatwork API トークン（sy817 のトークン）
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

import anthropic
import requests

# ---- 設定 ----------------------------------------------------------------
CHATWORK_ROOM_ID = "437135676"
CHATWORK_API_URL = f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages"

SCRIPT_DIR = Path(__file__).parent
NEWS_SENT_FILE = SCRIPT_DIR / "news_sent.json"

MAX_ARTICLES = 5
MODEL = "claude-opus-4-7"

DESIGN_KEYWORDS = [
    "UI/UXデザイン トレンド 2026",
    "グラフィックデザイン 最新",
    "デザインツール 新機能",
    "Figma Canva Adobe 最新情報",
]

AI_KEYWORDS = [
    "Claude Code プロンプト 活用",
    "AI デザイン プロンプトエンジニアリング",
    "Claude Design 使い方",
    "AIツール クリエイター向け",
]


# ---- 配信済み URL 管理 ----------------------------------------------------

def load_sent_urls() -> set:
    if NEWS_SENT_FILE.exists():
        data = json.loads(NEWS_SENT_FILE.read_text(encoding="utf-8"))
        return set(data.get("urls", []))
    return set()


def save_sent_urls(new_urls: set) -> None:
    existing = load_sent_urls()
    all_urls = list(existing | new_urls)
    NEWS_SENT_FILE.write_text(
        json.dumps({"urls": all_urls}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---- 記事収集 -------------------------------------------------------------

def search_articles(client: anthropic.Anthropic, keywords: list[str]) -> list[dict]:
    """Claude web_search で記事を収集し JSON リストで返す。"""
    keywords_text = "、".join(keywords)
    prompt = (
        f"以下のキーワードでウェブ検索して最新記事を {MAX_ARTICLES} 件見つけてください。\n"
        f"キーワード：{keywords_text}\n\n"
        "2025〜2026 年の信頼性の高い日本語・英語記事を優先してください。\n"
        "各記事のタイトル・URL・日本語 2〜3 行の要約を含む JSON のみを返してください：\n"
        '{"articles": [{"title": "...", "url": "https://...", "summary": "..."}]}'
    )

    messages: list[dict] = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20250305", "name": "web_search"}]

    for _ in range(20):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            # Concatenate all text blocks (response may be split across many blocks)
            full_text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            # Strip markdown code fences if present
            for fence in ("```json", "```"):
                if fence in full_text:
                    full_text = full_text.split(fence, 1)[-1].rsplit("```", 1)[0]
            s = full_text.find("{")
            e = full_text.rfind("}") + 1
            if s >= 0 and e > s:
                try:
                    return json.loads(full_text[s:e]).get("articles", [])[:MAX_ARTICLES]
                except json.JSONDecodeError:
                    pass
            return []

        # tool_use — add assistant turn and continue (server handles search execution)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

    return []


def filter_new(articles: list[dict], sent_urls: set) -> list[dict]:
    seen: set = set()
    result = []
    for a in articles:
        url = a.get("url", "")
        if url and url not in sent_urls and url not in seen:
            seen.add(url)
            result.append(a)
    return result


# ---- メッセージ構築 -------------------------------------------------------

def build_message(design: list[dict], ai: list[dict]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = [
        f"🎨 デザインニュース | {today}",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "📰 デザイントレンド・ニュース",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for i, a in enumerate(design, 1):
        lines += [f"[{i}] {a['title']}", f"📝 要約：{a['summary']}", f"🔗 {a['url']}", ""]

    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        "🤖 Claude/AIプロンプト・記事",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for i, a in enumerate(ai, 1):
        lines += [f"[{i}] {a['title']}", f"📝 要約：{a['summary']}", f"🔗 {a['url']}", ""]

    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        "AI秘書ニュースボット | 8:00配信",
    ]
    return "\n".join(lines)


# ---- Chatwork 送信 --------------------------------------------------------

def send_to_chatwork(message: str, token: str) -> dict:
    resp = requests.post(
        CHATWORK_API_URL,
        headers={"X-ChatWorkToken": token},
        data={"body": message},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---- エントリポイント -----------------------------------------------------

def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    cw_token = os.environ.get("CHATWORK_API_TOKEN")

    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY が設定されていません")
    if not cw_token:
        sys.exit("Error: CHATWORK_API_TOKEN が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)
    sent_urls = load_sent_urls()

    print("🔍 デザインニュースを収集中...", flush=True)
    design_articles = filter_new(search_articles(client, DESIGN_KEYWORDS), sent_urls)

    print("🔍 AI/Claude ニュースを収集中...", flush=True)
    ai_articles = filter_new(search_articles(client, AI_KEYWORDS), sent_urls)

    if not design_articles and not ai_articles:
        print("新しい記事が見つかりませんでした")
        return

    message = build_message(design_articles, ai_articles)
    print("\n--- 配信メッセージ ---")
    print(message)
    print("-------------------\n")

    print("📨 Chatwork に送信中...", flush=True)
    send_to_chatwork(message, cw_token)

    new_urls = {a["url"] for a in design_articles + ai_articles if a.get("url")}
    save_sent_urls(new_urls)

    print(f"✅ 配信完了：デザイン {len(design_articles)} 件 / AI・Claude {len(ai_articles)} 件")


if __name__ == "__main__":
    main()
