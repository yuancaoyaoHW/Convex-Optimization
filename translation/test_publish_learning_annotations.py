import unittest

from translation._publish_learning_annotations import (
    DISCUSSIONS_QUERY,
    DISCUSSION_COMMENTS_QUERY,
    MARKER,
    build_discussion_body,
    build_discussion_title,
    fetch_existing_discussions,
    learning_note_body,
    plan_publication,
    strict_hash_marker,
)


class PublisherPlanningTests(unittest.TestCase):
    def test_discussions_query_requests_comment_page_info_for_initial_page(self):
        normalized_query = " ".join(DISCUSSIONS_QUERY.split())
        self.assertIn("comments(first: 50)", normalized_query)
        self.assertIn(
            "comments(first: 50) { nodes { id body author { login } } pageInfo { hasNextPage endCursor } }",
            normalized_query,
        )

    def test_build_discussion_title_uses_exact_term(self):
        entry = {"term": "ch03-convex-functions.html#pair-13", "title": "Example 3.1 indicator function"}
        self.assertEqual(
            build_discussion_title(entry),
            "ch03-convex-functions.html#pair-13",
        )

    def test_build_discussion_body_includes_strict_hash_marker(self):
        entry = {"term": "ch03-convex-functions.html#pair-13", "title": "Example 3.1 indicator function"}
        body = build_discussion_body(entry)
        self.assertIn("# ch03-convex-functions.html#pair-13", body)
        self.assertIn(strict_hash_marker(entry["term"]), body)

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

    def test_plan_publication_syncs_suffixed_title_and_missing_strict_hash(self):
        entry = {"term": "ch03-convex-functions.html#pair-13", "title": "Example", "body": "Learning note\n\nA"}
        existing = {
            "ch03-convex-functions.html#pair-13": {
                "discussion_id": "D_13",
                "title": "ch03-convex-functions.html#pair-13 - Example",
                "body": "Created for Giscus term ch03-convex-functions.html#pair-13",
                "comment_id": "C_13",
                "comment_body": learning_note_body(entry),
            }
        }
        plan = plan_publication([entry], existing)
        self.assertEqual([item["action"] for item in plan], ["sync_discussion"])


class FetchExistingDiscussionsTests(unittest.TestCase):
    def test_fetch_existing_discussions_matches_exact_title_term(self):
        calls = []

        def fake_graphql(token, query, variables):
            calls.append((query, variables))
            self.assertEqual(variables["cursor"], None)
            return {
                "data": {
                    "repository": {
                        "discussions": {
                            "nodes": [
                                {
                                    "id": "D10",
                                    "title": "ch03-convex-functions.html#pair-10 - Pair 10 title",
                                    "comments": {
                                        "nodes": [{"id": "C10", "body": MARKER + "\n\npair 10"}],
                                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                                    },
                                },
                                {
                                    "id": "D1",
                                    "title": "ch03-convex-functions.html#pair-1 - Pair 1 title",
                                    "comments": {
                                        "nodes": [{"id": "C1", "body": MARKER + "\n\npair 1"}],
                                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                                    },
                                },
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }

        existing = fetch_existing_discussions(
            "token",
            {"ch03-convex-functions.html#pair-1"},
            graphql_fn=fake_graphql,
        )

        self.assertEqual(list(existing.keys()), ["ch03-convex-functions.html#pair-1"])
        self.assertEqual(existing["ch03-convex-functions.html#pair-1"]["discussion_id"], "D1")
        self.assertEqual(len(calls), 1)

    def test_fetch_existing_discussions_paginates_comments_until_marker_found(self):
        calls = []

        def fake_graphql(token, query, variables):
            calls.append((query, variables.copy()))
            if query == DISCUSSION_COMMENTS_QUERY:
                self.assertEqual(variables["discussionId"], "D1")
                if variables["cursor"] is None:
                    return {
                        "data": {
                            "node": {
                                "comments": {
                                    "nodes": [{"id": "C0", "body": "plain comment"}],
                                    "pageInfo": {"hasNextPage": True, "endCursor": "comment-cursor-1"},
                                }
                            }
                        }
                    }
                self.assertEqual(variables["cursor"], "comment-cursor-1")
                return {
                    "data": {
                        "node": {
                            "comments": {
                                "nodes": [{"id": "C1", "body": MARKER + "\n\npaged note"}],
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                            }
                        }
                    }
                }

            self.assertIsNone(variables["cursor"])
            return {
                "data": {
                    "repository": {
                        "discussions": {
                            "nodes": [
                                {
                                    "id": "D1",
                                    "title": "term-1 - Example title",
                                    "comments": {
                                        "nodes": [{"id": "Cx", "body": "plain comment"}],
                                        "pageInfo": {"hasNextPage": True, "endCursor": "comment-cursor-1"},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }

        existing = fetch_existing_discussions("token", {"term-1"}, graphql_fn=fake_graphql)

        self.assertEqual(existing["term-1"]["comment_id"], "C1")
        self.assertEqual(existing["term-1"]["comment_body"], MARKER + "\n\npaged note")
        self.assertEqual(
            [variables["cursor"] for query, variables in calls if query == DISCUSSION_COMMENTS_QUERY],
            ["comment-cursor-1"],
        )


if __name__ == "__main__":
    unittest.main()
