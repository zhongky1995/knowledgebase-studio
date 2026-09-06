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

## Compatibility

- Keep the Python tools dependency-free unless a dependency has a clear, documented benefit.
- Prefer portable paths and UTF-8 text.
- Do not include machine-specific paths, credentials, private source material, generated `_kb-control/` state, or release packages in contributions.

By submitting a contribution, you agree that it may be distributed under this repository's MIT License.
