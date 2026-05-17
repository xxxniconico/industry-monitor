#!/usr/bin/env python3
# Dependencies: requests
"""Fetch recruiting interventional trials from ClinicalTrials.gov API v2."""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = (
    "https://clinicaltrials.gov/api/v2/studies"
    "?query.term=AREA[OverallStatus]RECRUITING+AND+AREA[StudyType]INTERVENTIONAL"
    "&pageSize=50&format=json"
)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "feeds"


def extract_phase(design_module: dict) -> str:
    phases = design_module.get("phases") or []
    if not phases:
        return ""
    label_map = {
        "NA": "N/A",
        "EARLY_PHASE1": "Early Phase 1",
        "PHASE1": "Phase 1",
        "PHASE2": "Phase 2",
        "PHASE3": "Phase 3",
        "PHASE4": "Phase 4",
    }
    return ", ".join(label_map.get(p, p.replace("_", " ").title()) for p in phases)


def parse_study(study: dict) -> dict:
    protocol = study.get("protocolSection") or {}
    ident = protocol.get("identificationModule") or {}
    status_mod = protocol.get("statusModule") or {}
    design = protocol.get("designModule") or {}
    conditions_mod = protocol.get("conditionsModule") or {}
    arms_mod = protocol.get("armsInterventionsModule") or {}

    nct_id = ident.get("nctId", "")
    interventions = [
        i.get("name", "")
        for i in (arms_mod.get("interventions") or [])
        if i.get("name")
    ]

    start_date = ""
    start_struct = status_mod.get("startDateStruct") or {}
    if start_struct.get("date"):
        start_date = start_struct["date"]

    return {
        "nct_id": nct_id,
        "title": ident.get("briefTitle") or ident.get("officialTitle") or "",
        "status": status_mod.get("overallStatus", ""),
        "phase": extract_phase(design),
        "conditions": conditions_mod.get("conditions") or [],
        "interventions": interventions,
        "start_date": start_date,
        "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
    }


def fetch_trials() -> dict:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {"source": "clinicaltrials", "fetched_at": fetched_at, "items": []}

    try:
        resp = requests.get(API_URL, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        result["error"] = str(exc)
        return result
    except json.JSONDecodeError as exc:
        result["error"] = f"JSON parse error: {exc}"
        return result

    for study in payload.get("studies") or []:
        result["items"].append(parse_study(study))

    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_path = OUTPUT_DIR / f"clinical_trials_{today}.json"

    data = fetch_trials()
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(data.get('items', []))} items to {output_path}")
    if "error" in data:
        print(f"Warning: {data['error']}")


if __name__ == "__main__":
    main()
