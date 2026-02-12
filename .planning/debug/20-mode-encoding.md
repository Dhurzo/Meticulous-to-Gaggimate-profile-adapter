## Debug: Phase 20 batch mode execution failure

- **Date:** 2026-02-12T15:10:00Z
- **Scenario:** Running `PYTHONPATH=src python3 -m translate_profile.cli translate-batch tests/fixtures/batch_test_data/valid_profiles --mode linear` from repository root.
- **Observation:** Python prints the full interpreter configuration, then raises `Fatal Python error: init_fs_encoding` followed by `ModuleNotFoundError: No module named 'encodings'`. The process terminates before Typer can run.
- **Diagnosis:** Injecting `PYTHONPATH=src` into the environment hides the standard library directories that provide `encodings`. The interpreter cannot initialize its filesystem encoding codec without `encodings`, so it crashes immediately. Even explicitly activating `.venv/bin/activate` does not fix it because the `PYTHONPATH` override remains in effect.
- **Suggested fix:** Run the command with the full virtualenv, avoiding forced PYTHONPATH settings that bypass the stdlib. For example: `. .venv/bin/activate && python -m translate_profile.cli ...` or ensure `PYTHONPATH` includes the stdlib directories.
