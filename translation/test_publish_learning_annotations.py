import unittest

from translation._publish_learning_annotations import build_discussion_title, learning_note_body, plan_publication


class PublisherPlanningTests(unittest.TestCase):
    def test_build_discussion_title_uses_exact_term(self):
        entry = {"term": "ch03-convex-functions.html#pair-13", "title": "Example 3.1 indicator function"}
        self.assertEqual(
            build_discussion_title(entry),
            "ch03-convex-functions.html#pair-13 - Example 3.1 indicator function",
        )

    def test_learning_note_body_has_marker(self):
        entry = {"body": "Learning note\n\n鍐呭"}
        body = learning_note_body(entry)
        self.assertIn("<!-- codex-learning-note -->", body)
        self.assertIn("Learning note", body)

    def test_plan_publication_detects_create_update_and_skip(self):
        entries = [
            {"term": "term-a", "title": "A", "body": "Learning note\n\nA"},
            {"term": "term-b", "title": "B", "body": "Learning note\n\nB"},
            {"term": "term-c", "title": "C", "body": "Learning note\n\nC"},
        ]
        existing = {
            "term-b": {"discussion_id": "D_b", "comment_id": None, "comment_body": None},
            "term-c": {"discussion_id": "D_c", "comment_id": "C_c", "comment_body": learning_note_body(entries[2])},
        }
        plan = plan_publication(entries, existing)
        self.assertEqual([item["action"] for item in plan], ["create", "comment", "skip"])


if __name__ == "__main__":
    unittest.main()
