# Chapter 3 Giscus Learning Annotations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a reviewed first pass of 35-50 Chapter 3 learning annotations into the existing Giscus Discussions workflow and verify that the live page renders them correctly.

**Architecture:** Keep the chapter HTML unchanged. Add a reviewable manifest under `docs/annotations/`, add small stdlib Python tooling under `translation/` to validate and publish the manifest through GitHub GraphQL, then refresh the existing `translation/annotated-pairs.json` index. Rendering verification is captured in a Markdown report so future batches can reuse the same workflow.

**Tech Stack:** Static HTML, existing Giscus embed in `translation/assets/annotations.js`, Python 3 standard library, GitHub GraphQL API, existing GitHub Pages deployment workflow.

## Global Constraints

- Scope is `translation/ch03-convex-functions.html` only.
- First pass contains 35-50 high-value `.pair` blocks, not all 321 pairs.
- Every manifest entry uses term format `ch03-convex-functions.html#pair-N`.
- Do not rewrite the Chapter 3 bilingual HTML text.
- Do not change the Giscus modal UI unless rendering verification reveals a blocking layout issue.
- Preserve existing reader comments; do not delete or overwrite unrelated discussion content.
- Stop before publication if GitHub API authentication is unavailable.
- Prefer conservative Markdown: inline `$...$` math where possible, displayed `$$...$$` only when needed, no complex aligned environments.
- Rendering checks must cover desktop and mobile widths on the live GitHub Pages page.

---

## File Structure

- Create `docs/annotations/ch03-learning-annotations.json`: source-of-truth manifest with 40 selected learning annotations.
- Create `docs/annotations/ch03-rendering-check.md`: checklist and results for live rendering checks.
- Create `translation/_ch03_annotation_manifest.py`: extraction and validation helpers for Chapter 3 `.pair` blocks and manifest entries.
- Create `translation/_publish_learning_annotations.py`: GitHub GraphQL publisher with dry-run support.
- Create `translation/test_ch03_annotation_manifest.py`: stdlib unit tests for manifest validation.
- Create `translation/test_publish_learning_annotations.py`: stdlib unit tests for publisher query/mutation planning with a fake GraphQL client.
- Modify `translation/annotated-pairs.json`: only after publication, by running the existing `translation/_build_annotated_pairs.py`.

## Task 1: Manifest Validation Helpers

**Files:**
- Create: `translation/_ch03_annotation_manifest.py`
- Create: `translation/test_ch03_annotation_manifest.py`

**Interfaces:**
- Consumes: `translation/ch03-convex-functions.html`, `docs/annotations/ch03-learning-annotations.json`
- Produces:
  - `extract_pair_texts(html_path: str) -> dict[int, str]`
  - `load_manifest(path: str) -> list[dict]`
  - `validate_manifest(entries: list[dict], pair_texts: dict[int, str], enforce_count: bool = True) -> list[str]`
  - CLI: `python translation/_ch03_annotation_manifest.py docs/annotations/ch03-learning-annotations.json`

- [ ] **Step 1: Write failing tests**

Create `translation/test_ch03_annotation_manifest.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest translation.test_ch03_annotation_manifest -v
```

Expected: FAIL because `_ch03_annotation_manifest` does not exist.

- [ ] **Step 3: Implement validation helpers**

Create `translation/_ch03_annotation_manifest.py`:

```python
#!/usr/bin/env python3
"""Validate Chapter 3 learning annotation manifests."""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

PAGE = "ch03-convex-functions.html"
TERM_PREFIX = PAGE + "#pair-"
VALID_KINDS = {
    "definition",
    "example",
    "condition",
    "geometry",
    "operation",
    "conjugate",
    "quasiconvex",
    "log-concave",
    "generalized",
}
REQUIRED_FIELDS = {"page", "pair", "term", "kind", "title", "body", "source_summary"}


class PairTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_pair = False
        self.depth = 0
        self.current: list[str] = []
        self.pairs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()
        if tag == "div" and "pair" in classes and not self.in_pair:
            self.in_pair = True
            self.depth = 1
            self.current = []
            return
        if self.in_pair:
            if tag == "div":
                self.depth += 1
            if tag in {"h2", "h3", "p", "li", "strong", "em"}:
                self.current.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if not self.in_pair:
            return
        if tag in {"h2", "h3", "p", "li"}:
            self.current.append(" ")
        if tag == "div":
            self.depth -= 1
            if self.depth == 0:
                text = unescape(" ".join("".join(self.current).split()))
                self.pairs.append(text)
                self.in_pair = False

    def handle_data(self, data: str) -> None:
        if self.in_pair:
            self.current.append(data)


def extract_pair_texts(html_path: str) -> dict[int, str]:
    parser = PairTextParser()
    parser.feed(Path(html_path).read_text(encoding="utf-8"))
    return {index + 1: text for index, text in enumerate(parser.pairs)}


def load_manifest(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("manifest root must be a JSON array")
    return data


def validate_manifest(entries: list[dict], pair_texts: dict[int, str], enforce_count: bool = True) -> list[str]:
    errors: list[str] = []
    seen_terms: set[str] = set()
    for index, entry in enumerate(entries, 1):
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            errors.append(f"entry {index}: missing fields {sorted(missing)}")
            continue
        pair = entry["pair"]
        term = entry["term"]
        expected_term = f"{TERM_PREFIX}{pair}"
        if entry["page"] != PAGE:
            errors.append(f"entry {index}: page must be {PAGE}")
        if not isinstance(pair, int) or pair < 1:
            errors.append(f"entry {index}: pair must be a positive integer")
        elif pair not in pair_texts:
            errors.append(f"entry {index}: pair {pair} does not exist in {PAGE}")
        if term != expected_term:
            errors.append(f"entry {index}: term must be {expected_term}")
        if term in seen_terms:
            errors.append(f"entry {index}: duplicate term {term}")
        seen_terms.add(term)
        if entry["kind"] not in VALID_KINDS:
            errors.append(f"entry {index}: invalid kind {entry['kind']}")
        if not str(entry["title"]).strip():
            errors.append(f"entry {index}: title is empty")
        body = str(entry["body"])
        if "Learning note" not in body:
            errors.append(f"entry {index}: body must contain heading Learning note")
        if len(re.sub(r"\s+", "", body)) < 40:
            errors.append(f"entry {index}: body is too short")
    if enforce_count and not 35 <= len(entries) <= 50:
        errors.append(f"manifest must contain 35-50 entries, found {len(entries)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--html", default="translation/ch03-convex-functions.html")
    args = parser.parse_args()
    entries = load_manifest(args.manifest)
    errors = validate_manifest(entries, extract_pair_texts(args.html))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"valid manifest: {len(entries)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and validation helper**

Run:

```powershell
python -m unittest translation.test_ch03_annotation_manifest -v
```

Expected: PASS, 4 tests.

Run:

```powershell
python translation/_ch03_annotation_manifest.py docs/annotations/ch03-learning-annotations.json
```

Expected before Task 2: FAIL because the manifest file does not exist.

- [ ] **Step 5: Commit**

```powershell
git add translation/_ch03_annotation_manifest.py translation/test_ch03_annotation_manifest.py
git commit -m "Add chapter 3 annotation manifest validation"
```

## Task 2: Author the Chapter 3 Learning Annotation Manifest

**Files:**
- Create: `docs/annotations/ch03-learning-annotations.json`

**Interfaces:**
- Consumes: `translation/_ch03_annotation_manifest.py`
- Produces: a validated manifest with 40 entries for later publication

- [ ] **Step 1: Create manifest directory**

Run:

```powershell
New-Item -ItemType Directory -Force docs/annotations
```

Expected: directory exists.

- [ ] **Step 2: Create the manifest**

Create `docs/annotations/ch03-learning-annotations.json` as a JSON array. Use exactly 40 objects with these `pair` values:

```text
3, 5, 8, 13, 17, 30, 35, 57, 62, 65,
71, 78, 90, 92, 96, 102, 103, 112, 117, 126,
130, 141, 146, 148, 150, 162, 169, 170, 174, 176,
197, 208, 226, 253, 256, 263, 278, 289, 301, 312
```

For each object, use:

```json
{
  "page": "ch03-convex-functions.html",
  "pair": 3,
  "term": "ch03-convex-functions.html#pair-3",
  "kind": "definition",
  "title": "Convex function definition",
  "body": "Learning note\n\n抓住这一定义时，先看两层：定义域本身要是凸集，函数值还要满足“中点不高于端点线性插值”。几何上就是弦在图像上方。后面一阶条件、Jensen 不等式、上图刻画都在重写同一个核心想法。",
  "source_summary": "Convex function definition and chord interpretation"
}
```

Then fill the remaining 39 objects with these exact titles, kinds, and bodies. For each remaining object, set `page` to `ch03-convex-functions.html`, set `term` to `ch03-convex-functions.html#pair-N`, and set `source_summary` to the same text as `title`.

```text
pair 5, kind definition, title "Affine equality case", body "Learning note\n\n仿射函数既凸又凹，因为插值时函数值完全等于端点值的插值。这个例子是判断很多规则的基准：如果一个证明在仿射函数上不能退化成等号，通常说明方向或符号写反了。"
pair 8, kind definition, title "Restriction to lines", body "Learning note\n\n把多维凸性限制到任意直线，是把复杂问题降到一维的常用入口。实践中检查 Hessian、证明复合规则、研究拟凸性时，很多论证都是先沿直线看 $g(t)=f(x+tv)$。"
pair 13, kind example, title "Example 3.1 indicator function", body "Learning note\n\n指示函数把“约束集合”变成“目标函数的一部分”：在集合内代价为 0，集合外代价为 $\\infty$。这让带约束最小化可以写成无约束形式 $f+I_C$，是后面对偶和近端方法里的基础语言。"
pair 17, kind condition, title "First-order condition", body "Learning note\n\n一阶条件说切平面是全局下界，而不只是局部近似。凸优化中“局部信息推出全局结论”的魔法基本从这里来：若 $\\nabla f(x)=0$，立刻得到 $x$ 是全局最小点。"
pair 30, kind condition, title "Second-order condition", body "Learning note\n\n二阶条件把凸性翻译成曲率非负：$\\nabla^2 f(x)\\succeq0$。注意严格凸不等于处处 Hessian 正定；正定是强而方便的充分条件，很多严格凸函数会在某些点曲率退化。"
pair 35, kind example, title "Example 3.2 quadratic functions", body "Learning note\n\n二次函数是 Hessian 判据的标准样本：$f(x)=\\frac12x^TPx+q^Tx+r$ 的凸性只看 $P\\succeq0$。线性项和常数项会平移或倾斜图像，但不改变曲率。"
pair 57, kind geometry, title "Sublevel sets", body "Learning note\n\n凸函数的下水平集一定凸，所以“函数凸”能推出“阈值以下的可行区域凸”。反过来不成立；所有下水平集凸只说明拟凸。这个区别在 3.4 节会正式出现。"
pair 62, kind geometry, title "Epigraph definition", body "Learning note\n\n上图把函数问题变成集合问题：$\\mathrm{epi}\\,f$ 是图像以上的所有点。很多函数凸性的证明并不直接算不等式，而是证明上图是凸集。"
pair 65, kind example, title "Example 3.4 matrix fractional function", body "Learning note\n\n矩阵分式函数 $x^TY^{-1}x$ 看起来非线性很强，但它的上图能通过 Schur 补写成线性矩阵不等式。这里展示了一个重要套路：把难函数转成半正定块矩阵条件。"
pair 71, kind condition, title "Jensen inequality", body "Learning note\n\nJensen 不等式是凸性定义的多点版本：函数作用在平均值上，不超过函数值的平均。它既是证明不等式的工具，也是概率期望形式 $f(E X)\\le E f(X)$ 的来源。"
pair 78, kind condition, title "AM-GM from Jensen", body "Learning note\n\n这里的重点不是 AM-GM 本身，而是选函数的眼光：用凸函数 $-\\log x$ 把乘积关系变成和的关系。很多经典不等式都可以看成“挑对凸函数后套 Jensen”。"
pair 90, kind operation, title "Example 3.5 pointwise maximum", body "Learning note\n\n若干仿射函数的逐点最大值是凸的，所以分段线性凸函数可以看成许多平面的上包络。支持向量机、最大损失、鲁棒约束里都会反复出现这种结构。"
pair 92, kind operation, title "Example 3.6 sum of largest components", body "Learning note\n\n“最大的 $r$ 个分量之和”凸，是因为它可以写成很多线性函数的最大值。这个例子训练一种视角：排序函数虽然不光滑，但常常能通过上确界或最大值证明凸性。"
pair 96, kind operation, title "Example 3.7 support function", body "Learning note\n\n支撑函数 $S_C(x)=\\sup_{y\\in C}x^Ty$ 把集合 $C$ 的方向宽度编码成函数。它总是凸的，即使 $C$ 本身不凸；因为对固定 $y$，$x^Ty$ 是仿射函数。"
pair 102, kind example, title "Example 3.10 maximum eigenvalue", body "Learning note\n\n最大特征值可写成 Rayleigh 商的上确界：$\\lambda_{\\max}(X)=\\sup_{\\|u\\|=1}u^TXu$。对固定 $u$ 这是 $X$ 的线性函数，所以上确界给出凸性。"
pair 103, kind example, title "Example 3.11 spectral norm", body "Learning note\n\n谱范数是最大奇异值，也能写成双线性表达的上确界。这个例子和最大特征值平行：矩阵函数的凸性常常不是靠展开元素，而是靠变分表示。"
pair 112, kind operation, title "Composition rules motivation", body "Learning note\n\n复合规则回答的是：已知 $h$ 和 $g$ 的曲率，什么时候 $h(g(x))$ 仍然凸？这里最容易错的是单调性条件；外层函数是否递增，决定内层凸性的不等式方向能否传递。"
pair 117, kind operation, title "Scalar composition theorem", body "Learning note\n\n标量复合的口诀：凸且非减的外函数可以吃凸函数；凸且非增的外函数可以吃凹函数。不要只记“凸套凸仍凸”，它少了关键的单调性限制。"
pair 126, kind example, title "Example 3.13 simple composition", body "Learning note\n\n这些例子是复合规则的速查表。读时把每个函数拆成外层 $h$ 和内层 $g$，逐项检查“外层曲率、外层单调性、内层曲率”，比直接求 Hessian 更稳。"
pair 130, kind operation, title "Vector composition", body "Learning note\n\n向量复合把标量规则推广到多个内层函数 $g_i$。核心仍是外层 $h$ 对每个坐标的单调性：哪个坐标非减，就允许对应的 $g_i$ 是凸；哪个坐标非增，就允许对应的 $g_i$ 是凹。"
pair 141, kind example, title "Example 3.15 Schur complement", body "Learning note\n\n这个例子把“对某个变量取下确界保持凸性”和 Schur 补连接起来。消去变量 $y$ 后得到的函数仍凸，背后是凸上图在投影下仍为凸集。"
pair 146, kind operation, title "Perspective function", body "Learning note\n\n透视函数 $g(x,t)=t f(x/t)$ 是把函数放到齐次坐标里看。许多分式形态的凸性都来自它，例如 $x^Tx/t$ 和相对熵。记住条件 $t>0$，否则表达式没有意义。"
pair 148, kind example, title "Example 3.18 norm squared perspective", body "Learning note\n\n$\\|x\\|_2^2/t$ 的凸性不是偶然的，它是平方范数的透视函数。优化里这类项常出现在二阶锥、方差归一化和分式目标中。"
pair 150, kind example, title "Example 3.19 negative log perspective", body "Learning note\n\n相对熵来自 $-\\log x$ 的透视函数。这个例子值得记：信息论里的 KL divergence 可以被凸分析统一处理，后面遇到熵正则化和概率模型时会很有用。"
pair 162, kind conjugate, title "Example 3.21 one-dimensional conjugates", body "Learning note\n\n共轭函数 $f^*(y)=\\sup_x(yx-f(x))$ 衡量线性函数 $yx$ 能超过 $f$ 多少。计算时最重要的是定义域：若上确界无界，结果就是 $\\infty$，不是“没有答案”。"
pair 169, kind conjugate, title "Example 3.24 indicator conjugate", body "Learning note\n\n集合指示函数的共轭就是支撑函数。这条关系把“约束集合”和“支持超平面”接起来，是对偶问题里约束变成支撑函数或共轭项的核心机制。"
pair 170, kind conjugate, title "Example 3.25 log-sum-exp conjugate", body "Learning note\n\nlog-sum-exp 的共轭把变量限制到概率单纯形，并产生负熵形式。这解释了为什么 softmax、熵和概率权重经常一起出现：它们是同一对共轭结构的两面。"
pair 174, kind conjugate, title "Example 3.26 norm conjugate", body "Learning note\n\n范数的共轭是对偶范数单位球的指示函数。直觉是：线性函数 $y^Tx$ 若被 $\\|x\\|$ 控住，需要 $\\|y\\|_*\\le1$；否则沿某个方向放大就会无界。"
pair 176, kind conjugate, title "Example 3.27 norm squared conjugate", body "Learning note\n\n平方范数的共轭仍是平方范数，只是换成对偶范数：$\\frac12\\|x\\|^2$ 对应 $\\frac12\\|y\\|_*^2$。这比范数本身更平滑，所以在正则化和对偶推导里更好用。"
pair 197, kind quasiconvex, title "Quasiconvex definition", body "Learning note\n\n拟凸函数不要求弦在图像上方，只要求所有下水平集是凸的。它保留了“低于某个阈值的可行区域好处理”这一点，因此常用于可行性二分和准凸优化。"
pair 208, kind quasiconvex, title "Example 3.32 linear-fractional function", body "Learning note\n\n线性分式函数同时拟凸和拟凹，因为它的下水平集和上水平集都能化成线性不等式。分式规划里常见的可处理性，很多就来自这种水平集视角。"
pair 226, kind quasiconvex, title "First-order quasiconvex condition", body "Learning note\n\n拟凸的一阶条件不是切平面全局下界，而是：若 $y$ 的函数值不高于 $x$，梯度方向不能指向 $y$。它描述的是下水平集边界的支撑超平面。"
pair 253, kind quasiconvex, title "Example 3.38 convex over concave", body "Learning note\n\n凸函数除以正的凹函数通常不是凸函数，但它是拟凸函数。证明看下水平集：$p(x)/q(x)\\le t$ 等价于 $p(x)-tq(x)\\le0$，这是凸函数的下水平集。"
pair 256, kind log-concave, title "Log-concavity definition", body "Learning note\n\n对数凹把乘法结构转成加法结构：$\\log f$ 凹意味着 $f$ 在几何平均意义下表现良好。概率密度、体积和良率问题常用它，因为积分和边缘化有很好的保持性。"
pair 263, kind log-concave, title "Example 3.40 log-concave densities", body "Learning note\n\n高斯密度对数凹，所以很多高斯概率区域会继承凸性或拟凸性性质。这里的重点是：概率模型的形状可以通过 $\\log f$ 的凹性进入凸优化工具箱。"
pair 278, kind log-concave, title "Integration of log-concave functions", body "Learning note\n\n对数函函数在积分下的保持性很强：联合对数凹函数边缘化后仍对数凹。概率论里这意味着很多边缘分布、命中概率和体积函数仍保留可优化结构。"
pair 289, kind generalized, title "Monotonicity under generalized inequalities", body "Learning note\n\n$K$-单调性把普通的“逐点变大”换成锥诱导的偏序。读这一节时先问：哪个锥定义了“更大”？在矩阵场景里，这个锥通常是半正定锥。"
pair 301, kind generalized, title "Example 3.48 matrix convexity", body "Learning note\n\n矩阵凸性要求不等式按半正定序成立，比逐元素凸更强。一个实用判据是：对所有向量 $z$，标量函数 $z^Tf(x)z$ 凸；这把矩阵不等式拉回标量凸性。"
pair 312, kind generalized, title "Example 3.49 quadratic matrix function", body "Learning note\n\n这个例子把 $K$-凸复合规则和 $-\\log\\det$ 连接起来。复杂矩阵表达式的凸性往往不是直接展开证明，而是识别出半正定序、矩阵凹性和单调复合。"
```

- [ ] **Step 3: Validate manifest**

Run:

```powershell
python translation/_ch03_annotation_manifest.py docs/annotations/ch03-learning-annotations.json
```

Expected: `valid manifest: 40 entries`.

- [ ] **Step 4: Commit**

```powershell
git add docs/annotations/ch03-learning-annotations.json
git commit -m "Add chapter 3 learning annotation manifest"
```

## Task 3: GitHub Discussions Publisher

**Files:**
- Create: `translation/_publish_learning_annotations.py`
- Create: `translation/test_publish_learning_annotations.py`

**Interfaces:**
- Consumes: `docs/annotations/ch03-learning-annotations.json`, `translation/giscus-config.json`, `GH_TOKEN` or `GITHUB_TOKEN`
- Produces:
  - Dry-run publication plan
  - Published or updated Giscus Discussion comments headed `Learning note`
  - CLI: `python translation/_publish_learning_annotations.py docs/annotations/ch03-learning-annotations.json --dry-run`

- [ ] **Step 1: Write failing tests**

Create `translation/test_publish_learning_annotations.py`:

```python
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
        entry = {"body": "Learning note\n\n内容"}
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest translation.test_publish_learning_annotations -v
```

Expected: FAIL because `_publish_learning_annotations` does not exist.

- [ ] **Step 3: Implement publisher**

Create `translation/_publish_learning_annotations.py` with:

```python
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


def fetch_existing_discussions(token: str, terms: set[str]) -> dict[str, dict]:
    existing: dict[str, dict] = {}
    cursor = None
    while True:
        data = graphql(token, DISCUSSIONS_QUERY, {"owner": OWNER, "name": REPO, "cursor": cursor})
        discussions = data["data"]["repository"]["discussions"]
        for node in discussions["nodes"]:
            matching_terms = [term for term in terms if term in node["title"]]
            if not matching_terms:
                continue
            if len(matching_terms) > 1:
                raise RuntimeError(f"ambiguous discussion title: {node['title']}")
            term = matching_terms[0]
            marked = None
            for comment in node["comments"]["nodes"]:
                if MARKER in comment.get("body", ""):
                    marked = comment
                    break
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
    repo_id = fetch_repo_id(token)
    apply_plan(token, config, repo_id, plan, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m unittest translation.test_publish_learning_annotations -v
python -m unittest translation.test_ch03_annotation_manifest translation.test_publish_learning_annotations -v
```

Expected: PASS, 7 tests.

- [ ] **Step 5: Run publisher dry-run**

Run with a token that has Discussions read/write permissions:

```powershell
$env:GH_TOKEN="<token>"
python translation/_publish_learning_annotations.py docs/annotations/ch03-learning-annotations.json --dry-run
```

