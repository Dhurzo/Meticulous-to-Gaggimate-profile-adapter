import subprocess
import sys
from pathlib import Path


CLI = Path(".workspace-venv/bin/translate-profile")
SINGLE = [CLI, "translate", "tests/fixtures/batch_test_data/valid_profiles/profile2.json", "-o", "/tmp/cli-mode-test.json"]
BATCH = [CLI, "translate-batch", "tests/fixtures/batch_test_data/valid_profiles"]


def run_cli(cmd, mode=None):
    args = cmd.copy()
    if mode:
        args.append("--mode")
        args.append(mode)
    result = subprocess.run(args, capture_output=True, text=True)
    output = result.stdout + result.stderr
    return result.returncode, output


def assert_mode_lines(output, mode, expect_summary=True):
    assert f"Translation mode: {mode}" in output, "missing initial mode line"
    if expect_summary:
        assert f"Mode: {mode}" in output, "missing summary mode line"


def test_translate_modes():
    # default smart
    code, out = run_cli(SINGLE)
    assert_mode_lines(out, "smart", expect_summary=False)
    assert code in (0, 1)

    for mode in ("preserve", "linear", "instant"):
        code, out = run_cli(SINGLE, mode)
        assert_mode_lines(out, mode, expect_summary=False)
        assert code in (0, 1)


def test_translate_batch_mode():
    code, out = run_cli(BATCH, "linear")
    assert_mode_lines(out, "linear")
    assert code in (0, 1)

    code, out = run_cli(BATCH)
    assert_mode_lines(out, "smart")
    assert code in (0, 1)
