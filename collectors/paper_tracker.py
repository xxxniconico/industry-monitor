#!/usr/bin/env python3
# Dependencies: requests (stdlib: xml.etree.ElementTree)
"""Fetch recent arXiv papers for AI and medical categories."""

import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

ARXIV_API = (
    "http://export.arxiv.org/api/query"
    "?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG+OR+cat:q-bio+OR+cat:stat.ML"
    "&sortBy=submittedDate&sortOrder=descending&max_results=50"
)
USER_AGENT = "IndustryMonitor/1.0 (contact: industry-monitor@local)"
ATOM_URI = "http://www.w3.org/2005/Atom"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "feeds"


def atom_tag(local: str) -> str:
    return f"{{{ATOM_URI}}}{local}"

AI_CATEGORIES = {"cs.AI", "cs.CL", "cs.LG", "stat.ML"}
MEDICAL_CATEGORIES = {"q-bio"}


def infer_industry(categories: list[str]) -> str:
    if any(c.split(".")[0] == "q-bio" or c in MEDICAL_CATEGORIES for c in categories):
        return "medical"
    return "AI"


def parse_arxiv_id(entry_id: str) -> str:
    match = re.search(r"arxiv\.org/abs/([^/\s]+)", entry_id)
    if match:
        return re.sub(r"v\d+$", "", match.group(1))
    return entry_id.rsplit("/", 1)[-1]


def fetch_arxiv_xml() -> tuple[bytes | None, str | None]:
    """Try urllib first (stdlib), then requests with retries."""
    req = urllib.request.Request(ARXIV_API, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            content = resp.read()
            if len(content) >= 200:
                return content, None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        last_error = str(exc)
    else:
        last_error = "urllib returned empty response"

    for attempt in range(3):
        try:
            resp = requests.get(
                ARXIV_API,
                headers={"User-Agent": USER_AGENT},
                timeout=(10, 90),
            )
            resp.raise_for_status()
            if len(resp.content) >= 200:
                return resp.content, None
            last_error = f"requests returned only {len(resp.content)} bytes"
        except requests.RequestException as exc:
            last_error = str(exc)
        if attempt < 2:
            time.sleep(3 * (attempt + 1))

    return None, last_error


def iter_entries(root: ET.Element) -> list[ET.Element]:
    ns = {"atom": ATOM_URI}
    entries = root.findall(atom_tag("entry"))
    if not entries:
        entries = root.findall(".//atom:entry", ns)
    if not entries:
        entries = list(root.iter(atom_tag("entry")))
    return entries


def normalize_published(value: str) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return value


def fetch_papers() -> dict:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {"source": "arxiv", "fetched_at": fetched_at, "items": []}

    content, fetch_error = fetch_arxiv_xml()
    if content is None:
        result["error"] = fetch_error or "Failed to fetch arXiv API"
        return result

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        result["error"] = f"XML parse error: {exc}"
        return result

    entries = iter_entries(root)
    if not entries:
        result["error"] = "No atom:entry elements found in API response"
        return result

    for entry in entries:
        title_el = entry.find(atom_tag("title"))
        id_el = entry.find(atom_tag("id"))
        published_el = entry.find(atom_tag("published"))
        summary_el = entry.find(atom_tag("summary"))
        categories = [
            cat.get("term", "")
            for cat in entry.findall(atom_tag("category"))
            if cat.get("term")
        ]

        if id_el is None or not (id_el.text or "").strip():
            continue

        arxiv_id = parse_arxiv_id(id_el.text.strip())
        title = ((title_el.text if title_el is not None else "") or "").strip().replace("\n", " ")
        summary = ((summary_el.text if summary_el is not None else "") or "").strip().replace("\n", " ")

        result["items"].append(
            {
                "title": title,
                "arxiv_id": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "published": normalize_published(
                    ((published_el.text if published_el is not None else "") or "").strip()
                ),
                "categories": categories,
                "industry": infer_industry(categories),
                "summary": summary,
            }
        )

    if not result["items"]:
        result["error"] = f"Parsed {len(entries)} entries but extracted 0 items"

    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_path = OUTPUT_DIR / f"arxiv_{today}.json"

    data = fetch_papers()
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data.get('items', []))} items to {output_path}")
    if "error" in data:
        print(f"Warning: {data['error']}")


if __name__ == "__main__":
    main()