Expected: 40 lines with actions `create`, `comment`, `update`, or `skip`. No GitHub Discussions are changed in dry-run mode.

- [ ] **Step 6: Commit**

```powershell
git add translation/_publish_learning_annotations.py translation/test_publish_learning_annotations.py
git commit -m "Add Giscus learning annotation publisher"
```

## Task 4: Publish Annotations and Refresh the Comment Index

**Files:**
- Modify: GitHub Discussions in `yuancaoyaoHW/Convex-Optimization`
- Modify: `translation/annotated-pairs.json`

**Interfaces:**
- Consumes: publisher from Task 3, manifest from Task 2, existing `translation/_build_annotated_pairs.py`
- Produces: published Giscus discussions/comments and updated local annotation count index

- [ ] **Step 1: Confirm authentication**

Run:

```powershell
if ($env:GH_TOKEN) { "GH_TOKEN present" } elseif ($env:GITHUB_TOKEN) { "GITHUB_TOKEN present" } else { "missing token"; exit 1 }
```

Expected: `GH_TOKEN present` or `GITHUB_TOKEN present`.

- [ ] **Step 2: Re-run dry-run immediately before publication**

Run:

```powershell
python translation/_publish_learning_annotations.py docs/annotations/ch03-learning-annotations.json --dry-run
```

