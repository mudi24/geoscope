from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from urllib.parse import urlparse
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from core.ai_analyzer import analyze_with_cache, fingerprint_content
from core.db import connect, get_db_path, init_db
from core.fetcher import fetch_url
from core.geo_scorer import score as score_geo
from core.heartbeat import start_heartbeat
from core.rate_limit import RateLimiter
from core.url_safety import UrlSafetyError, validate_public_url
from models.schemas import AnalysisResponse, HistoryItem
from models.schemas import AnalyzeRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = get_db_path()
    await init_db(db_path)
    app.state.db_path = db_path
    app.state.worker_semaphore = asyncio.Semaphore(
        int(os.getenv("GEOSCOPE_MAX_CONCURRENT_ANALYZE", "2"))
    )
    app.state.rate_limiter = RateLimiter(
        int(os.getenv("GEOSCOPE_ANALYZE_PER_MINUTE", "20"))
    )
    app.state.ai_daily_budget: dict[tuple[str, str], int] = {}
    stop_event, hb_task = start_heartbeat()
    yield
    stop_event.set()
    hb_task.cancel()


app = FastAPI(title="GEOScope API", version="0.1.0", lifespan=lifespan)

cors_origins = os.getenv("GEOSCOPE_CORS_ORIGINS", "http://localhost:3000")
allow_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
allow_all = len(allow_origins) == 1 and allow_origins[0] == "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False if allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Response-Time-ms"] = f"{(time.perf_counter() - start) * 1000:.1f}"
    return response


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest, request: Request) -> dict:
    client_id = _get_client_id(request)
    limiter: RateLimiter = app.state.rate_limiter
    ip = (request.client.host if request.client else "unknown").strip()
    if not limiter.allow(f"{client_id}:{ip}"):
        raise HTTPException(status_code=429, detail="rate limited: too many analyze requests")
    url = str(req.url)
    domain = urlparse(url).netloc

    try:
        validate_public_url(url)
    except UrlSafetyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    conn = await connect(app.state.db_path)
    try:
        cur = await conn.execute(
            """
            INSERT INTO analyses (
              url, domain, client_id, status
            ) VALUES (?, ?, ?, ?)
            """,
            (
                url,
                domain,
                client_id,
                "queued",
            ),
        )
        await conn.commit()
        analysis_id = cur.lastrowid
    finally:
        await conn.close()

    asyncio.create_task(_process_analysis(app, analysis_id, url, client_id))

    return {"id": analysis_id}


def _get_client_id(request: Request) -> str:
    require = os.getenv("GEOSCOPE_REQUIRE_CLIENT_ID", "true").lower() in {"1", "true", "yes"}
    client_id = request.headers.get("x-client-id")
    if client_id:
        return client_id.strip()
    if require:
        raise HTTPException(status_code=400, detail="missing X-Client-Id header")
    return os.getenv("GEOSCOPE_DEFAULT_CLIENT_ID", "public")


