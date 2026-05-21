#!/bin/bash
# ニュースデーモン セットアップスクリプト
# 使い方: bash setup_newsdaemon.sh

set -e

AI_DIR="$HOME/Desktop/ai-secretary"
PLIST_NAME="com.ai-secretary.newsdaemon.plist"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

echo "=== ニュースデーモン セットアップ ==="
echo ""

# 1. news_daemon.py の存在確認
echo "【1】$AI_DIR/news_daemon.py を確認中..."
if [ -f "$AI_DIR/news_daemon.py" ]; then
    echo "    ✅ 存在します"
else
    echo "    ⚠️  見つかりません。リポジトリからコピーします..."
    mkdir -p "$AI_DIR"
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    cp "$SCRIPT_DIR/news_bot.py"    "$AI_DIR/"
    cp "$SCRIPT_DIR/news_daemon.py" "$AI_DIR/"
    echo "    ✅ コピーしました: news_bot.py / news_daemon.py"
fi

echo ""

# 2. plist を ~/Desktop/ai-secretary/ に作成
echo "【2】$AI_DIR/$PLIST_NAME を作成中..."

USERNAME="$(whoami)"
PYTHON3="$(which python3)"

cat > "$AI_DIR/$PLIST_NAME" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ai-secretary.newsdaemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON3</string>
        <string>$AI_DIR/news_daemon.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/news_daemon.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/news_daemon_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>${ANTHROPIC_API_KEY:-YOUR_ANTHROPIC_API_KEY_HERE}</string>
        <key>CHATWORK_API_TOKEN</key>
        <string>${CHATWORK_API_TOKEN:-YOUR_CHATWORK_API_TOKEN_HERE}</string>
    </dict>
</dict>
</plist>
EOF

echo "    ✅ 作成しました: $AI_DIR/$PLIST_NAME"
echo "    python3 パス : $PYTHON3"
echo "    スクリプトパス: $AI_DIR/news_daemon.py"

echo ""

# 3. LaunchAgents に登録
echo "【3】LaunchAgent に登録中..."
mkdir -p "$LAUNCH_AGENTS"

# 既存の登録を解除してから再登録
launchctl unload "$LAUNCH_AGENTS/$PLIST_NAME" 2>/dev/null || true
cp "$AI_DIR/$PLIST_NAME" "$LAUNCH_AGENTS/"
launchctl load "$LAUNCH_AGENTS/$PLIST_NAME"

echo "    ✅ 登録完了"
echo ""

# 4. 確認
echo "【4】動作確認..."
sleep 1
STATUS=$(launchctl list | grep newsdaemon || echo "")
if [ -n "$STATUS" ]; then
    echo "    ✅ 起動中: $STATUS"
else
    echo "    ⚠️  未起動。API キーが未設定の可能性があります。"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ："
echo "  テスト配信:"
echo "    ANTHROPIC_API_KEY=sk-ant-... CHATWORK_API_TOKEN=<token> python3 $AI_DIR/news_bot.py"
echo ""
echo "  ログ確認:"
echo "    tail -f /tmp/news_daemon.log"
echo ""
echo "  停止:"
echo "    launchctl unload $LAUNCH_AGENTS/$PLIST_NAME"
