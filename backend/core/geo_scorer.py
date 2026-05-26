from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GeoScoreResult:
    semantic_clarity: int
    entity_completeness: int
    citation_credibility: int
    qa_friendly: int
    tech_markup: int
    total_score: int


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def score(content: str, raw_html: Optional[str] = None) -> GeoScoreResult:
    semantic = _score_semantic(content, raw_html)
    entity = _score_entity(content)
    citation = _score_citation(content, raw_html)
    qa = _score_qa(content)
    tech = _score_tech(raw_html or "")
    total = round((semantic + entity + citation + qa + tech) / 5)
    return GeoScoreResult(
        semantic_clarity=semantic,
        entity_completeness=entity,
        citation_credibility=citation,
        qa_friendly=qa,
        tech_markup=tech,
        total_score=total,
    )


def _score_semantic(content: str, raw_html: Optional[str]) -> int:
    score = 0

    if raw_html and re.search(r"<h1[^>]*>", raw_html, flags=re.IGNORECASE):
        score += 35
    if raw_html and re.search(r"<h[2-6][^>]*>", raw_html, flags=re.IGNORECASE):
        score += 25

    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    if lines:
        avg_len = sum(len(ln) for ln in lines) / len(lines)
        if avg_len <= 200:
            score += 20
        short_heading_like = sum(1 for ln in lines if len(ln) <= 40)
        if short_heading_like >= 4:
            score += 20

    paras = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
    if paras:
        avg_para = sum(len(p) for p in paras) / len(paras)
        if avg_para <= 200:
            score += 20

    return _clamp(score)


def _score_entity(content: str) -> int:
    score = 0

    if re.search(r"[\u4e00-\u9fffA-Za-z0-9_]{2,20}\s*是\s*[\u4e00-\u9fffA-Za-z0-9_]{2,80}", content):
        score += 50
    if re.search(r"[（(][^）)]{2,60}[）)]", content):
        score += 30
    if re.search(r"\b[A-Z]{2,}\b\s*(?:\(|（)[^）)]{2,60}(?:\)|）)", content):
        score += 20

    return _clamp(score)


def _score_citation(content: str, raw_html: Optional[str]) -> int:
    text = (raw_html or "") + "\n" + content
    score = 0

    if re.search(r"(作者|Author|By\s+[A-Z][a-z]+)", text, flags=re.IGNORECASE):
        score += 40
    if re.search(r"\b20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}", text):
        score += 30

    links = re.findall(r"https?://[^\s)]+", text)
    if len(set(links)) >= 2:
        score += 30
    elif len(set(links)) == 1:
        score += 15

    return _clamp(score)


def _score_qa(content: str) -> int:
    score = 0
    lower = content.lower()

    if "faq" in lower or "常见问题" in content:
        score += 50

    questions = sum(
        1
        for pat in [r"什么是", r"如何", r"为什么", r"怎么", r"Q[:：]"]
        if re.search(pat, content, flags=re.IGNORECASE)
    )
    if questions >= 2:
        score += 30
    elif questions == 1:
        score += 15

    if re.search(r"(结论|总结|TL;DR|答案[:：])", content, flags=re.IGNORECASE):
        score += 20

    return _clamp(score)


def _score_tech(raw_html: str) -> int:
    score = 0
    if not raw_html:
        return 0

    if re.search(r'type=["\']application/ld\+json["\']', raw_html, flags=re.IGNORECASE) or "schema.org" in raw_html:
        score += 50
    if re.search(r'property=["\']og:', raw_html, flags=re.IGNORECASE) or re.search(r'name=["\']twitter:', raw_html, flags=re.IGNORECASE):
        score += 25
    if re.search(r'rel=["\']canonical["\']', raw_html, flags=re.IGNORECASE):
        score += 25

    return _clamp(score)