async def _process_analysis(app: FastAPI, analysis_id: int, url: str, client_id: str) -> None:
    sem: asyncio.Semaphore = app.state.worker_semaphore
    cache_hit = False
    external_called = False
    fetched_method = "unknown"
    async with sem:
        t0 = time.perf_counter()
        conn = await connect(app.state.db_path)
        try:
            await conn.execute(
                "UPDATE analyses SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                ("running", analysis_id),
            )
            await conn.commit()

            fetched = await fetch_url(url)
            fetched_method = fetched.method
            scores = score_geo(fetched.content, fetched.raw_html)

            # 先只查缓存；未命中再考虑是否允许调用外部 AI（防滥用/配额）
            ai_result, cache_hit, _ = await analyze_with_cache(
                conn, url, fetched.content, allow_external=False
            )
            if not cache_hit:
                max_daily = int(os.getenv("GEOSCOPE_AI_CALLS_PER_DAY", "30"))
                day_key = datetime.utcnow().date().isoformat()
                used = app.state.ai_daily_budget.get((day_key, client_id), 0)
                allow_external = used < max_daily
                ai_result, cache_hit, external_called = await analyze_with_cache(
                    conn, url, fetched.content, allow_external=allow_external
                )
                if external_called:
                    app.state.ai_daily_budget[(day_key, client_id)] = used + 1
            fp = fingerprint_content(fetched.content)

            await conn.execute(
                """
                UPDATE analyses SET
                  title=?,
                  content_length=?,
                  semantic_clarity=?,
                  entity_completeness=?,
                  citation_credibility=?,
                  qa_friendly=?,
                  tech_markup=?,
                  total_score=?,
                  score_evidence=?,
                  ai_summary=?,
                  ai_gaps=?,
                  ai_suggestions=?,
                  fetch_method=?,
                  content_fingerprint=?,
                  status='done',
                  error=NULL,
                  updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    fetched.title,
                    fetched.length,
                    scores.semantic_clarity,
                    scores.entity_completeness,
                    scores.citation_credibility,
                    scores.qa_friendly,
                    scores.tech_markup,
                    scores.total_score,
                    json.dumps(scores.evidence, ensure_ascii=False),
                    ai_result.get("summary", ""),
                    json.dumps(ai_result.get("gaps", []), ensure_ascii=False),
                    json.dumps(ai_result.get("suggestions", []), ensure_ascii=False),
                    fetched.method,
                    fp,
                    analysis_id,
                ),
            )
            await conn.commit()
        except Exception as e:
            try:
                await conn.execute(
                    "UPDATE analyses SET status='error', error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (str(e), analysis_id),
                )
                await conn.commit()
            except Exception:
                pass
        finally:
            await conn.close()

        metrics = getattr(app.state, "metrics", None)
        if metrics is None:
            metrics = app.state.metrics = {
                "analyze_total": 0,
                "ai_cache_hit": 0,
                "ai_cache_miss": 0,
                "ai_external_called": 0,
                "fetch_method": {},
            }
        metrics["analyze_total"] += 1
        metrics["ai_cache_hit" if cache_hit else "ai_cache_miss"] += 1
        if external_called:
            metrics["ai_external_called"] += 1
        metrics["fetch_method"][fetched_method] = metrics["fetch_method"].get(fetched_method, 0) + 1
        metrics["last_analyze_ms"] = round((time.perf_counter() - t0) * 1000)


@app.get("/api/stats")
async def stats(request: Request) -> dict:
    client_id = _get_client_id(request)
    metrics = getattr(app.state, "metrics", None) or {}
    conn = await connect(app.state.db_path)
    try:
        cur = await conn.execute("SELECT COUNT(1) AS c FROM analyses WHERE client_id = ?", (client_id,))
        row = await cur.fetchone()
        total = int(row["c"]) if row else 0
        cur2 = await conn.execute("SELECT COUNT(1) AS c FROM ai_cache")
        row2 = await cur2.fetchone()
        cache_total = int(row2["c"]) if row2 else 0
    finally:
        await conn.close()
    day_key = datetime.utcnow().date().isoformat()
    used = app.state.ai_daily_budget.get((day_key, client_id), 0)
    max_daily = int(os.getenv("GEOSCOPE_AI_CALLS_PER_DAY", "30"))
    return {
        "db": {"analyses": total, "ai_cache": cache_total},
        "runtime": metrics,
        "ai_budget": {"date": day_key, "used": used, "limit": max_daily, "remaining": max(0, max_daily - used)},
    }


@app.get("/api/history", response_model=list[HistoryItem])
async def history(request: Request) -> list[HistoryItem]:
    client_id = _get_client_id(request)
    conn = await connect(app.state.db_path)
    try:
        cur = await conn.execute(
            """
            SELECT id, url, title, status, total_score, created_at
            FROM analyses
            WHERE client_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT 20
            """
            ,
            (client_id,),
        )
        rows = await cur.fetchall()
    finally:
        await conn.close()

    items: list[HistoryItem] = []
    for row in rows:
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        items.append(
            HistoryItem(
                id=row["id"],
                url=row["url"],
                title=row["title"],
                status=row["status"] or "done",
                total_score=row["total_score"] or 0,
                created_at=created_at,
            )
        )
    return items


@app.get("/api/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: int, request: Request) -> AnalysisResponse:
    client_id = _get_client_id(request)
    conn = await connect(app.state.db_path)
    try:
        cur = await conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND client_id = ?",
            (analysis_id, client_id),
        )
        row = await cur.fetchone()
    finally:
        await conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="analysis not found")

    created_at = row["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

    gaps = json.loads(row["ai_gaps"] or "[]")
    suggestions = json.loads(row["ai_suggestions"] or "[]")
    score_evidence = None
    try:
        if row["score_evidence"]:
            score_evidence = json.loads(row["score_evidence"])
    except Exception:
        score_evidence = None

    return AnalysisResponse(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        domain=row["domain"],
        status=row["status"] or "done",
        error=row["error"],
        scores={
            "semantic_clarity": row["semantic_clarity"] or 0,
            "entity_completeness": row["entity_completeness"] or 0,
            "citation_credibility": row["citation_credibility"] or 0,
            "qa_friendly": row["qa_friendly"] or 0,
            "tech_markup": row["tech_markup"] or 0,
            "total_score": row["total_score"] or 0,
        },
        score_evidence=score_evidence,
        ai_result={
            "summary": row["ai_summary"] or "",
            "gaps": gaps,
            "suggestions": suggestions,
        },
        fetch_method=row["fetch_method"] or ("pending" if (row["status"] or "") != "done" else "httpx"),
        created_at=created_at,
    )
import os
import time
import uuid
