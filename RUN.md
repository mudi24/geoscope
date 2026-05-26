# GEOScope 运行流程与命令

## 0. 前置条件

- Python 3.11+（本仓库当前环境为 Python 3.13 也可用）
- Node.js 18+ / npm

## 1. 一键启动（推荐）

```bash
chmod +x start.sh
./start.sh
```

- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`（Swagger：`http://localhost:8000/docs`）

## 2. 手动启动（便于调试）

### 2.1 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> `init_db.py` 支持对旧数据库做增量补列（例如 `client_id/status/score_evidence`），无需手动删库重建。

如果遇到 `lxml.html.clean module is now a separate project lxml_html_clean`：

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 2.2 前端

新开一个终端：

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## 3. Playwright（可选，但建议安装）

当 `httpx` 抓取失败或正文太短时会降级到 Playwright。首次使用需要安装浏览器二进制：

```bash
cd backend
source venv/bin/activate
python -m playwright install chromium
```

常见报错：`Executable doesn't exist at .../ms-playwright/.../Chromium` → 按上面安装即可。

## 4. 环境变量（可选）

建议用配置文件（不会被提交到 git）：

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

### 4.1 DeepSeek（启用 AI 分析）

```bash
export DEEPSEEK_API_KEY="你的key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"   # 可选
export DEEPSEEK_MODEL="deepseek-chat"                 # 可选
```

未配置 `DEEPSEEK_API_KEY` 时会返回本地占位 AI 结果（流程仍可演示）。

### 4.2 运行参数

```bash
export GEOSCOPE_CORS_ORIGINS="http://localhost:3000"  # 逗号分隔，或设为 *
export GEOSCOPE_REQUIRE_CLIENT_ID=true                # 默认 true；要求请求带 X-Client-Id，用于数据隔离
export GEOSCOPE_MAX_CONCURRENT_ANALYZE=2              # 后台分析并发
export GEOSCOPE_MAX_CONCURRENT_PLAYWRIGHT=1           # Playwright 并发
export GEOSCOPE_ANALYZE_PER_MINUTE=20                 # /api/analyze 每分钟限流（按 client_id+IP）
export GEOSCOPE_AI_CALLS_PER_DAY=30                   # 每个 client_id 每日外部 AI 调用上限（缓存命中不计数）
export GEOSCOPE_ALLOW_PRIVATE_NETWORKS=false          # true 时允许抓取内网地址（仅调试）
```

## 5. 常用接口（自检/演示）

```bash
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/api/stats -H 'X-Client-Id: demo'
curl -s http://localhost:8000/api/history -H 'X-Client-Id: demo'
curl -s http://localhost:8000/api/analysis/1 -H 'X-Client-Id: demo'
```

查看后端是否读到了 DeepSeek 配置（不会泄露 key，仅显示是否已设置）：

```bash
export GEOSCOPE_ENABLE_DEBUG=true
curl -s http://localhost:8000/api/debug/config
```

提交分析：

```bash
curl -s http://localhost:8000/api/analyze \
  -H 'X-Client-Id: demo' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

## 6. 重置数据库（可选）

```bash
rm -f backend/data/geoscope.db
cd backend && python3 init_db.py
```

## 7. 构建前端（可选）

```bash
cd frontend
npm run build
npm run start
```
