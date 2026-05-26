# GEOScope 技术方案文档
**版本**：零服务器纯本地 MVP  
**目标**：面试演示可用的 GEO 分析平台

> 已按本文档落地实现基础版本；面试演示推荐按 `ITERATIONS.md` 的 3 个迭代顺序讲解与展示。

---

## 一、技术架构总览

```
┌─────────────────────────────────────┐
│  前端 (Next.js 14 App Router)        │
│  - 静态导出 → Vercel 免费托管         │
│  - 与后端通信: 环境变量配置 API 地址   │
├─────────────────────────────────────┤
│  后端 (Python + FastAPI)             │
│  - 单进程 Uvicorn 本地运行            │
│  - SQLite 单文件数据库               │
│  - 三层爬虫降级策略                   │
│  - DeepSeek API 代理 + 本地缓存       │
└─────────────────────────────────────┘
```

---

## 二、项目目录结构

```
geoscope/
├── README.md                 # 项目说明
├── start.sh                  # 一键启动脚本
├── backend/                  # Python 后端
│   ├── main.py               # FastAPI 入口 + 路由
│   ├── requirements.txt      # 依赖清单
│   ├── init_db.sql           # 数据库初始化
│   ├── data/                 # SQLite 数据目录
│   │   └── .gitkeep
│   ├── core/
│   │   ├── __init__.py
│   │   ├── fetcher.py        # 爬虫三层降级
│   │   ├── geo_scorer.py     # 本地五维评分引擎
│   │   ├── ai_analyzer.py    # DeepSeek API 代理 + 缓存
│   │   └── heartbeat.py      # 保活心跳
│   └── models/
│       ├── __init__.py
│       └── schemas.py        # Pydantic 模型
│
├── frontend/                 # Next.js 前端
│   ├── package.json
│   ├── next.config.js        # 静态导出配置
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── app/
│   │   ├── layout.tsx        # 根布局
│   │   ├── page.tsx          # 首页 (URL输入)
│   │   ├── globals.css
│   │   ├── analyze/
│   │   │   └── [id]/
│   │   │       └── page.tsx  # 分析结果页
│   │   └── history/
│   │       └── page.tsx      # 历史记录页
│   ├── components/
│   │   ├── UrlInput.tsx      # URL 输入组件
│   │   ├── ScoreRadar.tsx    # 五维雷达图
│   │   ├── ScoreCard.tsx     # 单项评分卡片
│   │   ├── AIReport.tsx      # AI 分析结果展示
│   │   ├── SuggestionList.tsx # 优化建议列表
│   │   └── HistoryTable.tsx  # 历史记录表格
│   └── lib/
│       └── api.ts            # API 请求封装
└── .gitignore
```

---

## 三、数据库设计（SQLite）

**文件**：`backend/init_db.sql`

```sql
-- 分析主表
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT,
    domain TEXT,
    content_length INTEGER,
    
    -- 五维评分 (0-100)
    semantic_clarity INTEGER DEFAULT 0,
    entity_completeness INTEGER DEFAULT 0,
    citation_credibility INTEGER DEFAULT 0,
    qa_friendly INTEGER DEFAULT 0,
    tech_markup INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    
    -- AI 分析结果 (JSON 文本存储)
    ai_summary TEXT,
    ai_gaps TEXT,
    ai_suggestions TEXT,
    
    -- 抓取与缓存信息
    fetch_method TEXT DEFAULT 'httpx',
    content_fingerprint TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI 结果缓存表 (避免重复调用 API)
CREATE TABLE IF NOT EXISTS ai_cache (
    fingerprint TEXT PRIMARY KEY,
    url TEXT,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_analyses_url ON analyses(url);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_cache_created ON ai_cache(created_at);
```

**Pydantic 模型**：`backend/models/schemas.py`

```python
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class AnalyzeRequest(BaseModel):
    url: HttpUrl

class GeoScores(BaseModel):
    semantic_clarity: int
    entity_completeness: int
    citation_credibility: int
    qa_friendly: int
    tech_markup: int
    total_score: int

class AIResult(BaseModel):
    summary: str
    gaps: List[str]
    suggestions: List[str]

class AnalysisResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    domain: Optional[str]
    scores: GeoScores
    ai_result: AIResult
    fetch_method: str
    created_at: datetime

class HistoryItem(BaseModel):
    id: int
    url: str
    title: Optional[str]
    total_score: int
    created_at: datetime
```

---

## 四、后端核心模块设计

### 4.1 FastAPI 入口与路由 (`backend/main.py`)

**功能规格**：
- `POST /api/analyze` - 提交 URL 进行分析
- `GET /api/analysis/{id}` - 获取分析结果详情
- `GET /api/history` - 获取历史记录列表 (最近 20 条)
- `GET /api/health` - 健康检查 (供心跳使用)
- 启动时自动初始化 SQLite 数据库
- CORS 配置允许前端域名

### 4.2 爬虫模块 (`backend/core/fetcher.py`)

**三层降级策略**：

| 层级 | 方法 | 触发条件 | 内存占用 |
|-----|------|---------|---------|
| L1 | `httpx` + `readability-lxml` | 默认首选 | ~20MB |
| L2 | `playwright` headless | L1 失败或内容 < 500 字 | ~150MB |
| L3 | 返回错误 | L2 也失败 | - |

**输入**：URL  
**输出**：`{"title": str, "content": str, "method": str, "length": int}`

**关键要求**：
- 正文提取后清理 HTML 标签、脚本、样式
- 限制内容长度最大 8000 字，超长截断
- Playwright 使用完必须关闭 browser 上下文

### 4.3 本地评分引擎 (`backend/core/geo_scorer.py`)

**五维评分算法**（纯本地规则，零 Token）：

| 维度 | 检测规则 | 满分条件 |
|-----|---------|---------|
| semantic_clarity | H1-H6 层级是否合理、段落平均长度、小标题密度 | 有 H1、段落 < 200 字、小标题 > 3 个 |
| entity_completeness | 关键术语首次出现是否有上下文解释、缩写是否展开 | 检测到"XX 是..."句式、括号解释 |
| citation_credibility | 作者信息、发布日期、外部链接数、域名权威度 | 有作者+日期+外链 |
| qa_friendly | 是否包含 FAQ 结构、结论前置、直接答案句式 | 检测到"什么是"、"如何"问答块 |
| tech_markup | Schema.org JSON-LD、Open Graph、Canonical | 有 Article/FAQ Schema |

**评分逻辑**：每条规则加权累加，归一化到 0-100。

### 4.4 AI 分析代理 (`backend/core/ai_analyzer.py`)

**功能规格**：
1. 生成内容指纹 (MD5 前 1000 字)
2. 查 `ai_cache` 表，7 天内命中直接返回
3. 未命中则截断正文至 3000 字
4. 调用 DeepSeek API
5. 解析返回 JSON，存入缓存
6. 返回结构化结果

**Prompt 模板**：

```
你是一位生成式搜索引擎的批判性读者。请分析以下网页内容，严格按 JSON 格式返回：

{
  "summary": "一句话总结页面核心主题",
  "gaps": ["知识缺口1", "知识缺口2", "知识缺口3"],
  "suggestions": [
    {"priority": 1, "issue": "具体问题", "fix": "具体修改建议"},
    {"priority": 2, "issue": "...", "fix": "..."},
    {"priority": 3, "issue": "...", "fix": "..."}
  ]
}

要求：
1. gaps 必须具体，如"第3段提到'CAP定理'但未解释其含义"，而非"有些概念不清楚"
2. suggestions 必须可执行，包含具体位置和修改方式
3. 评估"可引用性"：AI 搜索回答相关问题时，引用此页面的可能性及原因

正文内容：
---
{content}
---
```

**API 配置**：
- 模型：`deepseek-chat` (DeepSeek-V3)
- Temperature：`0` (保证输出稳定)
- Max tokens：`1500`

### 4.5 心跳保活 (`backend/core/heartbeat.py`)

- 每 5 分钟访问一次 `GET /api/health`
- 使用 `asyncio` 后台任务
- 仅打印日志，不干扰主服务

---

## 五、前端核心组件设计

### 5.1 页面路由

| 路由 | 页面 | 功能 |
|-----|------|------|
| `/` | 首页 | URL 输入框 + 最近分析快捷入口 |
| `/analyze/[id]` | 结果页 | 雷达图 + 五维详情 + AI 报告 + 建议列表 |
| `/history` | 历史页 | 表格展示，支持按域名筛选 |

### 5.2 组件规格

**UrlInput.tsx**
- 输入框 + 提交按钮
- URL 格式校验
- Loading 状态（分析中约需 5-15 秒）
- 提交后跳转 `/analyze/{id}`

**ScoreRadar.tsx**
- 使用 `recharts` 的 RadarChart
- 五维数据：`semantic`, `entity`, `citation`, `qa`, `tech`
- 显示总分于中心

**AIReport.tsx**
- 展示 `ai_summary`（高亮显示）
- 展示 `ai_gaps`（红色警告样式列表）
- 展示 `ai_suggestions`（优先级排序，带颜色标签）

**HistoryTable.tsx**
- 表格列：时间、域名、标题、总分、操作
- 点击跳转结果页
- 空状态提示

### 5.3 API 封装 (`frontend/lib/api.ts`)

```typescript
// 通过环境变量切换本地/远程
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function analyzeUrl(url: string) { ... }
export async function getAnalysis(id: string) { ... }
export async function getHistory() { ... }
```

---

## 六、依赖清单

### 后端 (`backend/requirements.txt`)

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
httpx==0.27.0
readability-lxml==0.8.1
playwright==1.48.0
pydantic==2.9.0
python-multipart==0.0.12
aiosqlite==0.20.0
```

### 前端 (`frontend/package.json` 关键依赖)

```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "recharts": "^2.12.0",
    "tailwind-merge": "^2.5.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "@types/react": "^18.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## 七、在 Cursor / Claude Code 中的实现策略

### 7.1 推荐工作流

**阶段 1：后端骨架（Claude Code 擅长）**
```bash
# 在 Claude Code 中执行
mkdir -p geoscope/backend && cd geoscope/backend
# 然后要求 Claude Code 根据本方案生成完整后端
```

**阶段 2：前端界面（Cursor 擅长）**
```bash
# 在 Cursor 中打开 frontend 目录
# 使用 Composer 功能生成组件
```

**阶段 3：联调与 Prompt 调优（两者结合）**

### 7.2 给 AI 工具的 Prompt 模板

**Prompt 1：生成后端骨架**
```
请根据以下规格，生成一个完整的 FastAPI 后端项目：

1. 使用 Python 3.11 + FastAPI + SQLite (aiosqlite)
2. 数据库表结构见 [粘贴 init_db.sql]
3. Pydantic 模型见 [粘贴 schemas.py]
4. 需要实现以下路由：
   - POST /api/analyze: 接收 URL，调用爬虫 + 评分 + AI，返回分析 ID
   - GET /api/analysis/{id}: 返回完整分析结果
   - GET /api/history: 返回最近 20 条记录
   - GET /api/health: 返回 {"status": "ok"}

5. 爬虫模块要求：
   - 第一层用 httpx + readability-lxml
   - 第二层降级用 playwright (headless)
   - 提取 title 和正文，清理 HTML，限制长度 8000 字

6. 评分模块要求：
   - 本地规则引擎，零 AI 调用
   - 五维评分：semantic_clarity, entity_completeness, citation_credibility, qa_friendly, tech_markup
   - 具体规则：[粘贴评分规则表]

7. AI 模块要求：
   - 调用 DeepSeek API (base_url="https://api.deepseek.com", model="deepseek-chat")
   - 使用 Prompt 模板：[粘贴 Prompt]
   - 结果缓存到 ai_cache 表，指纹 MD5(content[:1000])
   - 正文截断 3000 字

8. 启动时自动执行 init_db.sql 初始化数据库
9. 配置 CORS 允许所有来源
10. 添加心跳保活任务

请生成所有文件，并确保可以直接 `uvicorn main:app --reload` 运行。
```

**Prompt 2：生成前端首页**
```
请生成一个 Next.js 14 (App Router) 页面：

文件：frontend/app/page.tsx

功能：
1. 居中布局，大标题 "GEOScope - AI 搜索引擎可见性分析"
2. 副标题："检测你的网页在 ChatGPT / Perplexity / Kimi 中的可引用性"
3. URL 输入框：
   - 占位符："输入文章 URL，如 https://example.com/blog/post"
   - 提交按钮："开始分析"
   - 校验 URL 格式
   - Loading 状态显示"正在抓取与 AI 分析..."
4. 提交后调用 POST {API_BASE}/api/analyze
5. 成功响应后跳转到 /analyze/{id}
6. 下方展示最近 3 条分析历史（调用 GET {API_BASE}/api/history）
7. 使用 Tailwind CSS，风格简洁专业，主色调 slate/indigo

环境变量 API_BASE 通过 process.env.NEXT_PUBLIC_API_URL 读取
```

**Prompt 3：生成结果页**
```
请生成 Next.js 结果页：frontend/app/analyze/[id]/page.tsx

功能：
1. 通过 params.id 获取分析 ID
2. 客户端调用 GET {API_BASE}/api/analysis/{id}
3. 页面分三区块：
   
   区块 A - 头部：
   - 页面标题、域名、分析时间
   - 总分大数字显示 (0-100)
   
   区块 B - 五维评分：
   - 使用 recharts RadarChart 展示雷达图
   - 五个维度：语义清晰度、实体完整性、引用可信度、问答友好度、技术标记
   - 每个维度显示分数和简短说明
   
   区块 C - AI 洞察：
   - AI 摘要（引用样式高亮）
   - 知识缺口列表（红色警告图标）
   - 优化建议列表（按优先级 1/2/3 分颜色标签：红/黄/绿）
   
4. 加载状态用骨架屏
5. 错误状态显示"分析失败，请重试"
6. 底部有"重新分析"和"查看历史"按钮
7. 响应式布局，移动端适配
```

**Prompt 4：生成历史记录页**
```
请生成历史记录页：frontend/app/history/page.tsx

功能：
1. 调用 GET {API_BASE}/api/history
2. 表格展示：
   - 列：时间、域名、标题、总分、操作
   - 总分用颜色区分：>=80 绿色，60-80 黄色，<<60 红色
   - 操作列有"查看详情"按钮，跳转 /analyze/{id}
3. 支持按域名筛选（简单输入框过滤）
4. 空状态：显示"暂无分析记录，去首页开始"
5. 使用 Tailwind，表格样式简洁
```

### 7.3 开发顺序建议

| 顺序 | 模块 | 工具 | 预计时间 |
|-----|------|------|---------|
| 1 | 后端路由 + SQLite | Claude Code | 30 min |
| 2 | 爬虫模块 (httpx) | Claude Code | 20 min |
| 3 | GEO 评分引擎 | Claude Code | 30 min |
| 4 | AI 代理 + Prompt | Claude Code | 30 min |
| 5 | Playwright 降级 | Claude Code | 15 min |
| 6 | 前端首页 | Cursor | 20 min |
| 7 | 前端结果页 | Cursor | 30 min |
| 8 | 前端历史页 | Cursor | 15 min |
| 9 | API 联调 | 两者 | 20 min |
| 10 | Prompt 调优 | 手动 | 40 min |
| **总计** | | | **~4 小时** |

---

## 八、关键配置片段

### 8.1 Next.js 配置（当前实现）

```javascript
// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
}
module.exports = nextConfig
```

> 说明：`/analyze/[id]` 属于动态路由，和 `output: 'export'` 的纯静态导出模式不兼容（需要预生成所有 `id`）。当前实现使用常规 Next.js 构建方式，更适合演示“提交任务→轮询结果”的真实产品链路。

### 8.2 一键启动脚本

```bash
#!/bin/bash
# start.sh
set -e

echo "🚀 GEOScope 启动..."

# 后端
cd backend
source venv/bin/activate 2>/dev/null || echo "请确保已创建 venv: python -m venv venv"
python init_db.py 2>/dev/null || true
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ 后端 PID: $BACKEND_PID"

# 前端
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端 PID: $FRONTEND_PID"

echo ""
echo "本地访问: http://localhost:3000"
echo "如需公网: cloudflared tunnel --url http://localhost:8000"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
```

### 8.3 .gitignore

```
# 根目录
**/__pycache__
**/.venv
**/venv
**/.env
backend/data/*.db
backend/data/*.db-journal
frontend/dist/
frontend/.next/
frontend/node_modules/
*.log
```

---

## 九、面试演示检查清单

```markdown
□ 运行 ./start.sh，确认前后端启动无报错
□ 浏览器访问 localhost:3000，确认首页渲染
□ 输入一个真实 URL（建议用自己的博客或知名技术文章）
□ 确认分析完成时间 < 15 秒
□ 结果页检查：
   □ 雷达图正常显示 5 个维度
   □ AI 摘要可读，不是胡言乱语
   □ 建议列表有 3 条，带优先级
□ 历史记录页显示刚分析的记录
□ 关闭前端，直接访问 localhost:8000/docs 确认 Swagger UI 正常
□ 测试重复分析同一 URL，确认缓存生效（第二次更快）
□ 准备 2-3 个不同领域的 URL（技术博客、产品页、新闻）
```

---

## 十、给 AI 的终极 Prompt（直接复制使用）

如果你只想发一个 Prompt 让 AI 生成整个项目骨架，用这个：

```
你是一个全栈工程师。请帮我生成一个名为 GEOScope 的项目，用于分析网页在 AI 搜索引擎中的可见性。

项目结构：
geoscope/
├── backend/ (Python FastAPI + SQLite)
│   ├── main.py (路由: POST /api/analyze, GET /api/analysis/{id}, GET /api/history, GET /api/health)
│   ├── core/fetcher.py (爬虫: httpx优先，playwright降级)
│   ├── core/geo_scorer.py (五维本地评分: semantic/entity/citation/qa/tech)
│   ├── core/ai_analyzer.py (DeepSeek API代理，本地缓存7天)
│   └── models/schemas.py (Pydantic模型)
├── frontend/ (Next.js 14 App Router + Tailwind + Recharts)
│   ├── app/page.tsx (URL输入)
│   ├── app/analyze/[id]/page.tsx (雷达图+AI报告)
│   └── app/history/page.tsx (历史表格)

关键要求：
1. 后端启动时自动初始化 SQLite (data/geoscope.db)
2. 爬虫提取正文限制8000字，AI分析截断3000字
3. AI Prompt要求输出JSON: {summary, gaps[], suggestions[{priority,issue,fix}]}
4. 前端静态导出配置，API地址通过 NEXT_PUBLIC_API_URL 环境变量
5. CORS允许所有来源

请生成所有文件的完整代码，确保可以直接运行。
```