Expected: 40 planned actions and no validation errors.

- [ ] **Step 3: Publish**

Run:

```powershell
python translation/_publish_learning_annotations.py docs/annotations/ch03-learning-annotations.json
```

Expected: 40 action lines. The command exits 0.

- [ ] **Step 4: Refresh annotated pairs**

Run:

```powershell
python translation/_build_annotated_pairs.py
```

Expected: output like `annotated pairs: N (pages queried: M)`, where `N` is at least 40 and includes the selected Chapter 3 pairs.

- [ ] **Step 5: Verify selected pairs are present in the index**

Run:

```powershell
python -c "import json; d=json.load(open('translation/annotated-pairs.json',encoding='utf-8')); wanted={3,5,8,13,17,30,35,57,62,65,71,78,90,92,96,102,103,112,117,126,130,141,146,148,150,162,169,170,174,176,197,208,226,253,256,263,278,289,301,312}; got={p['pair'] for p in d['pairs'] if p['page']=='ch03-convex-functions.html'}; missing=sorted(wanted-got); print('missing', missing); raise SystemExit(1 if missing else 0)"
```

Expected: `missing []`.

- [ ] **Step 6: Commit refreshed index**

```powershell
git add translation/annotated-pairs.json
git commit -m "Update chapter 3 annotated pairs"
```

## Task 5: Live Rendering Verification Report

**Files:**
- Create: `docs/annotations/ch03-rendering-check.md`

**Interfaces:**
- Consumes: live page `https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html`
- Produces: written verification report with desktop and mobile checks

- [ ] **Step 1: Trigger or wait for Pages deployment**

If Task 4 changed `translation/annotated-pairs.json`, push the branch or trigger the existing Pages workflow before live verification:

```powershell
git status --short --branch
```

Expected: local branch contains the Task 4 commit. If the branch is not pushed, push it before checking the live site:

```powershell
git push origin main
```

- [ ] **Step 2: Verify live raw index contains selected pairs**

Run:

```powershell
$json = Invoke-RestMethod -Uri "https://yuancaoyaohw.github.io/Convex-Optimization/annotated-pairs.json"
$wanted = @(3,13,65,170,226,263,301,312)
$got = $json.pairs | Where-Object { $_.page -eq "ch03-convex-functions.html" } | Select-Object -ExpandProperty pair
$missing = $wanted | Where-Object { $got -notcontains $_ }
"missing sample pairs: $($missing -join ', ')"
if ($missing.Count -gt 0) { exit 1 }
```

