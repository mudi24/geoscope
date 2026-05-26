#!/bin/bash
set -euo pipefail

echo "🚀 GEOScope 启动..."

# 后端
cd backend
if [ ! -d "venv" ]; then
  echo "未检测到 backend/venv，创建虚拟环境..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ 后端 PID: $BACKEND_PID"

# 前端
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端 PID: $FRONTEND_PID"

echo ""
echo "本地访问: http://localhost:3000"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait

