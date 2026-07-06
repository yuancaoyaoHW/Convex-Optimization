import unittest

from translation._build_site_annotations import build_site_annotations


class BuildSiteAnnotationsTest(unittest.TestCase):
    def test_chapter_manifest_entries_become_site_annotations(self):
        entries = [{
            "page": "ch03-convex-functions.html",
            "pair": 13,
            "term": "ch03-convex-functions.html#pair-13",
            "kind": "example",
            "title": "Example 3.1 indicator function",
            "body": "Learning note\n\nConstraints become $I_C$.",
            "source_summary": "Example 3.1",
        }]

        annotations = build_site_annotations(entries)

        self.assertEqual(annotations, [{
            "page": "ch03-convex-functions.html",
            "pair": 13,
            "title": "Example 3.1 indicator function",
            "body": "Learning note\n\nConstraints become $I_C$.",
        }])


if __name__ == "__main__":
    unittest.main()
