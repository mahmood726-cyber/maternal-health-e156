# Protocol

## Title

Registry-first Africa-site pregnancy-related maternal health RCT transfer scan.

## Rationale

This protocol describes a descriptive ClinicalTrials.gov scan focused on completed randomized interventional studies with posted results in the pregnancy-related maternal health domain.

## Primary Objective

Estimate the proportion of Africa-site pregnancy-related maternal health trials that meet a pragmatic transfer shortlist for cheaper and faster delivery.

## Data Source

ClinicalTrials.gov API v2 with focus term `pregnancy` plus Africa-site location filtering.

## Eligibility

- Study type: interventional
- Allocation: randomized
- Status: completed
- Results: posted on ClinicalTrials.gov
- Geography: at least one African study site

## Primary Estimand

Shortlist proportion among Africa-site benchmark trials. In the current run this was 12/80 with Wilson 95% interval 0.09 to 0.24.

## Secondary Measures

- trial duration days
- results-reporting lag days
- publication-link coverage
- country concentration
- sponsor-class mix

## Analysis Plan

Use registry-visible proxies only. Do not infer true budget or true intervention effectiveness from the shortlist metric alone.

## Outputs

- `paper/article.json`
- `paper/index.html`
- `data/summary.md`
- `data/africa_benchmark.csv`
- `data/africa_transfer_shortlist.csv`

## Limitation

This protocol relies on registry metadata and does not directly measure cost, implementation feasibility, or African intellectual leadership.
