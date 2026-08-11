# Local Knowledge App UX

## Mode Mapping

- Reader-led learning: a calm reading start, progressive disclosure, focused reader, resume position, and optional practice.
- Guided learning: capability phases, prerequisites, checks, and explicitly defined progress.
- Practice-led learning: current task, feedback, artifacts, and evidence, only when the contract selects this posture.
- Operations: workflow stages, current tasks, deliverables, tools, quality gates, and exceptions.
- Reference: search, taxonomy, canonical entries, aliases, and freshness.
- Hybrid: a short start path separated from work and lookup routes.

Do not impose course completion on a work or reference product.

## Page Responsibilities

- Home: explain what this is and offer the contract's single default action before secondary routes.
- Directory: exhaustive but structured browsing; for novice reader-led products, keep the full catalog behind progressive disclosure.
- Reader: focused content, local context, outline, and related tools/pages.
- Tools/templates: usable artifact first, followed by use conditions and validation.
- Cases/practice: evidence-led cases or checkable practice.
- Internal control: never expose by default.

## Homepage

Answer what the knowledge base helps do, where to start, and what can be searched. Avoid simultaneously showing a full chapter list, module grid, quick links, search preview, popular articles, and duplicate route summaries.

A single default action controls emphasis, not actionability. If a phase, task, or route card is visibly presented as a way to enter content, make the card or its explicit action directly clickable and keyboard reachable. Record its destination and click depth; do not force the reader through a directory merely to preserve a visually dominant primary button.

Run a five-second orientation check: a representative reader should be able to state what the product is, what to do next, and whether any task or completion commitment is required. Do not expose system metadata, progress machinery, source policy, or taxonomy merely because the implementation uses it.

## Directory And Search

Preserve stage, module, or category context in default, filtered, and search views. Avoid a flat dump of dozens of files. In a reader-led novice product, default to one recommended next item and reveal the exhaustive directory only on request. Support aliases and useful empty states. A scope label and default filter must agree: a view titled “全库搜索” cannot silently start in “专题” only.

## Reader

Put the article before large support navigation on mobile. Keep primary navigation reachable on long pages, reset scroll after article changes, wrap wide content, and follow the contract's source-presentation policy. Remove duplicate summaries, taxonomy labels, and control metadata when they do not help comprehension. Parse Markdown tables as tables rather than line-by-line code; make only the table region horizontally scrollable. Render images with alternative text and resolve relative Markdown links from the current article path.

## Validation

Run repository-specific syntax and build commands. Check desktop and mobile widths, page overflow, console errors, search context, route resolution, reader scroll behavior, image loading, table semantics, relative links, and template/download/copy actions. Also verify the default visible choice count, catalog collapsed/expanded states, primary and direct-entry click depth, pointer and keyboard actionability, article-first reading, optional-practice behavior, and that progress cannot contradict the contract. When a release package exists, repeat these checks against that package. Static DOM or source inspection cannot be reported as a passed browser check.
