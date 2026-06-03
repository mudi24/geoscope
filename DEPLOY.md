# GEOScope - Render 部署指南

## 前置条件

- GitHub 账号（将代码 push 到仓库）
- [Render](https://render.com) 账号（免费注册）
- DeepSeek API Key

---

## ⚠️ 部署前必做：清理敏感信息

`backend/.env` 包含真实 API Key，**不能提交到 git**。
`.gitignore` 已配置忽略 `.env`，但请确认：

```bash
git status  # 确认 backend/.env 不在暂存区
```

如果已经提交过，立即执行：

```bash
git rm --cached backend/.env
git commit -m "chore: remove .env from tracking"
```

---

## 部署步骤

### 第一步：Push 代码到 GitHub

```bash
git add .
git commit -m "feat: add Render deploy config"
git push origin main
```

### 第二步：在 Render 创建 Blueprint

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New** → **Blueprint**
3. 连接你的 GitHub 仓库
4. Render 会自动识别根目录的 `render.yaml`，显示两个服务：
   - `geoscope-backend`（Python Web Service）
   - `geoscope-frontend`（Node Web Service）
5. 点击 **Apply** 开始部署

### 第三步：配置环境变量（必须手动设置）

Blueprint 中标记了 `sync: false` 的变量需要在 Dashboard 手动填写：

#### geoscope-backend 服务

进入 `geoscope-backend` → **Environment** 标签页：

| 变量名 | 值 |
|--------|-----|
| `DEEPSEEK_API_KEY` | `sk-your-actual-key` |
| `GEOSCOPE_CORS_ORIGINS` | 等前端部署完后填写，格式见下方 |

#### geoscope-frontend 服务

进入 `geoscope-frontend` → **Environment** 标签页：

| 变量名 | 值 |
|--------|-----|
| `NEXT_PUBLIC_API_URL` | 等后端部署完后填写，格式见下方 |

### 第四步：获取实际 URL 并互相配置

部署成功后，在各服务的 **Settings** 页面找到分配的 URL：

- 后端 URL 示例：`https://geoscope-backend.onrender.com`
- 前端 URL 示例：`https://geoscope-frontend.onrender.com`

然后：

1. 在 `geoscope-backend` 的 Environment 中设置：
   ```
   GEOSCOPE_CORS_ORIGINS = https://geoscope-frontend.onrender.com
   GEOSCOPE_HEALTHCHECK_URL = https://geoscope-backend.onrender.com/api/health
   ```

2. 在 `geoscope-frontend` 的 Environment 中设置：
   ```
   NEXT_PUBLIC_API_URL = https://geoscope-backend.onrender.com
   ```

3. 每次修改环境变量后，点击 **Manual Deploy** → **Deploy latest commit** 使其生效。

---

## 部署时间预估

| 服务 | 首次构建时间 | 说明 |
|------|------------|------|
| geoscope-backend | ~5-8 分钟 | 主要耗时：安装 Playwright + Chromium (~300MB) |
| geoscope-frontend | ~2-3 分钟 | npm ci + next build |

---

## 免费套餐限制说明

| 限制 | 详情 |
|------|------|
| **休眠** | 15 分钟无流量后自动休眠，首次请求冷启动约 30s-60s |
| **内存** | 512MB RAM。Playwright 每次启动约消耗 150-200MB，与 FastAPI 共用可能偶发 OOM |
| **磁盘** | 临时存储，服务重启后 SQLite 数据库会重置（历史记录丢失） |
| **CPU** | 共享 CPU，高并发下响应变慢 |

**关于内存 OOM 风险**：若 Playwright 导致服务崩溃重启，可在 Dashboard 将 `plan` 从 `free` 升级到 `starter`（$7/月，512MB→2GB）。

---

## 验证部署

```bash
# 替换为你的实际后端 URL
BACKEND=https://geoscope-backend.onrender.com

# 健康检查
curl $BACKEND/api/health

# 提交一次分析（需要先有 client_id）
curl -X POST $BACKEND/api/analyze \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: test" \
  -d '{"url":"https://example.com"}'

# 查看历史
curl $BACKEND/api/history -H "X-Client-Id: test"
```

---

## 常见问题

**Q: 构建时 `playwright install-deps` 失败**

Render 的 Python 运行时是 Debian，`install-deps` 需要 `sudo`，但 Render 构建环境默认有 root 权限，应该可以正常运行。若失败请查看构建日志中的具体 apt 错误。

**Q: 前端报 `Failed to fetch` 或 CORS 错误**

检查 `GEOSCOPE_CORS_ORIGINS` 是否精确匹配前端 URL（含 `https://`，不含末尾 `/`）。

**Q: 分析一直转圈不返回结果**

免费套餐冷启动后 Playwright 初次加载慢。查看后端 Logs 确认是否有 OOM 报错，若有需升级套餐。

**Q: 每次重启历史记录丢失**

这是已知取舍（免费套餐临时磁盘）。如需持久化，在 Render 添加一个 **Disk**（$0.25/GB/月），挂载到 `/opt/render/project/src/data`，并修改 `backend/core/db.py` 中的 DB 路径。

---

## 本地与生产环境切换

本地开发无需改动，照常运行 `./start.sh`。

生产配置全部通过 Render Dashboard 的环境变量管理，不需要修改代码。
