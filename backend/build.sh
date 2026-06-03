#!/usr/bin/env bash
# backend/build.sh
# Render 构建脚本：安装 Python 依赖 + Playwright Chromium 系统依赖
set -euo pipefail

echo "──────────────────────────────────────"
echo "  GEOScope Backend Build"
echo "──────────────────────────────────────"

# 1. 安装 Python 依赖
echo "[1/4] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. 安装 Playwright Chromium 浏览器二进制
echo "[2/4] Installing Playwright Chromium..."
python -m playwright install chromium

# 3. 安装 Chromium 所需的系统级依赖（Render 运行在 Debian/Ubuntu）
echo "[3/4] Installing Chromium system dependencies..."
python -m playwright install-deps chromium

# 4. 初始化 SQLite 数据库
#    注意：Render 免费实例磁盘为临时存储，重启后数据会丢失，这是已知取舍
echo "[4/4] Initializing SQLite database..."
python3 init_db.py

echo "──────────────────────────────────────"
echo "  Build complete ✓"
echo "──────────────────────────────────────"
