# GEOScope 三个迭代（面试最加分、改动最小）

> 每个迭代都能单独演示：你可以逐个讲“我先解决什么问题、为什么、怎么验证”。

## Iteration 1：安全 + 可观测（Quick Wins）

**做了什么**
- SSRF 基础防护：默认禁止访问 localhost/内网地址（可通过环境变量放开）。
- CORS：默认只允许 `http://localhost:3000`，避免 `* + credentials` 的常见坑。
- 可观测性：响应带 `X-Request-ID`、`X-Response-Time-ms`；新增 `/api/stats` 查看运行期指标与 DB 计数。

**怎么演示**
- 访问 `GET /api/stats`：展示分析次数、AI 缓存命中/未命中、抓取方式分布等。
- 提交一个内网 URL（例如 `http://127.0.0.1`）：展示被拒绝（SSRF 防护）。

**环境变量**
- `GEOSCOPE_CORS_ORIGINS`：逗号分隔（默认 `http://localhost:3000`，可设 `*`）。
- `GEOSCOPE_ALLOW_PRIVATE_NETWORKS=true`：允许抓取内网地址（仅本地调试建议）。

## Iteration 2：异步任务（更稳、更贴近真实产品）

**做了什么**
- `POST /api/analyze` 立刻返回 `{id}`，后端后台跑“抓取 + 评分 + AI”。
- `/api/analysis/{id}` 返回 `status`：`queued/running/done/error`。
- 前端结果页自动轮询直到 `done` 或 `error`。
- DB 自动迁移：启动时给 `analyses` 表补齐 `status/error/updated_at` 字段（不要求手动重建 DB）。

**怎么演示**
- 提交 URL 后，立刻跳结果页：先看到 `queued/running`，随后自动变为 `done` 并展示雷达图与 AI 建议。

**环境变量**
- `GEOSCOPE_MAX_CONCURRENT_ANALYZE`：后台并发（默认 `2`）。

## Iteration 3：抓取资源控制 + 评分证据（解释性更强）

**做了什么**
- Playwright 抓取加入资源拦截：默认不拉图片/字体/媒体，降低内存与耗时。
- 评分输出“命中证据”（signals），结果页可展开查看，便于解释“为什么给这个分”。
- DB 自动迁移：给 `analyses` 表补齐 `score_evidence` 字段。

**怎么演示**
- 在结果页展开“评分证据”：展示如 `has_h1`、`unique_links`、`has_jsonld_or_schemaorg` 等信号。
- 用正文抽取困难的页面：观察抓取方式可能从 `httpx` 降级到 `playwright`，并在 `/api/stats` 里看到分布变化。

**环境变量**
- `GEOSCOPE_MAX_CONCURRENT_PLAYWRIGHT`：Playwright 并发（默认 `1`）。

**Playwright 首次使用说明**
- 若出现 `Executable doesn't exist ... ms-playwright/.../Chromium`，在 `backend` 虚拟环境中执行：`python -m playwright install chromium`
