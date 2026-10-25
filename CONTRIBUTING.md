# Contributing

Contributions that improve evidence quality, workflow correctness, learning design, validation coverage, documentation, or portability are welcome.

## Before opening a change

- Open an issue for a large behavioral change so the intended contract is clear before implementation.
- Keep a pull request focused on one problem.
- Preserve the separation between local release readiness and external publication authorization.
- Do not weaken semantic gates into file-existence checks.

## Development workflow

1. Fork the repository and create a focused branch.
2. Update the relevant skill instructions, scripts, templates, and tests together.
3. Run the test suite:

   ```bash
   python3 -B -m unittest discover -s scripts -p 'test_*.py'
   ```

4. If you changed a `SKILL.md`, validate that skill with the Codex skill validator available in your development environment.
5. Explain the user-facing impact and the checks you ran in the pull request.

## Editorial method validation

For an editorial-method change, inspect complete connected outputs in addition to program tests. Use the same reader request and raw material for the previous and revised method, keep both actual outputs, and compare them without revealing method labels or expected defects to the evaluator. Include material that is accurate and complete but poorly selected, plus a different purpose where detail must remain. Do not rerun until a preferred winner appears; report no clear improvement when that is the result.

Use a topic not present in the method's examples to check transfer. Keep real private manuscripts and runtime evidence outside the repository. Record what the comparison supports and what remains uncertain; mock runtime tests verify dispatch and gates, not writing quality or observed human learning. The shared method and its actual execution snapshot should agree without duplicating their prose in Python prompts.

For a structural-method change, exercise the actual ordered route with connected full-text samples, not just a polished standalone chapter. Include a legitimate different purpose, such as an operating or reference path, to detect an imposed universal sequence. Verify that overall findings cannot be replaced by page passes, that route changes invalidate the old decision, and that claims and quotations stay within the material the reader actually received. A design proposal remains provisional until its consequential transitions have been developed and read.

## Compatibility

- Keep the Python tools dependency-free unless a dependency has a clear, documented benefit.
- Prefer portable paths and UTF-8 text.
- Do not include machine-specific paths, credentials, private source material, generated `_kb-control/` state, or release packages in contributions.

By submitting a contribution, you agree that it may be distributed under this repository's MIT License.
