# Chapter 3 Learning Annotation Rendering Check

Date: 2026-07-05
Page: https://yuancaoyaohw.github.io/Convex-Optimization/ch03-convex-functions.html

## Index Check

- `annotated-pairs.json` includes sampled Chapter 3 pairs: yes
- Sampled pairs: 3, 13, 65, 170, 226, 263, 301, 312
- Live Chapter 3 indexed pairs: 50

## Giscus Data Check

- Giscus strict matching required Discussion bodies to include the SHA-1 hash marker for each term.
- Publisher was updated to create exact term titles and sync missing strict hash markers.
- Final authenticated publisher dry-run result: all 40 manifest entries were `skip`.

| Pair | Discussion | Result |
| --- | --- | --- |
| 3 | https://github.com/yuancaoyaoHW/Convex-Optimization/discussions/21 | pass: Learning note returned by Giscus API |
| 65 | https://github.com/yuancaoyaoHW/Convex-Optimization/discussions/28 | pass: Learning note returned by Giscus API |
| 170 | https://github.com/yuancaoyaoHW/Convex-Optimization/discussions/43 | pass: Learning note returned by Giscus API |
| 226 | https://github.com/yuancaoyaoHW/Convex-Optimization/discussions/48 | pass: Learning note returned by Giscus API |
| 263 | https://github.com/yuancaoyaoHW/Convex-Optimization/discussions/51 | pass: Learning note returned by Giscus API |
| 301 | https://github.com/yuancaoyaoHW/Convex-Optimization/discussions/54 | pass: Learning note returned by Giscus API |

## Desktop Checks

Viewport: 1280 x 800

| Pair | Topic | Result | Notes |
| --- | --- | --- | --- |
| 3 | convex definition | pass | Modal opens, Giscus iframe loads, term matches. |
| 65 | matrix fractional function | pass | Modal opens, no horizontal overflow. |
| 170 | log-sum-exp conjugate | pass | Modal opens, close button visible. |
| 226 | quasiconvex first-order condition | pass | Context line matches pair-226. |
| 263 | log-concave density | pass | Giscus term matches pair-263. |
| 301 | matrix convexity | pass | Modal panel remains within viewport. |

## Mobile Checks

Viewport: 390 x 844

| Pair | Result | Notes |
| --- | --- | --- |
| 3 | pass | Modal and close button remain usable. |
| 65 | pass | Panel remains within viewport; no horizontal overflow. |
| 170 | pass | Giscus iframe loads and term matches. |
| 301 | pass | No overlap in modal header or body. |

## Follow-up Fixes

- Fixed publisher compatibility with Giscus `data-strict="1"` by adding exact term titles and SHA-1 hash markers to Discussion bodies.
- No CSS or modal layout fixes were required.
