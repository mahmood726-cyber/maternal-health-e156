#!/usr/bin/env python3
"""Scan ClinicalTrials.gov for fast, lean randomized trials with Africa relevance."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import time
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
CTG_URL = "https://clinicaltrials.gov/api/v2/studies"
PUBMED_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
BASE_QUERY = (
    "AREA[StudyType]INTERVENTIONAL "
    "AND AREA[DesignAllocation]RANDOMIZED "
    "AND AREA[OverallStatus]COMPLETED "
    "AND NOT AREA[ResultsFirstPostDate]MISSING"
)
AFRICAN_COUNTRIES = {
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros",
    "Congo", "Cote d'Ivoire", "Democratic Republic of the Congo", "Djibouti",
    "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon",
    "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho",
    "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania",
    "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria",
    "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles",
    "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan",
    "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-global", type=int, default=150)
    parser.add_argument("--max-africa", type=int, default=120)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=0.34)
    parser.add_argument("--focus-term", default="")
    parser.add_argument("--output-tag", default="")
    parser.add_argument("--skip-pubmed", action="store_true")
    return parser.parse_args()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def days_between(start: date | None, end: date | None) -> int | None:
    return None if not start or not end else (end - start).days


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=60, headers={"User-Agent": "africa-rct-scan/0.1"})
    response.raise_for_status()
    return response.json()


def africa_clause() -> str:
    parts = [f'AREA[LocationCountry]"{country}"' for country in sorted(AFRICAN_COUNTRIES)]
    return "SEARCH[Location](" + " OR ".join(parts) + ")"


def build_query(africa_only: bool, focus_term: str) -> str:
    parts = [BASE_QUERY]
    if focus_term:
        parts.append(f'"{focus_term}"')
    if africa_only:
        parts.append(africa_clause())
    return " AND ".join(parts)


def slugify_tag(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return text or "scan"


def fetch_studies(
    query: str,
    label: str,
    limit: int,
    page_size: int,
    sleep_seconds: float,
    raw_dir: Path,
) -> list[dict[str, Any]]:
    studies: list[dict[str, Any]] = []
    page_token: str | None = None
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    page = 1
    while len(studies) < limit:
        params: dict[str, Any] = {
            "format": "json",
            "pageSize": min(page_size, limit - len(studies)),
            "query.term": query,
        }
        if page_token:
            params["pageToken"] = page_token
        payload = get_json(CTG_URL, params)
        (raw_dir / f"{label}_{stamp}_page_{page:03d}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        batch = payload.get("studies", [])
        if not batch:
            break
        studies.extend(batch)
        print(f"[{label}] page {page}: +{len(batch)} studies")
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
        page += 1
        time.sleep(sleep_seconds)
    return studies[:limit]


def extract_row(study: dict[str, Any], dataset: str) -> dict[str, Any]:
    protocol = study.get("protocolSection", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    design_info = design.get("designInfo", {})
    arms = protocol.get("armsInterventionsModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    contacts = protocol.get("contactsLocationsModule", {})
    refs = protocol.get("referencesModule", {}).get("references", [])
    ident = protocol.get("identificationModule", {})
    start_date = parse_date(status.get("startDateStruct", {}).get("date"))
    primary_completion = parse_date(status.get("primaryCompletionDateStruct", {}).get("date"))
    completion_date = parse_date(status.get("completionDateStruct", {}).get("date"))
    primary_date = primary_completion or completion_date
    results_date = parse_date(status.get("resultsFirstPostDateStruct", {}).get("date"))
    submit_date = parse_date(status.get("studyFirstSubmitDate"))
    locations = contacts.get("locations", [])
    countries = sorted({loc.get("country") for loc in locations if loc.get("country")})
    africa_countries = [country for country in countries if country in AFRICAN_COUNTRIES]
    result_pmids = [str(ref.get("pmid")).strip() for ref in refs if ref.get("pmid") and ref.get("type") == "RESULT"]
    pmids = [str(ref.get("pmid")).strip() for ref in refs if ref.get("pmid")]
    return {
        "dataset_label": dataset,
        "nct_id": ident.get("nctId", ""),
        "brief_title": ident.get("briefTitle", ""),
        "lead_sponsor_class": sponsor.get("leadSponsor", {}).get("class", ""),
        "primary_purpose": design_info.get("primaryPurpose", ""),
        "intervention_types": " | ".join(sorted({item.get("type", "") for item in arms.get("interventions", []) if item.get("type")})),
        "enrollment": design.get("enrollmentInfo", {}).get("count"),
        "arm_group_count": len(arms.get("armGroups", [])),
        "location_count": len(locations),
        "country_count": len(countries),
        "countries": " | ".join(countries),
        "africa_countries": " | ".join(africa_countries),
        "has_africa_site": bool(africa_countries),
        "start_date": start_date.isoformat() if start_date else "",
        "primary_completion_date": primary_completion.isoformat() if primary_completion else "",
        "results_first_post_date": results_date.isoformat() if results_date else "",
        "trial_duration_days": days_between(start_date, primary_date),
        "results_reporting_lag_days": days_between(primary_date, results_date),
        "registration_lead_days": days_between(submit_date, start_date),
        "prospectively_registered": days_between(submit_date, start_date) is not None and days_between(submit_date, start_date) >= 0,
        "has_results_section": bool(study.get("resultsSection")),
        "has_publication_reference": bool(pmids),
        "has_result_reference": bool(result_pmids),
        "pmids": "|".join(sorted(set(pmids))),
        "result_pmids": "|".join(sorted(set(result_pmids))),
        "publication_lag_days": None,
        "speed_score": 0.0,
        "frugality_score": 0.0,
        "dissemination_score": 0.0,
        "overall_efficiency_score": 0.0,
    }


def fetch_pubmed_dates(pmids: list[str], sleep_seconds: float) -> dict[str, date]:
    if not pmids:
        return {}
    results: dict[str, date] = {}
    unique_pmids = sorted(set(pmids))
    for i in range(0, len(unique_pmids), 100):
        batch = unique_pmids[i:i + 100]
        payload = get_json(PUBMED_URL, {"db": "pubmed", "id": ",".join(batch), "retmode": "json"})
        for pmid in payload.get("result", {}).get("uids", []):
            raw = str(payload["result"].get(pmid, {}).get("sortpubdate") or payload["result"].get(pmid, {}).get("pubdate") or "")
            token = raw.split()[0].replace("/", "-")
            for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
                try:
                    results[pmid] = datetime.strptime(token, fmt).date()
                    break
                except ValueError:
                    pass
        print(f"[pubmed] enriched {len(batch)} PMIDs")
        time.sleep(sleep_seconds)
    return results


def percentile_score(values: list[float], value: float) -> float:
    ordered = sorted(values)
    rank = sum(1 for item in ordered if item <= value) / len(ordered)
    return round((1.0 - rank) * 100.0, 2)


def enrich_and_score(rows: list[dict[str, Any]], sleep_seconds: float, skip_pubmed: bool) -> None:
    pmids = []
    for row in rows:
        key = row["result_pmids"]
        if key:
            pmids.extend(part for part in key.split("|") if part)
    pubmed_dates = {} if skip_pubmed else fetch_pubmed_dates(pmids, sleep_seconds)
    for row in rows:
        key = row["result_pmids"]
        dates = [pubmed_dates[pmid] for pmid in key.split("|") if pmid in pubmed_dates]
        earliest = min(dates) if dates else None
        primary_completion = parse_date(row["primary_completion_date"])
        lag = days_between(primary_completion, earliest)
        row["publication_lag_days"] = lag if lag is not None and lag >= 0 else None
    metrics = {
        "trial_duration_days": [float(r["trial_duration_days"]) for r in rows if isinstance(r.get("trial_duration_days"), int)],
        "results_reporting_lag_days": [float(r["results_reporting_lag_days"]) for r in rows if isinstance(r.get("results_reporting_lag_days"), int)],
        "publication_lag_days": [float(r["publication_lag_days"]) for r in rows if isinstance(r.get("publication_lag_days"), int)],
        "enrollment": [float(r["enrollment"]) for r in rows if isinstance(r.get("enrollment"), int)],
        "location_count": [float(r["location_count"]) for r in rows if isinstance(r.get("location_count"), int)],
        "country_count": [float(r["country_count"]) for r in rows if isinstance(r.get("country_count"), int)],
        "arm_group_count": [float(r["arm_group_count"]) for r in rows if isinstance(r.get("arm_group_count"), int)],
    }
    for row in rows:
        speed_parts = [percentile_score(metrics[f], float(row[f])) for f in ("trial_duration_days", "results_reporting_lag_days") if isinstance(row.get(f), int)]
        if isinstance(row.get("publication_lag_days"), int):
            speed_parts.append(percentile_score(metrics["publication_lag_days"], float(row["publication_lag_days"])))
        frugality_parts = [percentile_score(metrics[f], float(row[f])) for f in ("enrollment", "location_count", "country_count", "arm_group_count") if isinstance(row.get(f), int)]
        row["speed_score"] = round(statistics.mean(speed_parts), 2) if speed_parts else 0.0
        row["frugality_score"] = round(statistics.mean(frugality_parts), 2) if frugality_parts else 0.0
        bonus = 8.0 if row["has_result_reference"] else 0.0
        if row["prospectively_registered"]:
            bonus += 6.0
        row["dissemination_score"] = round((row["speed_score"] * 0.5) + bonus, 2)
        row["overall_efficiency_score"] = round((row["speed_score"] * 0.45) + (row["frugality_score"] * 0.35) + (row["dissemination_score"] * 0.20), 2)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def median_of(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [row[field] for row in rows if isinstance(row.get(field), int)]
    return float(statistics.median(values)) if values else None


def top_counts(rows: list[dict[str, Any]], field: str) -> str:
    counter: Counter[str] = Counter()
    for row in rows:
        raw = str(row.get(field, "")).strip()
        if not raw:
            continue
        counter.update(part.strip() for part in raw.split("|") if part.strip())
    return ", ".join(f"{name} ({count})" for name, count in counter.most_common(5)) or "none"


def main() -> None:
    args = parse_args()
    tag = slugify_tag(args.output_tag or args.focus_term) if (args.output_tag or args.focus_term) else ""
    raw_dir = RAW_DIR / tag if tag else RAW_DIR
    out_dir = OUT_DIR / tag if tag else OUT_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    global_rows = [extract_row(study, "global") for study in fetch_studies(build_query(False, args.focus_term), "global", args.max_global, args.page_size, args.sleep_seconds, raw_dir)]
    africa_rows = [extract_row(study, "africa") for study in fetch_studies(build_query(True, args.focus_term), "africa", args.max_africa, args.page_size, args.sleep_seconds, raw_dir)]
    all_rows = global_rows + africa_rows
    enrich_and_score(all_rows, args.sleep_seconds, args.skip_pubmed)
    scores = sorted(row["overall_efficiency_score"] for row in all_rows)
    cutoff = scores[max(0, int(len(scores) * 0.75) - 1)] if scores else 0.0
    top_rows = sorted([row for row in all_rows if row["overall_efficiency_score"] >= cutoff], key=lambda row: row["overall_efficiency_score"], reverse=True)
    africa_shortlist = sorted([
        row for row in africa_rows
        if isinstance(row.get("enrollment"), int) and row["enrollment"] <= 500
        and isinstance(row.get("location_count"), int) and row["location_count"] <= 10
        and isinstance(row.get("country_count"), int) and row["country_count"] <= 2
        and row["prospectively_registered"]
    ], key=lambda row: row["overall_efficiency_score"], reverse=True)
    write_csv(out_dir / "global_benchmark.csv", global_rows)
    write_csv(out_dir / "africa_benchmark.csv", africa_rows)
    write_csv(out_dir / "top_efficiency_trials.csv", top_rows)
    write_csv(out_dir / "africa_transfer_shortlist.csv", africa_shortlist)
    summary = "\n".join([
        "# Africa RCT Efficiency Scan Summary",
        "",
        f"- Global benchmark studies: {len(global_rows)}",
        f"- Africa-site benchmark studies: {len(africa_rows)}",
        f"- Top-efficiency studies: {len(top_rows)}",
        f"- Africa transfer shortlist studies: {len(africa_shortlist)}",
        f"- Global median enrollment: {median_of(global_rows, 'enrollment')}",
        f"- Global median duration days: {median_of(global_rows, 'trial_duration_days')}",
        f"- Global median results lag days: {median_of(global_rows, 'results_reporting_lag_days')}",
        f"- Global median publication lag days: {median_of(global_rows, 'publication_lag_days')}",
        f"- Global result-linked publication count: {sum(row['has_result_reference'] for row in global_rows)} of {len(global_rows)}",
        f"- Africa median enrollment: {median_of(africa_rows, 'enrollment')}",
        f"- Africa median duration days: {median_of(africa_rows, 'trial_duration_days')}",
        f"- Africa median results lag days: {median_of(africa_rows, 'results_reporting_lag_days')}",
        f"- Africa median publication lag days: {median_of(africa_rows, 'publication_lag_days')}",
        f"- Africa result-linked publication count: {sum(row['has_result_reference'] for row in africa_rows)} of {len(africa_rows)}",
        f"- Top sponsor classes: {top_counts(top_rows, 'lead_sponsor_class')}",
        f"- Top intervention types: {top_counts(top_rows, 'intervention_types')}",
        f"- Top Africa countries in Africa benchmark: {top_counts(africa_rows, 'africa_countries')}",
        "",
        "Interpretation: this benchmark rewards faster completion, smaller operational footprint, and faster public reporting. It does not measure true cost or true clinical effectiveness.",
    ]) + "\n"
    (out_dir / "summary.md").write_text(summary, encoding="utf-8")
    print(f"Wrote {out_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
