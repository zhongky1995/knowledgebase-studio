# Diagram Design And Review

Use for explanatory diagrams. Adapt to the host knowledge base's existing visual style; these are practical defaults for a neutral reading interface, not a mandatory brand. For data charts also use the evidence-to-judgment guidance. For animation apply these rules to keyframes and the static fallback.

## Choose A Graphic Structure

| Reader's question | Useful structure | What must be visible | Common failure |
| --- | --- | --- | --- |
| What changed? | Before/after | Same objects in stable positions; changed record highlighted and named | Different layouts make everything look changed |
| Who sends what to whom? | Request/reply lanes | Participants persist; each arrow names what travels and its direction | One bidirectional arrow hides order and reply failure |
| Where is it stored/shared? | Ownership/containment | A visible boundary encloses the actual shared object; devices remain distinct | Identical boxes imply copies or identity equality |
| What happens if a condition changes? | Branch/contrast | Explicit condition; labeled outcomes; same comparison basis | Unlabeled arrows imply an unexplained choice |
| How do parts form a whole? | Layer/overview | Containers show the selected kind of boundary and major dependencies | Mixing deployment, responsibility and data ownership without a legend |

Four editable SVG examples plus deliberate counterexamples are in `../../../assets/visual-patterns/index.html`. Rebuild them with `python3 <plugin-root>/scripts/kb_visual_examples.py --output <directory>`; `--force` replaces only its known generated files. These are illustrated teaching cases, not source evidence or a universal page template. Copy the suitable good SVG, replace its objects and statements, then review the actual result. Do not copy the deliberately bad examples into a learner-facing release.

## Hierarchy And Typography

- One conclusion or question is the visual headline. Put the explanation in the picture below it; surrounding prose carries exceptions that would overload labels.
- Use three levels: headline 22–28 px, object/action labels 16–18 px, supporting labels 14–16 px **at rendered size**. Important labels are not footnotes. Match the host font; use a CJK-capable sans-serif fallback and confirm font loading before measuring.
- The reference samples use a 360-unit canvas displayed at no more than 360 CSS px, 24/20/18-unit type. At a 320 px viewport with 16 px page gutters a 16-unit label would be 12.8 px, so give the diagram a wider slot, increase the type, or reflow. Do not declare it readable from source font-size alone. Default minimum rendered label size is 14 px; a different minimum needs a documented audience/destination reason and actual review.
- Aim for short noun labels and verb phrases. If a label needs more than two short lines, move the explanation adjacent to the figure or split the figure. This is a redesign trigger, not a hard character quota.
- Keep text as editable SVG text where practical. Add a title and a mechanism-bearing description. In an HTML `<img>`, supply meaningful alt text too; an internal SVG description does not replace it.

## Spacing And Composition

- Use a small spacing scale such as 8/16/24/32 px. Leave at least one line-height between text groups. Give the outer edge about 20–24 px at the reference size, and at least 12–16 px inside object containers.
- Align objects with the same role. Keep an object's position and appearance stable across before/after views. Emphasize the changed portion instead of changing every color.
- Prefer one dominant reading direction. On narrow screens, stack comparison panels in the same order and align the repeated objects. Avoid shrinking a wide desktop diagram into illegible text.
- Keep the main explanation readable without horizontal scrolling or zooming on a phone. A separately labeled detailed map may allow pan/zoom only when an understandable overview remains available.
- Object shapes should carry meaning: device frames for screens, rows for records, an enclosing outline for shared storage. Avoid ornamental icons and shadows that imply hierarchy without explanation.

## Color And Non-Color Meaning

Reference palette: dark text `#172B4D`, secondary text `#42526E`, neutral background `#F5F7FA`, request blue `#175CD3`, stored/result green `#067647`, change/attention amber `#92400E`, error red `#B42318`. Pale fills accompany dark labels, never replace them. Use the host palette when it provides the same distinctions.

- Assign colors to meanings, not to arbitrary boxes. Keep meanings stable across the corpus. Limit accents to the distinctions needed in this figure.
- Pair color with words, shapes, position or line style. “已保存” plus a record row is interpretable without green; red/green alone is insufficient.
- Measure foreground/background contrast with the actual colors. Use [W3C text contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) (4.5:1 for normal text) and [non-text contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) (3:1 for necessary graphical objects) as baseline targets; inspect grayscale as a separate meaning check. These are design targets, not a claim of full accessibility certification.
- Do not use a faint decorative border to carry an essential boundary. Avoid gradients/transparency behind small text unless the worst contrast is checked.

## Arrows, Lines And Boundaries

- An arrow means a directed action or transfer. Name what moves (“收藏请求”, “保存结果”) or the action. A line without an arrow means association/containment, with a label if ambiguous.
- Point the arrowhead at the receiving object's boundary, not into its label or an empty gap. Keep it visibly distinct from the stroke; use roughly 2 px strokes and 7–9 px arrowheads at the reference size.
- Route orthogonal lines around labels. Avoid crossings; if unavoidable, use a bridge or clearly separated lanes. A junction dot means connection; a plain crossing should not silently imply one.
- Show requests and replies with separate directions and labels. Keep the same endpoints even if a response is missing. Use dashed lines only with a declared meaning such as “未收到回复”; do not alternate solid/dashed for decoration.
- Enclosures distinguish ownership, location or permission. State which one the boundary represents. Do not use the same enclosure to imply all three at once.
- A sequence number establishes reading order, not duration. Label delays or time only when supported; a longer arrow does not imply a slower network.

## Fit, Review And Repair

1. State the learning job and choose a matching structure. Confirm each assertion and boundary against the source ledger.
2. Draw the actual objects/actions and check the mechanism with labels temporarily hidden. Restore necessary labels after the check. Meaningful flowcharts remain valid.
3. Render inside the intended article. Inspect at a narrow supported mobile width and a desktop width; include the narrowest supported width if it is below 360 px. Record both viewport width and actual diagram width.
4. Inspect text wrapping/clipping, label collisions, connected endpoints, consistent colors, spatial grouping, reading order, and the stated boundary. Check grayscale meaning. Browser geometry helps find clipping; it cannot certify conceptual clarity.
5. Save screenshots of the complete figure in each layout, then complete the schema 2 `designReview` contract. Record a short observation for each dimension rather than copying “pass”. Screenshot pixel width must agree with the recorded rendered width and capture scale.
6. If the image or fallback changes, capture and review again. Asset and screenshot hashes bind the receipt to those files; they do not prove the screenshot depicts that asset, so manually compare them. Keep receipts under `_kb-control/`, outside public release material.

Use schema 2 for new or redesigned visuals. Legacy schema 1 remains readable but does not establish this design review. `kb_visual_check.py` checks receipt completeness, file probes and hashes; it does not render a browser or judge aesthetics. App and QC must inspect the actual embedded result. No new paid image service is required for editable mechanism diagrams.
