from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------

# Project-bundled font dir (downloaded by build.sh into backend/fonts/)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_DIR = os.path.join(_BACKEND_DIR, "fonts")

_FONT_CANDIDATES = [
    # 1. Project fonts/ directory (build.sh download fallback)
    os.path.join(_FONT_DIR, "NotoSansCJK-Regular.ttc"),
    os.path.join(_FONT_DIR, "NotoSansSC-Regular.otf"),
    os.path.join(_FONT_DIR, "NotoSansSC-Regular.ttf"),
    # 2. apt fonts-noto-cjk (Render / Ubuntu / Debian)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    # 3. apt fonts-wqy-zenhei (fallback, smaller package)
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
    # 4. macOS system fonts (local dev)
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]
_FONT_NAME = "Helvetica"  # fallback (ASCII only)


def _register_font() -> str:
    global _FONT_NAME
    if _FONT_NAME != "Helvetica":
        return _FONT_NAME
    for path in _FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        # Try with subfontIndex=0 first (required for .ttc), then without
        for kwargs in ({"subfontIndex": 0}, {}):
            try:
                pdfmetrics.registerFont(TTFont("CJK", path, **kwargs))
                _FONT_NAME = "CJK"
                print(f"[pdf_export] CJK font registered: {path}", flush=True)
                return _FONT_NAME
            except Exception:
                continue
    print(
        f"[pdf_export] WARNING: No CJK font found. Searched:\n"
        + "\n".join(f"  {p}" for p in _FONT_CANDIDATES),
        flush=True,
    )
    return _FONT_NAME


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
def _styles(font: str):
    base = getSampleStyleSheet()
    def s(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], fontName=font, **kw)

    return {
        "title":    s("title",    fontSize=20, textColor=colors.white, spaceAfter=4),
        "subtitle": s("subtitle", fontSize=10, textColor=colors.HexColor("#c7d2fe"), spaceAfter=2),
        "h2":       s("h2",       fontSize=13, textColor=colors.HexColor("#1e1b4b"),
                       spaceBefore=10, spaceAfter=4, leading=18),
        "body":     s("body",     fontSize=9,  textColor=colors.HexColor("#374151"),
                       spaceAfter=3, leading=14),
        "small":    s("small",    fontSize=8,  textColor=colors.HexColor("#6b7280"),
                       spaceAfter=2, leading=12),
        "label":    s("label",    fontSize=8,  textColor=colors.HexColor("#374151"),
                       leading=12),
        "pro":      s("pro",      fontSize=8,  textColor=colors.HexColor("#065f46"),
                       spaceAfter=1, leading=12),
        "con":      s("con",      fontSize=8,  textColor=colors.HexColor("#92400e"),
                       spaceAfter=1, leading=12),
        "suggest":  s("suggest",  fontSize=8,  textColor=colors.HexColor("#1e3a8a"),
                       spaceAfter=1, leading=12),
        "gap":      s("gap",      fontSize=9,  textColor=colors.HexColor("#b91c1c"),
                       spaceAfter=2, leading=13),
        "fix":      s("fix",      fontSize=8,  textColor=colors.HexColor("#374151"),
                       spaceAfter=2, leading=13),
    }


# ---------------------------------------------------------------------------
# Score bar as a Table row
# ---------------------------------------------------------------------------
def _score_color(score: int) -> str:
    if score >= 80:
        return "#065f46"
    if score >= 60:
        return "#92400e"
    return "#991b1b"

def _score_bar_table(label: str, score: int, font: str) -> Table:
    """Single-row table: label | score | bar"""
    bar_total = 90 * mm
    fill_w = max(2 * mm, bar_total * score / 100)
    sc = _score_color(score)

    bar_bg = Table([[""]], colWidths=[bar_total], rowHeights=[5 * mm])
    bar_bg.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#e5e7eb")),
        ("BOX", (0,0), (-1,-1), 0, colors.white),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))

    bar_fill = Table([[""]], colWidths=[fill_w], rowHeights=[5 * mm])
    bar_fill.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor(sc)),
        ("BOX", (0,0), (-1,-1), 0, colors.white),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))

    row = Table(
        [[Paragraph(label, ParagraphStyle("bl", fontName=font, fontSize=9)),
          Paragraph(f'<font color="{sc}"><b>{score}</b></font>',
                    ParagraphStyle("sc", fontName=font, fontSize=10)),
          bar_fill]],
        colWidths=[38*mm, 14*mm, bar_total],
        rowHeights=[7*mm],
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 1),
        ("BOTTOMPADDING", (0,0), (-1,-1), 1),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#f8f8fc")]),
        ("BOX", (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
    ]))
    return row


