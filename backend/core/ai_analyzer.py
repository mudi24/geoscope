from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Tuple

import httpx


def fingerprint_content(content: str) -> str:
    sample = content[:1000].encode("utf-8", errors="ignore")
    return hashlib.md5(sample).hexdigest()


def _prompt(content: str) -> str:
    return (
        "你是一位生成式搜索引擎的批判性读者。请分析以下网页内容，严格按 JSON 格式返回：\n\n"
        "{\n"
        '  "summary": "一句话总结页面核心主题",\n'
        '  "gaps": ["知识缺口1", "知识缺口2", "知识缺口3"],\n'
        '  "suggestions": [\n'
        '    {"priority": 1, "issue": "具体问题", "fix": "具体修改建议"},\n'
        '    {"priority": 2, "issue": "...", "fix": "..."},\n'
        '    {"priority": 3, "issue": "...", "fix": "..."}\n'
        "  ]\n"
        "}\n\n"
        "要求：\n"
        "1. gaps 必须具体，如\"第3段提到'CAP定理'但未解释其含义\"，而非\"有些概念不清楚\"\n"
        "2. suggestions 必须可执行，包含具体位置和修改方式\n"
        "3. 评估\"可引用性\"：AI 搜索回答相关问题时，引用此页面的可能性及原因\n\n"
        "正文内容：\n---\n"
        f"{content}\n"
        "---\n"
    )


def _normalize_result(obj: Dict[str, Any]) -> Dict[str, Any]:
    summary = str(obj.get("summary") or "").strip()
    gaps = obj.get("gaps") or []
    suggestions = obj.get("suggestions") or []

    if not isinstance(gaps, list):
        gaps = []
    gaps = [str(x).strip() for x in gaps if str(x).strip()]

    normalized_suggestions: List[Dict[str, Any]] = []
    if isinstance(suggestions, list):
        for s in suggestions:
            if not isinstance(s, dict):
                continue
            priority = int(s.get("priority") or 3)
            issue = str(s.get("issue") or "").strip()
            fix = str(s.get("fix") or "").strip()
            if not issue or not fix:
                continue
            normalized_suggestions.append({"priority": priority, "issue": issue, "fix": fix})

    normalized_suggestions.sort(key=lambda x: x["priority"])

    while len(gaps) < 3:
        gaps.append("未检测到明确的知识缺口（可能需要更长正文或更结构化的小标题）。")
    if len(normalized_suggestions) < 3:
        base = [
            {"priority": 1, "issue": "缺少清晰的结论/要点汇总", "fix": "在开头增加 TL;DR 列表，总结 3-5 条关键结论。"},
            {"priority": 2, "issue": "关键术语解释不足", "fix": "在首次出现术语处补充 1-2 句定义，并给出示例。"},
            {"priority": 3, "issue": "缺少可引用的外部来源", "fix": "补充 2-3 个权威外链（论文/标准/官方文档），并在文中标注引用位置。"},
        ]
        for item in base:
            if len(normalized_suggestions) >= 3:
                break
            normalized_suggestions.append(item)

    return {"summary": summary or "（未生成摘要）", "gaps": gaps[:6], "suggestions": normalized_suggestions[:6]}


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        snippet = re.sub(r"```(?:json)?", "", snippet, flags=re.IGNORECASE).strip()
        return json.loads(snippet)
    raise ValueError("AI response is not valid JSON")


async def analyze_with_cache(
    conn,
    url: str,
    content: str,
    *,
    allow_external: bool = True,
) -> Tuple[Dict[str, Any], bool, bool]:
    fp = fingerprint_content(content)
    cur = await conn.execute(
        """
        SELECT result_json
        FROM ai_cache
        WHERE fingerprint = ?
          AND datetime(created_at) >= datetime('now', '-7 days')
        """,
        (fp,),
    )
    row = await cur.fetchone()
    if row and row["result_json"]:
        try:
            return _normalize_result(json.loads(row["result_json"])), True, False
        except Exception:
            pass

    truncated = content[:3000]
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    external_called = False
    if not api_key or not allow_external:
        if not api_key:
            summary = "（AI 未调用：未配置 DEEPSEEK_API_KEY，返回本地占位分析）"
        else:
            summary = "（AI 未调用：已触发调用配额/限流，返回本地占位分析）"
        result = _normalize_result(
            {
                "summary": summary,
                "gaps": [
                    "未调用 AI：无法指出具体段落的知识缺口。",
                    "可补充作者/发布日期/引用链接以提升可引用性。",
                    "可加入 FAQ 或 Q&A 结构以提升问答友好度。",
                ],
                "suggestions": [],
            }
        )
    else:
        payload = {
            "model": model,
            "temperature": 0,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": _prompt(truncated)}],
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content_text = data["choices"][0]["message"]["content"]
        result = _normalize_result(_extract_json(content_text))
        external_called = True

    if external_called:
        await conn.execute(
            """
            INSERT INTO ai_cache (fingerprint, url, result_json)
            VALUES (?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
              url=excluded.url,
              result_json=excluded.result_json,
              created_at=CURRENT_TIMESTAMP
            """,
            (fp, url, json.dumps(result, ensure_ascii=False)),
        )
        await conn.commit()

    return result, False, external_called
