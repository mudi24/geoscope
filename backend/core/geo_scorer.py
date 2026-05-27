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


def build_insights(scores: GeoScoreResult) -> dict[str, dict]:
    """
    输出每个维度的优点/缺点/建议，便于面试演示解释“为什么给这个分、怎么改”。
    """
    ev = scores.evidence or {}
    out: dict[str, dict] = {}

    out["semantic_clarity"] = _insight_semantic(scores.semantic_clarity, ev.get("semantic_clarity") or {})
    out["entity_completeness"] = _insight_entity(scores.entity_completeness, ev.get("entity_completeness") or {})
    out["citation_credibility"] = _insight_citation(scores.citation_credibility, ev.get("citation_credibility") or {})
    out["qa_friendly"] = _insight_qa(scores.qa_friendly, ev.get("qa_friendly") or {})
    out["tech_markup"] = _insight_tech(scores.tech_markup, ev.get("tech_markup") or {})
    return out


def _base(score: int) -> dict:
    return {"score": score, "pros": [], "cons": [], "suggestions": []}


def _insight_semantic(score: int, ev: dict) -> dict:
    it = _base(score)
    if ev.get("has_h1"):
        it["pros"].append("包含 H1 主标题，有利于主题聚焦与可引用片段生成。")
    else:
        it["cons"].append("缺少 H1 主标题或标题结构不明确，AI 更难抓住页面主问题。")
        it["suggestions"].append("补充唯一 H1，标题用“问题/结论式”表述。")

    if ev.get("has_h2_6"):
        it["pros"].append("存在多级小标题，结构化程度较好。")
    else:
        it["cons"].append("小标题较少，内容可能是一大段叙述，难以被问答式引用。")
        it["suggestions"].append("按主题拆成 3-6 个小节（H2/H3），每节先给结论再解释。")

    avg_para = ev.get("avg_para_len")
    if isinstance(avg_para, (int, float)) and avg_para <= 200:
        it["pros"].append("段落长度适中，信息更易被模型切片引用。")
    elif isinstance(avg_para, (int, float)):
        it["cons"].append("段落偏长，容易导致关键句被淹没。")
        it["suggestions"].append("将 >200 字的段落拆分，并在段首加入“结论句”。")

    short_h = ev.get("short_heading_like_lines")
    if isinstance(short_h, int) and short_h >= 4:
        it["pros"].append("有一定的小标题密度，利于生成目录式回答。")
    return it


def _insight_entity(score: int, ev: dict) -> dict:
    it = _base(score)
    if ev.get("has_definition_pattern"):
        it["pros"].append("存在“X 是 …”式定义句，利于 AI 直接引用定义。")
    else:
        it["cons"].append("关键术语缺少明确的定义句，AI 回答时不敢引用或容易误引。")
        it["suggestions"].append("对每个核心概念补一条可引用定义（1-2 句）+ 一个例子。")

    if ev.get("has_parentheses_explain"):
        it["pros"].append("出现括号解释/补充说明，提升上下文完整性。")
    else:
        it["cons"].append("较少看到括号解释或注释信息，缩写/专有名词可能不友好。")
        it["suggestions"].append("首次出现缩写/名词时用括号补全全称或一句解释。")

    if ev.get("has_acronym_expand"):
        it["pros"].append("检测到缩写展开格式，对新读者更友好。")
    return it


def _insight_citation(score: int, ev: dict) -> dict:
    it = _base(score)
    if ev.get("has_author"):
        it["pros"].append("包含作者/署名信息，增强可追溯性。")
    else:
        it["cons"].append("缺少作者/署名信息，引用可信度会打折。")
        it["suggestions"].append("在页首或页尾补充作者/团队/机构信息。")

    if ev.get("has_date"):
        it["pros"].append("包含发布日期/更新时间，有利于时效性判断。")
    else:
        it["cons"].append("缺少日期信息，AI 很难判断内容是否过时。")
        it["suggestions"].append("补充发布时间与最近更新时间（ISO 或常见日期格式）。")

    links = ev.get("unique_links")
    if isinstance(links, int) and links >= 2:
        it["pros"].append("存在多个外部链接，可作为证据链支撑。")
    elif isinstance(links, int) and links == 1:
        it["cons"].append("外部链接偏少，论断可能缺乏支撑。")
        it["suggestions"].append("补充 2-3 个权威外链（论文/标准/官方文档），并在文中标注引用点。")
    else:
        it["cons"].append("未检测到外部链接，AI 通常会降低引用概率。")
        it["suggestions"].append("添加参考资料区（References），至少给 2 个权威来源链接。")
    return it


def _insight_qa(score: int, ev: dict) -> dict:
    it = _base(score)
    if ev.get("has_faq"):
        it["pros"].append("包含 FAQ/常见问题结构，天然适配问答检索。")
    else:
        it["cons"].append("缺少 FAQ/Q&A 结构，问答式引用场景覆盖不足。")
        it["suggestions"].append("新增 3-5 个常见问题（Q/A），每条答案先给一句话结论。")

    hits = ev.get("question_patterns_hit")
    if isinstance(hits, int) and hits >= 2:
        it["pros"].append("存在较多问题式句型（什么是/如何/为什么），更贴近用户 query。")
    elif isinstance(hits, int) and hits == 0:
        it["cons"].append("几乎没有问题式表达，难以覆盖长尾提问。")
        it["suggestions"].append("在小节标题中加入“如何/为什么/什么是”，并给出直接答案段。")

    if ev.get("has_conclusion"):
        it["pros"].append("有总结/结论信号，利于 AI 抽取 TL;DR。")
    else:
        it["cons"].append("缺少显式结论/总结，AI 需要自己归纳，引用稳定性下降。")
        it["suggestions"].append("加一个 TL;DR 区块（3-5 条要点），并在末尾总结关键结论。")
    return it


def _insight_tech(score: int, ev: dict) -> dict:
    it = _base(score)
    if ev.get("has_jsonld_or_schemaorg"):
        it["pros"].append("存在 JSON-LD/Schema.org 结构化数据，有利于机器理解内容类型。")
    else:
        it["cons"].append("缺少 Schema.org/JSON-LD，机器可读性不足。")
        it["suggestions"].append("补充 Article（或 FAQPage）JSON-LD，并填入 headline/datePublished/author。")

    if ev.get("has_open_graph_or_twitter"):
        it["pros"].append("包含 OpenGraph/Twitter Card 元信息，有利于标题/摘要一致性。")
    else:
        it["cons"].append("缺少 OG/Twitter 元信息，分享/抓取时标题摘要可能不稳定。")
        it["suggestions"].append("补齐 og:title/og:description/og:url 以及 twitter:card。")

    if ev.get("has_canonical"):
        it["pros"].append("有 canonical 链接，降低重复内容导致的权威性稀释。")
    else:
        it["cons"].append("缺少 canonical，多个 URL 指向同内容时可能影响权威信号。")
        it["suggestions"].append("为页面添加 canonical 指向首选 URL。")
    return it


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