# ---------------------------------------------------------------------------
# Section header helper
# ---------------------------------------------------------------------------
def _section(title: str, styles: dict, story: list) -> None:
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=2))
    story.append(Paragraph(title, styles["h2"]))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_pdf(data: dict[str, Any]) -> bytes:
    """
    Build a PDF report from an AnalysisResponse-shaped dict.
    Returns raw PDF bytes.
    """
    font = _register_font()
    st = _styles(font)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16*mm, rightMargin=16*mm,
        topMargin=16*mm, bottomMargin=20*mm,
    )

    story: list = []

    # ── Cover header ──────────────────────────────────────────
    # Indigo banner via a 1-row Table with coloured background
    scores = data.get("scores", {})
    total = scores.get("total_score", 0)
    sc_color = _score_color(total)

    title_text = data.get("title") or "（无标题）"
    domain_text = data.get("domain") or ""
    url_text = data.get("url", "")
    created_raw = data.get("created_at", "")
    if isinstance(created_raw, datetime):
        created_str = created_raw.strftime("%Y-%m-%d %H:%M")
    else:
        try:
            created_str = str(created_raw)[:16].replace("T", " ")
        except Exception:
            created_str = ""

    banner = Table(
        [[
            Paragraph("GEOScope 分析报告", st["title"]),
            Paragraph(f'<font color="{sc_color}"><b>{total}</b></font>',
                      ParagraphStyle("big", fontName=font, fontSize=36,
                                     textColor=colors.white, alignment=2)),
        ]],
        colWidths=[120*mm, 54*mm],
        rowHeights=[24*mm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#4f46e5")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (0,-1), 8),
        ("RIGHTPADDING", (-1,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(banner)
    story.append(Spacer(1, 3*mm))

    # Meta info
    meta = f"{domain_text}  ·  {created_str}  ·  {data.get('fetch_method', '')}"
    story.append(Paragraph(meta, st["small"]))
    story.append(Paragraph(f"ID: {data.get('id', '')}  |  {url_text[:80]}", st["small"]))
    story.append(Spacer(1, 2*mm))

    # ── Five dimensions ───────────────────────────────────────
    _section("五维评分", st, story)

    dim_map = [
        ("semantic_clarity",     "语义清晰度", "标题层级 / 段落长度 / 小标题密度"),
        ("entity_completeness",  "实体完整性", "关键术语解释 / 缩写展开"),
        ("citation_credibility", "引用可信度", "作者 / 日期 / 外链可追溯性"),
        ("qa_friendly",          "问答友好度", "FAQ / 结论前置 / 直接答案句式"),
        ("tech_markup",          "技术标记",   "Schema.org / OG / Canonical"),
    ]
    insights = data.get("score_insights") or {}

    for key, label, desc in dim_map:
        score = scores.get(key, 0)
        sc = _score_color(score)

        # ── Score bar row ──
        story.append(_score_bar_table(f"{label}  ({desc})", score, font))
        story.append(Spacer(1, 1 * mm))

        ins = insights.get(key)
        if not ins:
            story.append(Spacer(1, 3 * mm))
            continue

        # Normalise: ins may be a dict (plain) or a Pydantic object
        def _get(d, attr):
            if isinstance(d, dict):
                return d.get(attr) or []
            return getattr(d, attr, None) or []

        pros = _get(ins, "pros")
        cons = _get(ins, "cons")
        sugs = _get(ins, "suggestions")

        if not pros and not cons and not sugs:
            story.append(Spacer(1, 3 * mm))
            continue

        # Build a detail card: 3-column table (pros | cons | suggestions)
        PRO_COLOR  = "#065f46"
        CON_COLOR  = "#92400e"
        SUG_COLOR  = "#1e3a8a"
        HDR_BG     = colors.HexColor("#f0fdf4")   # green-50
        HDR_BG_CON = colors.HexColor("#fff7ed")   # orange-50
        HDR_BG_SUG = colors.HexColor("#eff6ff")   # blue-50

        def _bullet_paras(items, color, prefix):
            ps = ParagraphStyle(
                f"bp_{key}_{prefix}",
                fontName=font, fontSize=7.5,
                textColor=colors.HexColor(color),
                leading=12, spaceAfter=1,
            )
            return [Paragraph(f"{prefix} {item}", ps) for item in items] or [
                Paragraph("—", ParagraphStyle(f"em_{key}_{prefix}",
                          fontName=font, fontSize=7.5,
                          textColor=colors.HexColor("#9ca3af"), leading=12))
            ]

        hdr_style = ParagraphStyle(
            f"hdr_{key}", fontName=font, fontSize=8,
            leading=12, spaceAfter=0,
        )

        detail = Table(
            [
                # Header row
                [
                    Paragraph(f'<font color="{PRO_COLOR}"><b>✓ 优点</b></font>', hdr_style),
                    Paragraph(f'<font color="{CON_COLOR}"><b>✗ 缺点</b></font>', hdr_style),
                    Paragraph(f'<font color="{SUG_COLOR}"><b>→ 建议</b></font>', hdr_style),
                ],
                # Content row
                [
                    [p for p in _bullet_paras(pros, PRO_COLOR, "•")],
                    [p for p in _bullet_paras(cons, CON_COLOR, "•")],
                    [p for p in _bullet_paras(sugs, SUG_COLOR, "→")],
                ],
            ],
            colWidths=[58 * mm, 58 * mm, 58 * mm],
        )
        detail.setStyle(TableStyle([
            # Header backgrounds
            ("BACKGROUND",    (0, 0), (0, 0), HDR_BG),
            ("BACKGROUND",    (1, 0), (1, 0), HDR_BG_CON),
            ("BACKGROUND",    (2, 0), (2, 0), HDR_BG_SUG),
            # Content backgrounds (lighter)
            ("BACKGROUND",    (0, 1), (0, 1), colors.HexColor("#f7fdf9")),
            ("BACKGROUND",    (1, 1), (1, 1), colors.HexColor("#fffcf7")),
            ("BACKGROUND",    (2, 1), (2, 1), colors.HexColor("#f5f9ff")),
            # Borders
            ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
            # Padding
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(detail)
        story.append(Spacer(1, 4 * mm))

    # ── AI Summary ────────────────────────────────────────────
    ai = data.get("ai_result") or {}
    _section("AI 摘要", st, story)
    summary = ai.get("summary") or "（暂无摘要）"
    story.append(Paragraph(summary, st["body"]))

    # ── Gaps ──────────────────────────────────────────────────
    _section("知识缺口", st, story)
    for gap in (ai.get("gaps") or []):
        story.append(Paragraph(f"• {gap}", st["gap"]))

    # ── Suggestions ───────────────────────────────────────────
    _section("优化建议", st, story)
    p_colors = {1: "#991b1b", 2: "#92400e", 3: "#065f46"}
    for s in sorted(ai.get("suggestions") or [], key=lambda x: x.get("priority", 9)):
        pri = s.get("priority", 3)
        pc = p_colors.get(pri, "#374151")
        issue = s.get("issue", "")
        fix = s.get("fix", "")
        story.append(Paragraph(
            f'<font color="{pc}"><b>[P{pri}]</b></font>  {issue}',
            st["body"],
        ))
        story.append(Paragraph(f"    {fix}", st["fix"]))
        story.append(Spacer(1, 1*mm))

    # ── Evidence ──────────────────────────────────────────────
    evidence = data.get("score_evidence") or {}
    if evidence:
        _section("评分证据", st, story)
        DIM_LABELS = {
            "semantic_clarity": "语义清晰度",
            "entity_completeness": "实体完整性",
            "citation_credibility": "引用可信度",
            "qa_friendly": "问答友好度",
            "tech_markup": "技术标记",
        }
        KEY_LABELS = {
            "has_h1": "包含 H1 主标题", "has_h2_6": "包含 H2-H6",
            "avg_line_len": "平均行长度", "avg_para_len": "平均段落长度",
            "has_definition_pattern": "检测到定义句", "has_author": "包含作者信息",
            "has_date": "包含发布日期", "unique_links": "外链数量",
            "has_faq": "包含 FAQ", "has_conclusion": "包含结论信号",
            "has_jsonld_or_schemaorg": "包含 JSON-LD",
            "has_open_graph_or_twitter": "包含 OG/Twitter",
            "has_canonical": "包含 canonical",
        }
        for dim, obj in evidence.items():
            story.append(Paragraph(DIM_LABELS.get(dim, dim), st["label"]))
            if isinstance(obj, dict):
                rows = []
                for k, v in obj.items():
                    lbl = KEY_LABELS.get(k, k)
                    if isinstance(v, bool):
                        val_str = "是" if v else "否"
                        val_color = "#065f46" if v else "#991b1b"
                    else:
                        val_str = str(v) if v is not None else "—"
                        val_color = "#374151"
                    rows.append([
                        Paragraph(lbl, ParagraphStyle("el", fontName=font, fontSize=7.5)),
                        Paragraph(f'<font color="{val_color}">{val_str}</font>',
                                  ParagraphStyle("ev", fontName=font, fontSize=7.5)),
                    ])
                if rows:
                    ev_table = Table(rows, colWidths=[100*mm, 60*mm])
                    ev_table.setStyle(TableStyle([
                        ("ROWBACKGROUNDS", (0,0), (-1,-1),
                         [colors.HexColor("#f9fafb"), colors.white]),
                        ("BOX", (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
                        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
                        ("TOPPADDING", (0,0), (-1,-1), 2),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                        ("LEFTPADDING", (0,0), (-1,-1), 4),
                        ("RIGHTPADDING", (0,0), (-1,-1), 4),
                    ]))
                    story.append(ev_table)
                    story.append(Spacer(1, 3*mm))

    # ── Build ─────────────────────────────────────────────────
    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font, 7)
        canvas.setFillColor(colors.HexColor("#9ca3af"))
        w, h = A4
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        canvas.drawString(16*mm, 10*mm, f"GEOScope  ·  {now}")
        canvas.drawRightString(w - 16*mm, 10*mm,
                               f"{doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
