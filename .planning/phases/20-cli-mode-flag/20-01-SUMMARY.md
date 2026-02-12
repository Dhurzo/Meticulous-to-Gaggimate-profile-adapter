# Summary: Phase 20-01 — Add translate mode flag and logging

- Added a validated `--mode`/`--transition-mode` option to the single-profile `translate` command.
- The option normalizes choices (`smart`, `preserve`, `linear`, `instant`), defaults to `smart`, and feeds the selection to `translate_profile` so the existing heuristics remain unchanged.
- The command now prints the selected mode before starting each translation so users can confirm what ran.
- No translator internals were touched; only CLI wiring and messaging were updated.

## Testing
- Manual CLI invocation was not run because the package has no `__main__` entry point; running `python3 -m translate_profile.cli` currently raises a warning and cannot be executed directly in this environment. Environment-specific CLI smoke tests were skipped.
