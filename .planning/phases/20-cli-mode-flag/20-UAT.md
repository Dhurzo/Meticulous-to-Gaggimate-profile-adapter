---
status: testing
phase: 20-cli-mode-flag
source: 20-01-SUMMARY.md, 20-02-SUMMARY.md
started: 2026-02-12T15:00:00Z
updated: 2026-02-12T15:25:00Z
---

## Current Test

number: 4
name: Batch default mode is smart
expected: |
  Run the batch command without `--mode`. The CLI should print "Translation mode: smart" and "Mode: smart" so users know the default.
awaiting: user response

## Tests

### 1. Single profile mode flag reports selection
expected: Run the translate command with `--mode preserve` and observe both "Translation mode: preserve" and a final "Mode: preserve" line in the CLI output.
result: pending

### 2. Single profile default mode is smart
expected: Run the translate command without `--mode`. The CLI should echo "Translation mode: smart" and "Mode: smart" in the summary, confirming the default is smart.
result: pending

### 3. Batch mode flag reports selection
expected: Run `.workspace-venv/bin/translate-profile translate-batch tests/fixtures/batch_test_data/valid_profiles --mode linear` (or equivalent) and confirm both the initial output and summary mention "Mode: linear" while the translation completes. (Profile1 triggers validation failure but the mode logging should still appear.)
result: pass
reported: "Produced both 'Translation mode: linear' and 'Mode: linear' lines; translation failed for profile1.json due to validation but the mode output was present."

### 4. Batch default mode is smart
expected: Run the batch command without `--mode`. The CLI should print "Translation mode: smart" and "Mode: smart" so users know the default.
result: pending

## Summary

total: 4
passed: 1
issues: 0
pending: 3
skipped: 0

## Gaps

[none]
