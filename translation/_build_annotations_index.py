import re, os, json

BASE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["preface","ch01-introduction","ch02-convex-sets","ch03-convex-functions",
         "ch04-convex-problems","ch05-duality","ch06-approximation","ch07-statistical-estimation",
         "ch08-geometric-problems","ch09-unconstrained","ch10-equality-constrained",
         "ch11-interior-point","appendix-a","appendix-b","appendix-c"]

def extract_pairs(html):
    pairs = []
    chunks = re.split(r'(?=<div class="pair)', html)
    n = 0
    for chunk in chunks:
        if not re.match(r'<div class="pair', chunk):
            continue
        n += 1
        preview = "(无内容)"
        zh_m = re.search(r'<div class="zh">(.*?)</div>\s*</div>', chunk, re.S)
        if zh_m:
            zh = zh_m.group(1)
            pm = re.search(r'<(?:p|h[23456])[^>]*>(.*?)</(?:p|h[23456])>', zh, re.S)
            if pm:
                text = re.sub(r'<[^>]+>', '', pm.group(1)).strip()
                text = text.replace('\n',' ').replace('\r','')
                preview = text[:70] if text else "(空)"
        else:
            preview = "(图/无中文)"
        pairs.append({"n": n, "preview": preview})
    return pairs

pages = []
for stem in ORDER:
    fn = stem + ".html"
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        print("MISSING:", fn)
        continue
    html = open(p, encoding="utf-8").read()
    m = re.search(r'<title>(.*?)</title>', html)
    title = m.group(1) if m else fn
    pages.append({"page": fn, "title": title, "pairs": extract_pairs(html)})

out = {"pages": pages}
with open(os.path.join(BASE, "annotations-index.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("pages:", len(pages), "total pairs:", sum(len(p["pairs"]) for p in pages))
