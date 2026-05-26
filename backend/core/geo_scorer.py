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
    evidence: dict


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def score(content: str, raw_html: Optional[str] = None) -> GeoScoreResult:
    semantic, ev_sem = _score_semantic(content, raw_html)
    entity, ev_ent = _score_entity(content)
    citation, ev_cit = _score_citation(content, raw_html)
    qa, ev_qa = _score_qa(content)
    tech, ev_tech = _score_tech(raw_html or "")
    total = round((semantic + entity + citation + qa + tech) / 5)
    return GeoScoreResult(
        semantic_clarity=semantic,
        entity_completeness=entity,
        citation_credibility=citation,
        qa_friendly=qa,
        tech_markup=tech,
        total_score=total,
        evidence={
            "semantic_clarity": ev_sem,
            "entity_completeness": ev_ent,
            "citation_credibility": ev_cit,
            "qa_friendly": ev_qa,
            "tech_markup": ev_tech,
        },
    )


def _score_semantic(content: str, raw_html: Optional[str]) -> tuple[int, dict]:
    score = 0
    evidence: dict = {}

    has_h1 = bool(raw_html and re.search(r"<h1[^>]*>", raw_html, flags=re.IGNORECASE))
    has_h2_6 = bool(raw_html and re.search(r"<h[2-6][^>]*>", raw_html, flags=re.IGNORECASE))
    evidence["has_h1"] = has_h1
    evidence["has_h2_6"] = has_h2_6

    if has_h1:
        score += 35
    if has_h2_6:
        score += 25

    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    if lines:
        avg_len = sum(len(ln) for ln in lines) / len(lines)
        evidence["avg_line_len"] = round(avg_len, 1)
        if avg_len <= 200:
            score += 20
        short_heading_like = sum(1 for ln in lines if len(ln) <= 40)
        evidence["short_heading_like_lines"] = short_heading_like
        if short_heading_like >= 4:
            score += 20

    paras = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
    if paras:
        avg_para = sum(len(p) for p in paras) / len(paras)
        evidence["avg_para_len"] = round(avg_para, 1)
        if avg_para <= 200:
            score += 20

    return _clamp(score), evidence


def _score_entity(content: str) -> tuple[int, dict]:
    score = 0
    evidence: dict = {}

    has_definition = bool(
        re.search(r"[\u4e00-\u9fffA-Za-z0-9_]{2,20}\s*是\s*[\u4e00-\u9fffA-Za-z0-9_]{2,80}", content)
    )
    has_parentheses_explain = bool(re.search(r"[（(][^）)]{2,60}[）)]", content))
    has_acronym_expand = bool(
        re.search(r"\b[A-Z]{2,}\b\s*(?:\(|（)[^）)]{2,60}(?:\)|）)", content)
    )
    evidence["has_definition_pattern"] = has_definition
    evidence["has_parentheses_explain"] = has_parentheses_explain
    evidence["has_acronym_expand"] = has_acronym_expand

    if has_definition:
        score += 50
    if has_parentheses_explain:
        score += 30
    if has_acronym_expand:
        score += 20

    return _clamp(score), evidence


def _score_citation(content: str, raw_html: Optional[str]) -> tuple[int, dict]:
    text = (raw_html or "") + "\n" + content
    score = 0
    evidence: dict = {}

    has_author = bool(re.search(r"(作者|Author|By\s+[A-Z][a-z]+)", text, flags=re.IGNORECASE))
    has_date = bool(re.search(r"\b20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}", text))
    evidence["has_author"] = has_author
    evidence["has_date"] = has_date

    if has_author:
        score += 40
    if has_date:
        score += 30

    links = re.findall(r"https?://[^\s)]+", text)
    evidence["unique_links"] = len(set(links))
    if len(set(links)) >= 2:
        score += 30
    elif len(set(links)) == 1:
        score += 15

    return _clamp(score), evidence


def _score_qa(content: str) -> tuple[int, dict]:
    score = 0
    lower = content.lower()
    evidence: dict = {}

    has_faq = ("faq" in lower) or ("常见问题" in content)
    evidence["has_faq"] = has_faq
    if has_faq:
        score += 50

    questions = sum(
        1
        for pat in [r"什么是", r"如何", r"为什么", r"怎么", r"Q[:：]"]
        if re.search(pat, content, flags=re.IGNORECASE)
    )
    evidence["question_patterns_hit"] = questions
    if questions >= 2:
        score += 30
    elif questions == 1:
        score += 15

    has_conclusion = bool(re.search(r"(结论|总结|TL;DR|答案[:：])", content, flags=re.IGNORECASE))
    evidence["has_conclusion"] = has_conclusion
    if has_conclusion:
        score += 20

    return _clamp(score), evidence


def _score_tech(raw_html: str) -> tuple[int, dict]:
    score = 0
    evidence: dict = {}
    if not raw_html:
        return 0, evidence

    has_jsonld = bool(
        re.search(r'type=["\']application/ld\+json["\']', raw_html, flags=re.IGNORECASE)
        or "schema.org" in raw_html
    )
    has_og = bool(re.search(r'property=["\']og:', raw_html, flags=re.IGNORECASE) or re.search(r'name=["\']twitter:', raw_html, flags=re.IGNORECASE))
    has_canonical = bool(re.search(r'rel=["\']canonical["\']', raw_html, flags=re.IGNORECASE))
    evidence["has_jsonld_or_schemaorg"] = has_jsonld
    evidence["has_open_graph_or_twitter"] = has_og
    evidence["has_canonical"] = has_canonical

    if has_jsonld:
        score += 50
    if has_og:
        score += 25
    if has_canonical:
        score += 25

    return _clamp(score), evidence
