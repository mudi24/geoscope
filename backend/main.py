from __future__ import annotations

import json
from urllib.parse import urlparse
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.ai_analyzer import analyze_with_cache, fingerprint_content
from core.db import connect, get_db_path, init_db
from core.fetcher import fetch_url
from core.geo_scorer import score as score_geo
from core.heartbeat import start_heartbeat
from models.schemas import AnalysisResponse, HistoryItem
from models.schemas import AnalyzeRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = get_db_path()
    await init_db(db_path)
    app.state.db_path = db_path
    stop_event, hb_task = start_heartbeat()
    yield
    stop_event.set()
    hb_task.cancel()


app = FastAPI(title="GEOScope API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> dict:
    url = str(req.url)
    domain = urlparse(url).netloc

    fetched = await fetch_url(url)
    scores = score_geo(fetched.content, fetched.raw_html)

    conn = await connect(app.state.db_path)
    try:
        ai_result = await analyze_with_cache(conn, url, fetched.content)
        fp = fingerprint_content(fetched.content)

        cur = await conn.execute(
            """
            INSERT INTO analyses (
              url, title, domain, content_length,
              semantic_clarity, entity_completeness, citation_credibility, qa_friendly, tech_markup, total_score,
              ai_summary, ai_gaps, ai_suggestions,
              fetch_method, content_fingerprint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                fetched.title,
                domain,
                fetched.length,
                scores.semantic_clarity,
                scores.entity_completeness,
                scores.citation_credibility,
                scores.qa_friendly,
                scores.tech_markup,
                scores.total_score,
                ai_result.get("summary", ""),
                json.dumps(ai_result.get("gaps", []), ensure_ascii=False),
                json.dumps(ai_result.get("suggestions", []), ensure_ascii=False),
                fetched.method,
                fp,
            ),
        )
        await conn.commit()
        analysis_id = cur.lastrowid
    finally:
        await conn.close()

    return {"id": analysis_id}


@app.get("/api/history", response_model=list[HistoryItem])
async def history() -> list[HistoryItem]:
    conn = await connect(app.state.db_path)
    try:
        cur = await conn.execute(
            """
            SELECT id, url, title, total_score, created_at
            FROM analyses
            ORDER BY datetime(created_at) DESC
            LIMIT 20
            """
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
                total_score=row["total_score"] or 0,
                created_at=created_at,
            )
        )
    return items


@app.get("/api/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: int) -> AnalysisResponse:
    conn = await connect(app.state.db_path)
    try:
        cur = await conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
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

    return AnalysisResponse(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        domain=row["domain"],
        scores={
            "semantic_clarity": row["semantic_clarity"] or 0,
            "entity_completeness": row["entity_completeness"] or 0,
            "citation_credibility": row["citation_credibility"] or 0,
            "qa_friendly": row["qa_friendly"] or 0,
            "tech_markup": row["tech_markup"] or 0,
            "total_score": row["total_score"] or 0,
        },
        ai_result={
            "summary": row["ai_summary"] or "",
            "gaps": gaps,
            "suggestions": suggestions,
        },
        fetch_method=row["fetch_method"] or "httpx",
        created_at=created_at,
    )
