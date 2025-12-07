#!/bin/bash
# GitHub Secrets 配置助手
# 在 Mac mini 上运行，输出需要配置的 Secrets 值

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 GitHub Secrets 配置助手"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "请访问此链接添加 Secrets："
echo "👉 https://github.com/GeorgeZhiXu/AiChatBot/settings/secrets/actions"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Secret 1: Host
echo "1️⃣  MAC_MINI_HOST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Name:  MAC_MINI_HOST"
echo "Value: 24.19.48.87"
echo ""
read -p "按回车继续..." -r

# Secret 2: User
echo ""
echo "2️⃣  MAC_MINI_USER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Name:  MAC_MINI_USER"
echo "Value: $(whoami)"
echo ""
read -p "按回车继续..." -r

# Secret 3: SSH Key
echo ""
echo "3️⃣  MAC_MINI_SSH_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Name:  MAC_MINI_SSH_KEY"
echo "Value: (复制下面的完整内容，包括 BEGIN 和 END 行)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SSH_KEY="$HOME/.ssh/id_ed25519"
if [ -f "$SSH_KEY" ]; then
    cat "$SSH_KEY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "✅ 复制上面的私钥内容（包括 BEGIN/END）"
    echo ""

    # 复制到剪贴板（macOS）
    if command -v pbcopy &> /dev/null; then
        cat "$SSH_KEY" | pbcopy
        echo "✨ 私钥已自动复制到剪贴板！"
        echo "   直接在 GitHub 粘贴即可"
    fi
else
    echo "❌ SSH 密钥不存在: $SSH_KEY"
    echo "   请先运行: ssh-keygen -t ed25519 -C 'github-actions'"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 配置完成后，推送代码到 main 分支即可自动部署！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
