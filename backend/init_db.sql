-- 分析主表
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT,
    domain TEXT,
    client_id TEXT,
    content_length INTEGER,

    -- 任务状态（迭代 2：异步任务）
    status TEXT DEFAULT 'done',
    error TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 五维评分 (0-100)
    semantic_clarity INTEGER DEFAULT 0,
    entity_completeness INTEGER DEFAULT 0,
    citation_credibility INTEGER DEFAULT 0,
    qa_friendly INTEGER DEFAULT 0,
    tech_markup INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,

    -- 评分证据（JSON）
    score_evidence TEXT,

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
CREATE INDEX IF NOT EXISTS idx_analyses_client_created ON analyses(client_id, created_at);
CREATE INDEX IF NOT EXISTS idx_ai_cache_created ON ai_cache(created_at);
