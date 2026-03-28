# Protocol

## Working Title

Registry-first Africa-site pregnancy-related maternal health randomized trials as a transfer template for cheaper and faster RCT delivery.

## Background and Rationale

Large differences in infrastructure, budget, and trial management capacity make it hard to identify RCT designs that can be transferred across African settings. This protocol uses ClinicalTrials.gov as a registry-first screening layer to identify Africa-site randomized trials that look operationally lean and comparatively fast.

## Primary Objective

Estimate the proportion of Africa-site pregnancy-related maternal health randomized trials that meet a pragmatic transfer shortlist defined by smaller enrollment, lower site and country footprint, prospective registration, and completed results posting.

## Study Design

Descriptive registry analysis using ClinicalTrials.gov API v2 records restricted to completed randomized interventional studies with posted results and at least one African site.

## Data Source and Search Logic

- Registry: ClinicalTrials.gov API v2
- Focus term: `pregnancy`
- Geography filter: at least one African site country
- Query frame: interventional, randomized, completed, and not missing results posting

## Eligibility Criteria

- Study type: interventional
- Allocation: randomized
- Overall status: completed
- Results: posted on ClinicalTrials.gov
- Geography: at least one African study site

## Primary Estimand

Shortlist proportion among Africa-site benchmark trials. In the current analysis this was `12/80` with Wilson 95% interval `0.09` to `0.24`.

## Secondary Measures

- median trial duration days
- median results-reporting lag days
- publication-link coverage and result-PMID coverage
- country concentration across Africa-site records
- sponsor-class concentration among shortlist studies

## Current Snapshot

- Benchmark trials: `80`
- Total enrolled participants across benchmark records: `296306`
- Median trial duration days: `902.0`
- Median results-reporting lag days: `529.5`
- Most represented Africa-site countries: South Africa (49), Kenya (10), Uganda (8), Egypt (6), Malawi (3)
- Shortlist sponsor mix: OTHER (10), NIH (1), NETWORK (1)

## Analysis Plan

Use registry-visible proxies only. Compare Africa-site benchmarks against the topic-specific global benchmark. Treat the shortlist proportion as the lead operational signal and interpret duration, reporting lag, and sponsor mix as supporting markers rather than direct measures of cost or effectiveness.

## Governance and Limitations

This protocol does not estimate true budget, true implementation cost, or true clinical effectiveness. Registry metadata can understate local intellectual leadership, publication linkage is incomplete, and sponsor-country inference is imperfect.

## Outputs

- `paper/article.json`
- `paper/index.html`
- `paper/e156_body.md`
- `paper/validation.json`
- `data/summary.md`
- `data/africa_benchmark.csv`
- `data/africa_transfer_shortlist.csv`

## Versioning

Current protocol version: `0.1.0` dated `2026-03-28`.
