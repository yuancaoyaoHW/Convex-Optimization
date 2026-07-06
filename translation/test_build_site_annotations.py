import unittest

from translation._build_site_annotations import DEFAULT_MANIFESTS, build_site_annotations


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

    def test_default_manifests_include_chapter_four(self):
        self.assertIn("docs/annotations/ch03-learning-annotations.json", DEFAULT_MANIFESTS)
        self.assertIn("docs/annotations/ch04-learning-annotations.json", DEFAULT_MANIFESTS)
        self.assertIn("docs/annotations/ch05-learning-annotations.json", DEFAULT_MANIFESTS)
        self.assertIn("docs/annotations/ch06-learning-annotations.json", DEFAULT_MANIFESTS)
        self.assertIn("docs/annotations/ch07-learning-annotations.json", DEFAULT_MANIFESTS)
        self.assertIn("docs/annotations/ch08-learning-annotations.json", DEFAULT_MANIFESTS)
        self.assertIn("docs/annotations/ch09-learning-annotations.json", DEFAULT_MANIFESTS)


if __name__ == "__main__":
    unittest.main()
