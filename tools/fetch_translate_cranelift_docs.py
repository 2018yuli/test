#!/usr/bin/env python3
"""Fetch Cranelift docs and create paragraph-aligned English/Chinese Markdown."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE = DOCS / "source"
BILINGUAL = DOCS / "bilingual"
CACHE = DOCS / ".cache" / "translations.json"

RAW_BASE = "https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/"
SOURCES = [
    {
        "slug": "00-cranelift-home",
        "title": "Cranelift home page",
        "url": "https://cranelift.dev/",
        "kind": "html",
    },
    {
        "slug": "01-index",
        "title": "Cranelift documentation index",
        "url": RAW_BASE + "cranelift/docs/index.md",
        "kind": "markdown",
    },
    {
        "slug": "02-ir",
        "title": "Cranelift IR",
        "url": RAW_BASE + "cranelift/docs/ir.md",
        "kind": "markdown",
    },
    {
        "slug": "03-testing",
        "title": "Cranelift testing",
        "url": RAW_BASE + "cranelift/docs/testing.md",
        "kind": "markdown",
    },
    {
        "slug": "04-compare-llvm",
        "title": "Comparison with LLVM",
        "url": RAW_BASE + "cranelift/docs/compare-llvm.md",
        "kind": "markdown",
    },
    {
        "slug": "05-isle-integration",
        "title": "ISLE integration",
        "url": RAW_BASE + "cranelift/docs/isle-integration.md",
        "kind": "markdown",
    },
    {
        "slug": "06-isle-language-reference",
        "title": "ISLE language reference",
        "url": RAW_BASE + "cranelift/isle/docs/language-reference.md",
        "kind": "markdown",
    },
]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "codex-doc-fetcher/1.0"})
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                return response.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"fetch failed for {url}: {last_error}")


def html_to_markdown(html: str) -> str:
    proc = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm", "--wrap=none"],
        input=html,
        text=True,
        capture_output=True,
        check=True,
    )
    text = proc.stdout
    text = re.sub(r"\n\n\s*\n+", "\n\n", text).strip() + "\n"
    return text


def load_cache() -> dict[str, str]:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def is_code_or_verbatim(block: str) -> bool:
    stripped = block.strip()
    if not stripped:
        return True
    if stripped.startswith("```") or stripped.startswith("~~~"):
        return True
    if stripped.startswith("<") and stripped.endswith(">"):
        return True
    if re.fullmatch(r"\[[^\]]+\]:\s+\S+.*", stripped):
        return True
    # Markdown tables are usually less readable if duplicated line-by-line by
    # a translator. Keep them stable unless surrounding prose explains them.
    lines = [line for line in stripped.splitlines() if line.strip()]
    if len(lines) >= 2 and all(line.lstrip().startswith("|") for line in lines[:2]):
        return True
    return False


def split_markdown_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    fence: str | None = None

    for line in text.splitlines():
        fence_match = re.match(r"^(```+|~~~+)", line)
        if fence_match:
            marker = fence_match.group(1)[:3]
            if fence is None:
                if current:
                    blocks.append("\n".join(current).rstrip())
                    current = []
                fence = marker
                current.append(line)
                continue
            if fence == marker:
                current.append(line)
                blocks.append("\n".join(current).rstrip())
                current = []
                fence = None
                continue

        if fence is not None:
            current.append(line)
            continue

        if not line.strip():
            if current:
                blocks.append("\n".join(current).rstrip())
                current = []
            continue

        current.append(line)

    if current:
        blocks.append("\n".join(current).rstrip())
    return blocks


def extract_chat_text(data: dict) -> str:
    return data["choices"][0]["message"]["content"].strip()


def call_model(prompt: str, max_tokens: int) -> str:
    base_url = os.environ.get("NEBULA_CODEX_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    api_key = os.environ.get("NEBULA_CODEX_API_KEY") or os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("NEBULA_CODEX_MODEL", "gpt-5.5")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY/NEBULA_CODEX_API_KEY is not set")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a precise technical translator. Translate English software "
                    "documentation into Simplified Chinese. Preserve Markdown syntax, code "
                    "spans, links, identifiers, instruction names, and command-line flags. "
                    "Output only the requested machine-readable result."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                return extract_chat_text(json.load(response))
        except Exception as exc:  # noqa: BLE001
            if hasattr(exc, "read"):
                try:
                    body = exc.read().decode("utf-8")[:1000]
                    print(f"model error body: {body}", file=sys.stderr, flush=True)
                except Exception:
                    pass
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"model request failed: {last_error}")


def translate_batch(blocks: list[str]) -> list[str]:
    prompt = (
        "Translate each Markdown block in the JSON array below into Simplified Chinese.\n"
        "Return a JSON array of strings with exactly the same length and order.\n"
        "Do not add commentary. Do not wrap the JSON in Markdown fences.\n\n"
        + json.dumps(blocks, ensure_ascii=False)
    )
    max_tokens = min(8000, max(1200, int(sum(len(block) for block in blocks) * 1.8) + 800))
    content = call_model(prompt, max_tokens=max_tokens)
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"could not parse model JSON: {exc}\n{content[:1000]}") from exc
    if not isinstance(parsed, list) or len(parsed) != len(blocks):
        raise RuntimeError("model returned an unexpected translation array shape")
    return [str(item).strip() for item in parsed]


def translate_blocks_recursive(blocks: list[str]) -> list[str]:
    if not blocks:
        return []
    try:
        return translate_batch(blocks)
    except Exception as exc:  # noqa: BLE001
        if len(blocks) == 1:
            raise
        mid = len(blocks) // 2
        print(
            f"  batch failed ({len(blocks)} blocks); splitting into {mid} and {len(blocks) - mid}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        left = translate_blocks_recursive(blocks[:mid])
        right = translate_blocks_recursive(blocks[mid:])
        return left + right


def translate_blocks(blocks: list[str], cache: dict[str, str]) -> dict[str, str]:
    todo = []
    for block in blocks:
        if is_code_or_verbatim(block):
            continue
        key = hashlib.sha256(block.encode("utf-8")).hexdigest()
        if key not in cache:
            todo.append(block)

    batch: list[str] = []
    batch_chars = 0
    for block in todo:
        if batch and batch_chars + len(block) > 3000:
            print(f"  translating batch: {len(batch)} blocks, {batch_chars} chars", flush=True)
            translations = translate_blocks_recursive(batch)
            for source, translated in zip(batch, translations, strict=True):
                cache[hashlib.sha256(source.encode("utf-8")).hexdigest()] = translated
            save_cache(cache)
            batch = []
            batch_chars = 0
        batch.append(block)
        batch_chars += len(block)

    if batch:
        print(f"  translating batch: {len(batch)} blocks, {batch_chars} chars", flush=True)
        translations = translate_blocks_recursive(batch)
        for source, translated in zip(batch, translations, strict=True):
            cache[hashlib.sha256(source.encode("utf-8")).hexdigest()] = translated
        save_cache(cache)

    return cache


def bilingual_markdown(meta: dict[str, str], source_text: str, cache: dict[str, str]) -> str:
    blocks = split_markdown_blocks(source_text)
    output = [
        f"<!-- Source: {meta['url']} -->",
        f"<!-- Title: {meta['title']} -->",
        "",
    ]
    for block in blocks:
        output.append(block)
        if not is_code_or_verbatim(block):
            key = hashlib.sha256(block.encode("utf-8")).hexdigest()
            translated = cache.get(key, "").strip()
            if translated:
                output.append("")
                output.append(translated)
        output.append("")
    return "\n".join(output).rstrip() + "\n"


def main() -> int:
    SOURCE.mkdir(parents=True, exist_ok=True)
    BILINGUAL.mkdir(parents=True, exist_ok=True)
    cache = load_cache()
    manifest = []

    for item in SOURCES:
        print(f"fetching {item['slug']}...", flush=True)
        source_path = SOURCE / f"{item['slug']}.md"
        if source_path.exists():
            source_text = source_path.read_text(encoding="utf-8")
        else:
            raw = fetch(item["url"])
            source_text = html_to_markdown(raw) if item["kind"] == "html" else raw
            source_path.write_text(source_text, encoding="utf-8")

        blocks = split_markdown_blocks(source_text)
        print(f"translating {item['slug']} ({len(blocks)} blocks)...", flush=True)
        translate_blocks(blocks, cache)

        output_path = BILINGUAL / f"{item['slug']}.zh-en.md"
        output_path.write_text(bilingual_markdown(item, source_text, cache), encoding="utf-8")
        manifest.append(
            {
                "title": item["title"],
                "source_url": item["url"],
                "source_file": str(source_path.relative_to(ROOT)),
                "bilingual_file": str(output_path.relative_to(ROOT)),
                "sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            }
        )

    (DOCS / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(manifest)} bilingual documents", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
