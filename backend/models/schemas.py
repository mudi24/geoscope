from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class GeoScores(BaseModel):
    semantic_clarity: int
    entity_completeness: int
    citation_credibility: int
    qa_friendly: int
    tech_markup: int
    total_score: int


class AISuggestion(BaseModel):
    priority: int
    issue: str
    fix: str


class AIResult(BaseModel):
    summary: str
    gaps: List[str]
    suggestions: List[AISuggestion]


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