Expected: `missing sample pairs:` with no numbers after the colon.

- [ ] **Step 3: Browser-check sample modals**

Open these URLs and click or auto-open the annotation modal:

```text
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-3
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-65
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-170
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-226
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-263
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-301
```

For each URL, verify:

```text
- Modal opens for the requested pair.
- Context line shows ch03-convex-functions.html / pair-N.
- Giscus loads a discussion for the same term.
- The Learning note comment is visible.
- Existing comments, if any, remain visible.
- No horizontal overflow is visible inside the modal.
```

- [ ] **Step 4: Mobile-width check**

In browser devtools, set viewport width to 390px and check:

```text
pair-3: convex definition
pair-65: matrix fractional function
pair-170: log-sum-exp conjugate
pair-301: matrix convexity
```

Expected:

```text
- Modal fits within viewport.
- Close button remains visible.
- Giscus iframe is scrollable.
- Long formulas wrap or remain readable without overlapping adjacent UI.
```

- [ ] **Step 5: Write report**

Create `docs/annotations/ch03-rendering-check.md`:

```markdown
# Chapter 3 Learning Annotation Rendering Check

Date: 2026-07-05
Page: https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html

## Index Check

- `annotated-pairs.json` includes sampled Chapter 3 pairs: yes
- Sampled pairs: 3, 65, 170, 226, 263, 301

## Desktop Checks

| Pair | Topic | Result | Notes |
| --- | --- | --- | --- |
| 3 | convex definition | pass | Modal opens and Giscus term matches. |
| 65 | matrix fractional function | pass | Matrix-heavy note is readable. |
| 170 | log-sum-exp conjugate | pass | Inline math renders cleanly. |
| 226 | quasiconvex first-order condition | pass | Context and note match. |
| 263 | log-concave density | pass | Discussion loads without mismatch. |
| 301 | matrix convexity | pass | No horizontal overflow observed. |

## Mobile Checks

Viewport width: 390px

| Pair | Result | Notes |
| --- | --- | --- |
| 3 | pass | Modal and close button remain usable. |
| 65 | pass | Formula text remains readable. |
| 170 | pass | Giscus iframe scrolls normally. |
| 301 | pass | No overlap in modal header or body. |

## Follow-up Fixes

No rendering fixes were required.
```

If a check fails, replace the relevant `pass` with `fail`, describe the exact issue, revise the manifest body, rerun Task 3 publication for the changed entry, and repeat the affected rendering check.

- [ ] **Step 6: Commit report**

```powershell
git add docs/annotations/ch03-rendering-check.md
git commit -m "Document chapter 3 annotation rendering checks"
```

## Task 6: Final Verification and Push

**Files:**
- No new files unless previous tasks found rendering fixes.

**Interfaces:**
- Consumes: all commits from Tasks 1-5
- Produces: pushed `main` with manifest, tooling, refreshed index, and rendering report

- [ ] **Step 1: Run all local tests**

Run:

```powershell
python -m unittest translation.test_ch03_annotation_manifest translation.test_publish_learning_annotations -v
python translation/_ch03_annotation_manifest.py docs/annotations/ch03-learning-annotations.json
```

Expected:

```text
Ran 7 tests
OK
valid manifest: 40 entries
```

- [ ] **Step 2: Confirm git history and worktree**

Run:

```powershell
git log --oneline -6
git status --short --branch
```

Expected: recent commits include manifest validation, manifest, publisher, index update, and rendering report. Worktree is clean.

- [ ] **Step 3: Push**

Run:

```powershell
git push origin main
```

Expected: `main -> main`.

- [ ] **Step 4: Final live spot check**

Open:

```text
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-3
https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html#pair-301
```

Expected: both modals show the correct Giscus discussion and visible `Learning note` content.
