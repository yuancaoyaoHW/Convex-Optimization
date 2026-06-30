#!/usr/bin/env python3
"""Query GitHub Discussions via GraphQL, emit annotated-pairs.json.

Lists all discussions in the repo, keeps those whose title matches the
giscus term format `<page>#pair-<n>` and have >=1 comment. Writes the
result to annotated-pairs.json next to this script.

Run in GitHub Actions with GITHUB_TOKEN available. Local testing needs
a personal access token with `read:discussion` scope in GH_TOKEN.
"""
import json, os, sys, re, urllib.request, urllib.error

REPO_OWNER = "yuancaoyaoHW"
REPO_NAME = "Convex-Optimization"
API = "https://api.github.com/graphql"
TERM_RE = re.compile(r"^(.+\.html)#pair-(\d+)$")

QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        title
        number
        comments { totalCount }
      }
    }
  }
}
"""

def run_query(token, variables):
    body = json.dumps({"query": QUERY, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "annotation-index-builder",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.stderr.write("GITHUB_TOKEN env var required\n")
        return 1

    pairs = []
    cursor = None
    pages = 0
    while True:
        pages += 1
        data = run_query(token, {"owner": REPO_OWNER, "name": REPO_NAME, "cursor": cursor})
        disc = data.get("data", {}).get("repository", {}).get("discussions", {})
        if disc is None:
            sys.stderr.write("repository.discussions is null — token may lack discussion read scope\n")
            sys.stderr.write("response: %s\n" % json.dumps(data)[:300])
            return 1
        for node in disc.get("nodes", []):
            title = node.get("title", "")
            m = TERM_RE.match(title)
            if not m:
                continue
            n_comments = node.get("comments", {}).get("totalCount", 0)
            if n_comments > 0:
                pairs.append({
                    "page": m.group(1),
                    "pair": int(m.group(2)),
                    "comments": n_comments,
                })
        info = disc.get("pageInfo", {})
        if not info.get("hasNextPage"):
            break
        cursor = info.get("endCursor")
        if pages > 30:
            sys.stderr.write("safety: >30 pages, aborting\n")
            break

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "annotated-pairs.json")
    pairs.sort(key=lambda p: (p["page"], p["pair"]))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"pairs": pairs}, f, ensure_ascii=False, indent=2)
    print("annotated pairs: %d (pages queried: %d)" % (len(pairs), pages))
    return 0

if __name__ == "__main__":
    sys.exit(main())
