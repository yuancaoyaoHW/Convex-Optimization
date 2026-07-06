#!/usr/bin/env python3
"""Build static site annotations from reviewed annotation manifests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_site_annotations(entries: list[dict]) -> list[dict]:
    annotations = []
    for entry in entries:
        annotations.append({
            "page": entry["page"],
            "pair": entry["pair"],
            "title": entry["title"],
            "body": entry["body"],
        })
    return annotations


def load_entries(paths: list[str]) -> list[dict]:
    entries: list[dict] = []
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path} must contain a JSON array")
        entries.extend(data)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifests",
        nargs="*",
        default=["docs/annotations/ch03-learning-annotations.json"],
    )
    parser.add_argument("--output", default="translation/annotations.json")
    args = parser.parse_args()

    annotations = build_site_annotations(load_entries(args.manifests))
    Path(args.output).write_text(
        json.dumps(annotations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"site annotations: {len(annotations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
