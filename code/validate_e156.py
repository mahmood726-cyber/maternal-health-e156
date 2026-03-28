import argparse
import json
import re
import sys
from pathlib import Path


LINK_RE = re.compile(r"(https?://|www\.|doi\.org/)", re.IGNORECASE)
HEADING_RE = re.compile(r"^\s*#+\s+", re.MULTILINE)
INTERVAL_RE = re.compile(r"\b(?:95%\s*(?:CI|confidence interval)|CI)\b", re.IGNORECASE)
ESTIMATE_RE = re.compile(
    r"\b(?:RR|OR|HR|MD|SMD|RD|AUC|sensitivity|specificity|mean difference|risk ratio|proportion|prevalence|rate|median)\b",
    re.IGNORECASE,
)


def load_text(args: argparse.Namespace) -> str:
    if args.stdin:
        return sys.stdin.read().strip()

    if not args.file:
        raise SystemExit("Provide --file or --stdin.")

    path = Path(args.file)
    raw = path.read_text(encoding="utf-8")

    if args.json_field:
        data = json.loads(raw)
        value = data.get(args.json_field)
        if value is None:
            raise SystemExit(f"JSON field '{args.json_field}' not found.")
        return str(value).strip()

    return raw.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text.strip())
    return [part.strip() for part in parts if part.strip()]


def count_words(text: str) -> int:
    return len(text.split())


def validate(text: str, strict_words: bool = True) -> dict:
    sentences = split_sentences(text)
    words = count_words(text)
    checks = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("single paragraph", "\n\n" not in text, "Body must not contain blank-line paragraph breaks.")
    add("sentence count", len(sentences) == 7, f"Found {len(sentences)} sentences.")
    add("word count", words == 156 if strict_words else words <= 156, f"Found {words} words.")
    add("no headings", not HEADING_RE.search(text), "No markdown headings allowed in body.")
    add("no links", not LINK_RE.search(text), "No links or DOI links allowed in body.")
    add(
        "result sentence has interval",
        len(sentences) >= 4 and bool(INTERVAL_RE.search(sentences[3])),
        "Sentence 4 should include a confidence interval.",
    )
    add(
        "result sentence has estimand",
        len(sentences) >= 4 and bool(ESTIMATE_RE.search(sentences[3])),
        "Sentence 4 should name an effect measure or test metric.",
    )
    add(
        "boundary sentence present",
        len(sentences) >= 7
        and any(keyword in sentences[6].lower() for keyword in ["limit", "limited", "caution", "boundary", "harm", "scope"]),
        "Sentence 7 should express a limitation, harm, or scope boundary.",
    )

    return {
        "word_count": words,
        "sentence_count": len(sentences),
        "checks": checks,
        "ok": all(check["ok"] for check in checks),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an E156 body.")
    parser.add_argument("--file", help="Path to text or JSON file.")
    parser.add_argument("--json-field", help="Read body from a field inside a JSON file.")
    parser.add_argument("--stdin", action="store_true", help="Read body text from stdin.")
    parser.add_argument("--max-156", action="store_true", help="Allow up to 156 words instead of exactly 156.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    text = load_text(args)
    result = validate(text, strict_words=not args.max_156)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"word_count: {result['word_count']}")
    print(f"sentence_count: {result['sentence_count']}")
    print(f"overall: {'PASS' if result['ok'] else 'FAIL'}")
    for check in result["checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        print(f"- {status}: {check['name']} | {check['detail']}")


if __name__ == "__main__":
    main()
