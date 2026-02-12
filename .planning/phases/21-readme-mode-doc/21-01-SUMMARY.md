# Summary: Phase 21-01 — Document mode selection

- Expanded the Usage section with explicit `--mode` examples for both `translate` and `translate-batch`, plus notes that each command prints `Translation mode: <mode>`/`Mode: <mode>` and defaults to smart when the flag is absent.
- Added a Transition Modes explanation after the interpolation tables so readers can see how smart/preserve/linear/instant map Meticulous interpolations to Gaggimate transitions and understand that the CLI flag (not any hidden logic change) drives the choice.
- Verified the documented commands locally via `.workspace-venv/bin/translate-profile ... --mode preserve` and `... --mode linear`, checking that the CLI echoes the expected mode announcements and still writes output or summaries as noted.

## Testing
- Manual verification of the new README examples by running the CLI commands described above (`translate` with `--mode preserve` and `translate-batch` with `--mode linear`), observing the announced mode lines and confirming the smart default by rerunning without `--mode`.
