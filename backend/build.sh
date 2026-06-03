#!/usr/bin/env bash
# backend/build.sh
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

# 3. 初始化 SQLite 数据库
#    注意：Render 免费实例磁盘为临时存储，重启后数据会丢失，这是已知取舍
echo "[3/3] Initializing SQLite database..."
python3 init_db.py

echo "──────────────────────────────────────"
echo "  Build complete ✓"
echo "──────────────────────────────────────"
