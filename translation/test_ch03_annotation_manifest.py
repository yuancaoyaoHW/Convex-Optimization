import json
import tempfile
import unittest
from pathlib import Path

from translation._ch03_annotation_manifest import extract_pair_texts, load_manifest, validate_manifest


class ManifestValidationTests(unittest.TestCase):
    def test_extract_pair_texts_counts_chapter_pairs(self):
        pairs = extract_pair_texts("translation/ch03-convex-functions.html")
        self.assertEqual(len(pairs), 321)
        self.assertIn(13, pairs)
        self.assertIn("Example 3.1", pairs[13])

    def test_manifest_validation_accepts_valid_entry(self):
        entries = [{
            "page": "ch03-convex-functions.html",
            "pair": 13,
            "term": "ch03-convex-functions.html#pair-13",
            "kind": "example",
            "title": "Example 3.1 indicator function",
            "body": "Learning note\n\nConstraints can be represented as an indicator function.",
            "source_summary": "Example 3.1 Indicator function"
        }]
        errors = validate_manifest(entries, {13: "Example 3.1 Indicator function"}, enforce_count=False)
        self.assertEqual(errors, [])

    def test_manifest_validation_rejects_bad_term(self):
        entries = [{
            "page": "ch03-convex-functions.html",
            "pair": 13,
            "term": "ch03-convex-functions.html#pair-99",
            "kind": "example",
            "title": "Bad term",
            "body": "Learning note\n\nTerm does not match pair.",
            "source_summary": "Example 3.1"
        }]
        errors = validate_manifest(entries, {13: "Example 3.1"}, enforce_count=False)
        self.assertTrue(any("term must be" in error for error in errors))

    def test_load_manifest_requires_json_array(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps({"entries": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(str(path))


if __name__ == "__main__":
    unittest.main()
