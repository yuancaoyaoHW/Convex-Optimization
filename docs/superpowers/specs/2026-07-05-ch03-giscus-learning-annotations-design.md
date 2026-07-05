# Chapter 3 Giscus Learning Annotations Design

## Goal

For `translation/ch03-convex-functions.html`, create a first-pass set of selected learning annotations in Giscus Discussions. The annotations should help readers understand definitions, examples, conditions, and geometric interpretations in Chapter 3 without changing the main bilingual chapter text.

The first pass should cover about 35-50 high-value `.pair` blocks, not every paragraph or every example. This keeps the authoring, review, and rendering checks manageable while establishing a repeatable workflow for later expansion.

## Current Context

Chapter 3 is a bilingual static HTML page with 321 `.pair` blocks. The existing annotation UI attaches one button to each `.pair` and loads Giscus with:

- page: `ch03-convex-functions.html`
- pair term format: `ch03-convex-functions.html#pair-N`
- Giscus mapping: `specific`
- strict matching: enabled
- config: `translation/giscus-config.json`

The page already has an index mechanism through `translation/annotated-pairs.json`; populated pairs display a comment count on their annotation buttons. The current Giscus behavior means each selected annotation must be attached to the correct `pair-N` discussion term, or it will not appear in the intended modal.

## Annotation Scope

Prioritize concepts that create leverage for the rest of convex optimization:

- convex function definition, strict convexity, concavity, affine equality case
- restriction to lines
- extended-value extension and indicator functions
- first-order and second-order convexity conditions
- common scalar and matrix examples
- sublevel sets and epigraphs
- Jensen's inequality and inequality derivations
- operations that preserve convexity: sums, affine composition, maxima, suprema, vector composition, minimization, perspective, linear-fractional perspective
- conjugate functions and common conjugates
- quasiconvexity and its relationship to convexity
- log-concavity and log-convexity
- monotonicity, generalized inequalities, K-convexity, and matrix convexity

Representative selected examples should include, at minimum:

- Example 3.1 indicator function
- Example 3.2 quadratic functions
- Example 3.4 matrix fractional function
- Example 3.5 piecewise-linear functions
- Example 3.6 sum of largest components
- Example 3.10 maximum eigenvalue
- Example 3.11 spectral norm
- Example 3.15 Schur complement
- Example 3.18 Euclidean norm squared perspective
- Example 3.19 negative logarithm and relative entropy
- Examples 3.21-3.27 conjugates
- Example 3.32 linear-fractional function
- Example 3.38 convex-over-concave quasiconvex function
- Example 3.40 log-concave density functions
- Example 3.48 matrix convexity

## Annotation Content Style

Each annotation should be short enough to read inside the modal. Target 120-220 Chinese characters for ordinary notes and up to 350 characters for difficult examples.

Use this structure when useful:

1. `Hook`: one sentence explaining why the paragraph matters.
2. `Intuition`: geometric, algebraic, or optimization intuition.
3. `Pitfall`: a common misconception or boundary condition.
4. `Connection`: where the idea reappears later in convex optimization.

Do not restate the original paragraph line by line. Prefer reader-facing explanation, small examples, and contrastive notes. Avoid long derivations unless the source paragraph is itself a proof bottleneck.

Math should use conservative Markdown:

- prefer inline `$...$` formulas for short expressions
- use displayed `$$...$$` only when readability clearly improves
- avoid complex aligned environments in Giscus comments unless rendering is verified
- avoid raw HTML except simple links if needed

## Authoring Workflow

Create a structured local annotation manifest before writing to GitHub Discussions. Suggested path:

`docs/annotations/ch03-learning-annotations.json`

Each entry should include:

- `page`: `ch03-convex-functions.html`
- `pair`: numeric `.pair` index
- `term`: `ch03-convex-functions.html#pair-N`
- `kind`: one of `definition`, `example`, `condition`, `geometry`, `operation`, `conjugate`, `quasiconvex`, `log-concave`, `generalized`
- `title`: short human-readable label
- `body`: final Markdown body to post
- `source_summary`: short extracted bilingual context for review only

The manifest is the reviewable source of truth. GitHub Discussions are the publication target.

## GitHub Discussions Write Strategy

Use a script to publish annotations so the work is repeatable:

1. Read the manifest.
2. For each entry, search GitHub Discussions in `yuancaoyaoHW/Convex-Optimization` for the exact term.
3. If a matching Discussion exists, add or update a maintainer-authored comment headed `Learning note`.
4. If no matching Discussion exists, create a Discussion whose title contains the exact term, then add the annotation body.
5. Preserve existing reader comments. Do not delete or overwrite unrelated discussion content.
6. After publication, refresh `translation/annotated-pairs.json` by running the existing annotation index builder or triggering the existing workflow.

This avoids manual browser posting and makes it possible to revise a note later without losing track of what was authored.

## Rendering Verification

Rendering is a required part of the workflow, not a final courtesy check.

Verify at least these cases:

- a newly created discussion appears in the correct modal for its `pair-N`
- an existing discussion with a new annotation keeps existing comments visible
- Markdown lists render cleanly inside the Giscus iframe
- inline and displayed math do not overflow the modal on desktop
- selected modals remain usable on mobile width
- the annotation button count updates after `annotated-pairs.json` is refreshed

Minimum sample set for visual checks:

- convex definition near the start of the chapter
- one figure-related or epigraph note
- one matrix-heavy example
- one conjugate example
- one quasiconvex/log-concave example
- one late-chapter generalized inequality or matrix convexity note

Use browser inspection or screenshots against the live GitHub Pages page after publication. If a note renders poorly, revise the manifest first, republish, then re-check.

## Failure Handling

If GitHub API authentication is unavailable, stop before publication and keep the manifest ready for review.

If a Discussion search returns multiple candidates, do not guess. Record the ambiguous term and inspect the matching Discussion titles.

If Giscus creates or finds a Discussion under the wrong term, correct the Discussion title or change the publication logic before continuing to the rest of the batch.

If Markdown math does not render inside Giscus, rewrite the note using simpler inline formulas or plain-language notation instead of changing the chapter page.

## Acceptance Criteria

- A reviewed manifest contains 35-50 selected Chapter 3 annotations.
- Every manifest entry has a valid `pair` index that exists in `translation/ch03-convex-functions.html`.
- Every published annotation is attached to a Discussion title containing its exact `term`.
- The live page opens Giscus for sampled annotated pairs without mismatching discussions.
- Rendering checks cover desktop and mobile widths.
- `translation/annotated-pairs.json` reflects the newly populated Chapter 3 pairs.

## Out of Scope

- Rewriting the Chapter 3 bilingual HTML text.
- Changing the Giscus modal UI unless rendering verification reveals a blocking layout issue.
- Covering all 321 `.pair` blocks.
- Producing complete lecture notes or exercise solutions for the whole chapter.
