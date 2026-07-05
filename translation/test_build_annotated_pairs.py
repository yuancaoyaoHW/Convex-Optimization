import unittest

from translation import _build_annotated_pairs as builder


class BuildAnnotatedPairsTest(unittest.TestCase):
    def test_discussion_title_with_learning_suffix_keeps_giscus_term(self):
        self.assertEqual(
            builder.parse_discussion_title("ch03-convex-functions.html#pair-312 - 视角切换"),
            ("ch03-convex-functions.html", 312),
        )


if __name__ == "__main__":
    unittest.main()
