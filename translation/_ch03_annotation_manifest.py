#!/usr/bin/env python3
"""Validate Chapter 3 learning annotation manifests."""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

PAGE = "ch03-convex-functions.html"
TERM_PREFIX = PAGE + "#pair-"
VALID_KINDS = {
    "definition",
    "example",
    "condition",
    "geometry",
    "operation",
    "conjugate",
    "quasiconvex",
    "log-concave",
    "generalized",
}
REQUIRED_FIELDS = {"page", "pair", "term", "kind", "title", "body", "source_summary"}


class PairTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_pair = False
        self._pair_depth = 0
        self._current: list[str] = []
        self.pairs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()
        if tag == "div" and "pair" in classes and not self._in_pair:
            self._in_pair = True
            self._pair_depth = 1
            self._current = []
            return
        if not self._in_pair:
            return
        if tag == "div":
            self._pair_depth += 1
        if tag == "br":
            self._current.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if not self._in_pair:
            return
        if tag in {"p", "li", "h2", "h3", "h4", "h5", "h6", "div"}:
            self._current.append(" ")
        if tag == "div":
            self._pair_depth -= 1
            if self._pair_depth == 0:
                text = unescape("".join(self._current))
                text = re.sub(r"\s+", " ", text).strip()
                self.pairs.append(text)
                self._in_pair = False

    def handle_data(self, data: str) -> None:
        if self._in_pair:
            self._current.append(data)


def extract_pair_texts(html_path: str) -> dict[int, str]:
    parser = PairTextParser()
    parser.feed(Path(html_path).read_text(encoding="utf-8"))
    return {index + 1: text for index, text in enumerate(parser.pairs)}


def load_manifest(path: str) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("manifest must be valid JSON") from exc
    if not isinstance(data, list):
        raise ValueError("manifest root must be a JSON array")
    return data


def validate_manifest(entries: list[dict], pair_texts: dict[int, str], enforce_count: bool = True) -> list[str]:
    errors: list[str] = []
    seen_terms: set[str] = set()
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            errors.append(f"entry {index}: entry must be an object")
            continue

        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            errors.append(f"entry {index}: missing fields {sorted(missing)}")
            continue

        pair = entry["pair"]
        term = entry["term"]
        kind = entry["kind"]

        if entry["page"] != PAGE:
            errors.append(f"entry {index}: page must be {PAGE}")
        if type(pair) is not int or pair < 1:
            errors.append(f"entry {index}: pair must be a positive integer")
        else:
            expected_term = f"{TERM_PREFIX}{pair}"
            if pair not in pair_texts:
                errors.append(f"entry {index}: pair {pair} does not exist in {PAGE}")
            if not isinstance(term, str):
                errors.append(f"entry {index}: term must be {expected_term}")
            elif term != expected_term:
                errors.append(f"entry {index}: term must be {expected_term}")
            else:
                if term in seen_terms:
                    errors.append(f"entry {index}: duplicate term {term}")
                seen_terms.add(term)
        if not isinstance(kind, str) or kind not in VALID_KINDS:
            errors.append(f"entry {index}: invalid kind {kind}")
        if not str(entry["title"]).strip():
            errors.append(f"entry {index}: title is empty")

        body = str(entry["body"])
        if "Learning note" not in body:
            errors.append(f"entry {index}: body must contain heading Learning note")
        if len(re.sub(r"\s+", "", body)) < 40:
            errors.append(f"entry {index}: body is too short")

    if enforce_count and not 35 <= len(entries) <= 50:
        errors.append(f"manifest must contain 35-50 entries, found {len(entries)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--html", default="translation/ch03-convex-functions.html")
    args = parser.parse_args()

    try:
        entries = load_manifest(args.manifest)
        pair_texts = extract_pair_texts(args.html)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    errors = validate_manifest(entries, pair_texts)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"valid manifest: {len(entries)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
