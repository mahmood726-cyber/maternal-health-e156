# Lean Africa-site pregnancy-related RCTs as a transfer template

This repository packages a local E156 micro-paper, protocol draft, data extracts, and reproducibility files for a registry-first scan of Africa-site randomized trials.

## Research Question

The primary descriptive question is how often Africa-site trials in this topic meet a pragmatic shortlist for cheaper and faster delivery.

## Current Result

- Africa benchmark trials: `80`
- Transfer shortlist trials: `12`
- Shortlist proportion: `0.15` with Wilson 95% interval `0.09` to `0.24`
- Median trial duration days: `902.0`
- Median results-reporting lag days: `529.5`
- Most represented Africa-site countries: South Africa (49), Kenya (10), Uganda (8), Egypt (6), Malawi (3)

## Release Track

- Active paper format: `E156 micro-paper`
- Active paper body: exactly `156` words, `7` sentences, single paragraph
- Conventional journal expansion is deferred unless explicitly requested

## Layout

- `paper/`: E156 body, article JSON, validation record, and HTML bundle
- `protocol/`: submission-oriented protocol draft
- `data/`: copied topic outputs from the parent analysis project
- `code/`: local scripts needed to rerun validation and rebuild the bundle
- `.github/workflows/`: lightweight validation workflow for GitHub-hosted use
- `submission/`: E156-facing manuscript wrapper, title metadata, note files, and expansion notes
- `STATUS.md`: current completion state and remaining gaps

## Quick Start

Validate the E156 body:

```bash
python3 code/validate_e156.py --file paper/article.json --json-field body
```

Rebuild the HTML bundle:

```bash
python3 code/build_e156_bundle.py --input paper/article.json --output paper/index.html --template templates/e156_interactive_template.html
```

## Status

- Local E156 body validated
- Local HTML bundle generated
- Protocol tightened beyond the initial skeleton
- Local git repo initialized
- Public GitHub repository is live at `https://github.com/mahmood726-cyber/maternal-health-e156`
- Active submission package aligned to strict `E156` release mode
