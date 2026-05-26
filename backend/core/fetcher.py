from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass(frozen=True)
class FetchResult:
    title: str
    content: str
    method: str
    length: int
    raw_html: Optional[str] = None


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_with_readability(html: str) -> tuple[str, str]:
    from readability import Document
    from lxml import html as lxml_html

    doc = Document(html)
    title = (doc.title() or "").strip()
    summary_html = doc.summary(html_partial=True)
    root = lxml_html.fromstring(summary_html)
    content = root.text_content()
    return title, _clean_text(content)


async def _fetch_httpx(url: str) -> FetchResult:
    timeout = httpx.Timeout(15.0, connect=10.0)
    headers = {
        "User-Agent": "GEOScope/0.1 (+https://localhost) Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    title, content = _extract_with_readability(html)
    return FetchResult(
        title=title,
        content=content,
        method="httpx",
        length=len(content),
        raw_html=html,
    )


async def _fetch_playwright(url: str) -> FetchResult:
    from playwright.async_api import async_playwright

    max_pw = int(os.getenv("GEOSCOPE_MAX_CONCURRENT_PLAYWRIGHT", "1"))
    if not hasattr(_fetch_playwright, "_sem"):
        _fetch_playwright._sem = asyncio.Semaphore(max_pw)  # type: ignore[attr-defined]

    async with _fetch_playwright._sem:  # type: ignore[attr-defined]
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as e:
                msg = str(e)
                if "Executable doesn't exist" in msg or "playwright install" in msg:
                    raise RuntimeError(
                        "Playwright 浏览器未安装。请在 backend 虚拟环境中运行："
                        " `python -m playwright install chromium`"
                    ) from e
                raise
            context = await browser.new_context(
                user_agent="GEOScope/0.1 Playwright",
            )
            page = await context.new_page()
            try:
                async def route_handler(route):
                    if route.request.resource_type in {"image", "media", "font"}:
                        await route.abort()
                    else:
                        await route.continue_()

                await page.route("**/*", route_handler)
                page.set_default_navigation_timeout(30000)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                html = await page.content()
            finally:
                await page.close()
                await context.close()
                await browser.close()

    title, content = _extract_with_readability(html)
    return FetchResult(
        title=title,
        content=content,
        method="playwright",
        length=len(content),
        raw_html=html,
    )


async def fetch_url(url: str) -> FetchResult:
    """
    三层降级策略：
    - L1: httpx + readability
    - L2: playwright headless（当 L1 失败或内容 < 500）
    - L3: 抛出异常
    """
    httpx_result: Optional[FetchResult] = None
    try:
        httpx_result = await _fetch_httpx(url)
        if httpx_result.length >= 500:
            return _truncate(httpx_result)
    except Exception:
        httpx_result = None

    try:
        pw_result = await _fetch_playwright(url)
        return _truncate(pw_result)
    except Exception as e:
        if httpx_result is not None:
            # Playwright 失败时，退回 httpx 结果（即使偏短，也保证流程可演示/可用）
            return _truncate(httpx_result)
        raise RuntimeError(f"fetch failed: {e}") from e


def _truncate(result: FetchResult, max_chars: int = 8000) -> FetchResult:
    if len(result.content) <= max_chars:
        return result
    truncated = result.content[:max_chars].rstrip()
    return FetchResult(
        title=result.title,
        content=truncated,
        method=result.method,
        length=len(truncated),
        raw_html=result.raw_html,
    )
