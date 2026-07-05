#!/usr/bin/env python3
"""Publish learning annotation manifest entries to GitHub Discussions."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    from _ch03_annotation_manifest import extract_pair_texts, load_manifest, validate_manifest
except ImportError:
    from translation._ch03_annotation_manifest import extract_pair_texts, load_manifest, validate_manifest

API = "https://api.github.com/graphql"
OWNER = "yuancaoyaoHW"
REPO = "Convex-Optimization"
MARKER = "<!-- codex-learning-note -->"


def graphql(token: str, query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "ch03-learning-annotation-publisher",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub GraphQL HTTP {exc.code}: {detail}") from exc
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
    return data


def build_discussion_title(entry: dict) -> str:
    return f"{entry['term']} - {entry['title']}"


def learning_note_body(entry: dict) -> str:
    body = entry["body"].strip()
    if MARKER in body:
        return body
    return MARKER + "\n\n" + body


def plan_publication(entries: list[dict], existing: dict[str, dict]) -> list[dict]:
    plan = []
    for entry in entries:
        found = existing.get(entry["term"])
        desired = learning_note_body(entry)
        if not found:
            action = "create"
        elif not found.get("comment_id"):
            action = "comment"
        elif (found.get("comment_body") or "").strip() != desired.strip():
            action = "update"
        else:
            action = "skip"
        plan.append({"action": action, "entry": entry, "existing": found})
    return plan


REPO_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
  }
}
"""

DISCUSSIONS_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        comments(first: 50) {
          nodes {
            id
            body
            author { login }
          }
        }
      }
    }
  }
}
"""

DISCUSSION_COMMENTS_QUERY = """
query($discussionId: ID!, $cursor: String) {
  node(id: $discussionId) {
    ... on Discussion {
      comments(first: 50, after: $cursor) {
        nodes {
          id
          body
          author { login }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

CREATE_DISCUSSION = """
mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
    discussion { id title }
  }
}
"""

ADD_COMMENT = """
mutation($discussionId: ID!, $body: String!) {
  addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
    comment { id }
  }
}
"""

UPDATE_COMMENT = """
mutation($commentId: ID!, $body: String!) {
  updateDiscussionComment(input: {commentId: $commentId, body: $body}) {
    comment { id }
  }
}
"""


def load_giscus_config(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_repo_id(token: str) -> str:
    data = graphql(token, REPO_QUERY, {"owner": OWNER, "name": REPO})
    return data["data"]["repository"]["id"]


def discussion_term_from_title(title: str) -> str:
    if " - " in title:
        return title.split(" - ", 1)[0]
    return title


def find_marked_comment(comments: dict) -> dict | None:
    for comment in comments["nodes"]:
        if MARKER in comment.get("body", ""):
            return comment
    return None


def fetch_marked_comment(token: str, discussion_id: str, initial_comments: dict, graphql_fn=graphql) -> dict | None:
    marked = find_marked_comment(initial_comments)
    if marked or not initial_comments["pageInfo"]["hasNextPage"]:
        return marked

    cursor = initial_comments["pageInfo"]["endCursor"]
    while True:
        data = graphql_fn(token, DISCUSSION_COMMENTS_QUERY, {"discussionId": discussion_id, "cursor": cursor})
        comments = data["data"]["node"]["comments"]
        marked = find_marked_comment(comments)
        if marked:
            return marked
        if not comments["pageInfo"]["hasNextPage"]:
            return None
        cursor = comments["pageInfo"]["endCursor"]


def fetch_existing_discussions(token: str, terms: set[str], graphql_fn=graphql) -> dict[str, dict]:
    existing: dict[str, dict] = {}
    cursor = None
    while True:
        data = graphql_fn(token, DISCUSSIONS_QUERY, {"owner": OWNER, "name": REPO, "cursor": cursor})
        discussions = data["data"]["repository"]["discussions"]
        for node in discussions["nodes"]:
            term = discussion_term_from_title(node["title"])
            if term not in terms:
                continue
            marked = fetch_marked_comment(token, node["id"], node["comments"], graphql_fn=graphql_fn)
            existing[term] = {
                "discussion_id": node["id"],
                "comment_id": marked["id"] if marked else None,
                "comment_body": marked["body"] if marked else None,
            }
        page_info = discussions["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return existing


def apply_plan(token: str, config: dict, repo_id: str, plan: list[dict], dry_run: bool) -> None:
    for item in plan:
        entry = item["entry"]
        action = item["action"]
        print(f"{action}: {entry['term']} {entry['title']}")
        if dry_run or action == "skip":
            continue
        body = learning_note_body(entry)
        if action == "create":
            created = graphql(
                token,
                CREATE_DISCUSSION,
                {
                    "repositoryId": repo_id,
                    "categoryId": config["categoryId"],
                    "title": build_discussion_title(entry),
                    "body": "Created for Giscus term " + entry["term"],
                },
            )
            discussion_id = created["data"]["createDiscussion"]["discussion"]["id"]
            graphql(token, ADD_COMMENT, {"discussionId": discussion_id, "body": body})
        elif action == "comment":
            graphql(token, ADD_COMMENT, {"discussionId": item["existing"]["discussion_id"], "body": body})
        elif action == "update":
            graphql(token, UPDATE_COMMENT, {"commentId": item["existing"]["comment_id"], "body": body})
        else:
            raise RuntimeError(f"unknown action {action}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--config", default="translation/giscus-config.json")
    parser.add_argument("--html", default="translation/ch03-convex-functions.html")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    entries = load_manifest(args.manifest)
    errors = validate_manifest(entries, extract_pair_texts(args.html))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GH_TOKEN or GITHUB_TOKEN is required", file=sys.stderr)
        return 1

    config = load_giscus_config(args.config)
    existing = fetch_existing_discussions(token, {entry["term"] for entry in entries})
    plan = plan_publication(entries, existing)
    repo_id = None if args.dry_run else fetch_repo_id(token)
    apply_plan(token, config, repo_id, plan, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
