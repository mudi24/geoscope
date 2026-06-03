#!/usr/bin/env bash
# backend/build.sh - v2 (skip install-deps)
# Render 构建脚本：安装 Python 依赖 + Playwright Chromium
set -euo pipefail

echo "──────────────────────────────────────"
echo "  GEOScope Backend Build"
echo "──────────────────────────────────────"

# 1. 安装 Python 依赖
echo "[1/3] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. 安装 Playwright Chromium 浏览器二进制
echo "[2/3] Installing Playwright Chromium..."
# Render 的 Python 环境已预装大部分系统依赖，跳过 install-deps 避免权限问题
PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 python -m playwright install chromium

# 3. 安装 CJK 字体（供 PDF 导出使用，避免中文乱码）
echo "[3/4] Installing CJK fonts for PDF export..."
# 优先用 apt 安装系统字体包（Render 构建环境支持 apt-get）
if command -v apt-get &>/dev/null; then
  apt-get install -y --no-install-recommends fonts-noto-cjk 2>/dev/null \
    || apt-get install -y --no-install-recommends fonts-wqy-zenhei 2>/dev/null \
    || echo "WARNING: apt font install failed"
fi

# 备用：如果系统包安装失败，尝试下载单个 OTF 文件（简体中文子集，约 5MB）
FONT_DIR="$(pwd)/fonts"
mkdir -p "$FONT_DIR"
FONT_PATH="$FONT_DIR/NotoSansSC-Regular.otf"
if [ ! -f "$FONT_PATH" ]; then
  curl -fsSL --retry 3 --retry-delay 2 \
    "https://github.com/googlefonts/noto-cjk/raw/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf" \
    -o "$FONT_PATH" \
    && echo "Font downloaded OK: $FONT_PATH" \
    || echo "WARNING: Font download failed, PDF may render Chinese as boxes"
fi

# 4. 初始化 SQLite 数据库
#    注意：Render 免费实例磁盘为临时存储，重启后数据会丢失，这是已知取舍
echo "[4/4] Initializing SQLite database..."
python3 init_db.py

echo "──────────────────────────────────────"
echo "  Build complete ✓"
echo "──────────────────────────────────────"

# Print installed CJK fonts for debugging
echo "[INFO] Installed CJK fonts:"
fc-list :lang=zh 2>/dev/null | head -10 || find /usr/share/fonts -name "*[Nn]oto*CJK*" -o -name "wqy*" 2>/dev/null | head -10 || echo "  (none found via fc-list)"
echo "[INFO] Project fonts dir:"
ls -lh "$(dirname "$0")/fonts/" 2>/dev/null || echo "  (empty)"

