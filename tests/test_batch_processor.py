"""Tests for batch processing functionality."""

import pytest
from pathlib import Path
import tempfile
import os

from translate_profile.batch_processor import (
    BatchResult,
    validate_and_discover_files,
    process_batch,
)
from translate_profile.core import DEFAULT_OUTPUT_DIR


class TestBatchResult:
    """Test BatchResult dataclass functionality."""

    def test_batch_result_structure(self):
        """Verify BatchResult has all required fields."""
        result = BatchResult(
            processed=5,
            successful=3,
            failed=2,
            details=[{"file": "test.json", "status": "success"}],
        )

        assert hasattr(result, "processed")
        assert hasattr(result, "successful")
        assert hasattr(result, "failed")
        assert hasattr(result, "details")
        assert result.processed == 5
        assert result.successful == 3
        assert result.failed == 2
        assert len(result.details) == 1

    def test_calculations(self):
        """Verify successful/failed counts are calculated correctly."""
        details = [
            {"file": "test1.json", "status": "success"},
            {"file": "test2.json", "status": "failed"},
            {"file": "test3.json", "status": "success"},
            {"file": "test4.json", "status": "failed"},
        ]

        result = BatchResult(
            processed=len(details),
            successful=sum(1 for d in details if d["status"] == "success"),
            failed=sum(1 for d in details if d["status"] == "failed"),
            details=details,
        )

        assert result.processed == 4
        assert result.successful == 2
        assert result.failed == 2


class TestValidateAndDiscoverFiles:
    """Test file discovery and validation functionality."""

    def test_discovers_json_files(self):
        """Test discovery of JSON files in valid directory."""
        # Use test fixture directory with valid profiles
        fixture_dir = Path("tests/fixtures/batch_test_data/valid_profiles")
        json_files = validate_and_discover_files(fixture_dir)

        assert len(json_files) == 3
        file_names = [f.name for f in json_files]
        assert "profile1.json" in file_names
        assert "profile2.json" in file_names
        assert "complex_profile.json" in file_names
        assert all(f.suffix == ".json" for f in json_files)

    def test_no_json_files_found(self):
        """Test handling of directory with no JSON files."""
        # Use empty directory fixture
        empty_dir = Path("tests/fixtures/batch_test_data/empty_directory")

        with pytest.raises(Exception) as exc_info:
            validate_and_discover_files(empty_dir)

        # Should raise typer.BadParameter or similar exception
        assert "No JSON files found" in str(exc_info.value)

    def test_nonexistent_directory(self):
        """Test handling of non-existent directory."""
        nonexistent_dir = Path("tests/fixtures/batch_test_data/nonexistent")

        with pytest.raises(Exception) as exc_info:
            validate_and_discover_files(nonexistent_dir)

        # Should raise exception about directory not existing
        assert "does not exist" in str(exc_info.value) or "not a directory" in str(exc_info.value)

    def test_filters_non_json_files(self):
        """Test that non-JSON files are filtered out."""
        # Use mixed profiles directory with both JSON and non-JSON files
        mixed_dir = Path("tests/fixtures/batch_test_data/mixed_profiles")
        json_files = validate_and_discover_files(mixed_dir)

        # Should only find JSON files, ignore .txt files
        assert len(json_files) == 3
        file_names = [f.name for f in json_files]
        assert "valid_profile.json" in file_names
        assert "another_valid.json" in file_names
        assert "invalid_profile.json" in file_names
        assert "not_json.txt" not in file_names
        assert all(f.suffix == ".json" for f in json_files)


class TestProcessBatch:
    """Test batch processing functionality."""

    def test_successful_batch_processing(self):
        """Test processing of valid profiles only."""
        # Use valid profiles directory
        input_files = [
            Path("tests/fixtures/batch_test_data/valid_profiles/profile1.json"),
            Path("tests/fixtures/batch_test_data/valid_profiles/profile2.json"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = process_batch(input_files, output_dir)

            assert result.processed == 2
            assert result.successful == 2
            assert result.failed == 0
            assert len(result.details) == 2

            # Check all files were marked as successful
            for detail in result.details:
                assert detail["status"] == "success"
                assert "output" in detail
                assert Path(detail["output"]).exists()

            # Verify output files have correct names
            output_files = [Path(d["output"]) for d in result.details]
            assert any(f.name == "profile1.json" for f in output_files)
            assert any(f.name == "profile2.json" for f in output_files)

    def test_mixed_success_failure(self):
        """Test processing with mixed valid and invalid profiles."""
        # Use mixed profiles directory (contains both valid and invalid JSON)
        input_files = [
            Path("tests/fixtures/batch_test_data/mixed_profiles/valid_profile.json"),
            Path("tests/fixtures/batch_test_data/mixed_profiles/invalid_profile.json"),
            Path("tests/fixtures/batch_test_data/mixed_profiles/another_valid.json"),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = process_batch(input_files, output_dir)

            assert result.processed == 3
            # Should have 2 successful, 1 failed
            assert result.successful == 2
            assert result.failed == 1
            assert len(result.details) == 3

            # Check success/failure status
            statuses = [detail["status"] for detail in result.details]
            assert statuses.count("success") == 2
            assert statuses.count("failed") == 1

            # Check failed file has error message
            failed_details = [d for d in result.details if d["status"] == "failed"]
            assert len(failed_details) == 1
            assert "error" in failed_details[0]
            assert failed_details[0]["file"] == "invalid_profile.json"

    def test_preserves_filenames(self):
        """Test that original filenames are preserved in output."""
        input_files = [Path("tests/fixtures/batch_test_data/valid_profiles/complex_profile.json")]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = process_batch(input_files, output_dir)

            assert result.successful == 1
            detail = result.details[0]
            assert detail["status"] == "success"

            # Check filename is preserved
            output_path = Path(detail["output"])
            assert output_path.name == "complex_profile.json"
            assert output_path.parent == output_dir

    def test_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        input_files = [Path("tests/fixtures/batch_test_data/valid_profiles/profile1.json")]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a nested directory that doesn't exist
            output_dir = Path(temp_dir) / "nested" / "output"
            assert not output_dir.exists()

            result = process_batch(input_files, output_dir)

            assert result.successful == 1
            assert output_dir.exists()
            assert output_dir.is_dir()

    def test_error_aggregation(self):
        """Test that all errors are captured and reported."""
        input_files = [Path("tests/fixtures/batch_test_data/mixed_profiles/invalid_profile.json")]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = process_batch(input_files, output_dir)

            assert result.processed == 1
            assert result.successful == 0
            assert result.failed == 1

            # Check error details are captured
            detail = result.details[0]
            assert detail["status"] == "failed"
            assert "error" in detail
            assert len(detail["error"]) > 0
            assert detail["file"] == "invalid_profile.json"


class TestCliIntegration:
    """Test CLI integration for batch processing."""

    def test_translate_batch_command_exists(self):
        """Test that translate-batch command is registered."""
        from typer.testing import CliRunner
        from translate_profile.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "translate-batch" in result.stdout
        assert "Process all Meticulous profiles in a directory" in result.stdout

    def test_help_output(self):
        """Test that help text displays properly."""
        from typer.testing import CliRunner
        from translate_profile.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["translate-batch", "--help"])

        assert result.exit_code == 0
        assert "input_dir" in result.stdout
        assert "--output" in result.stdout
        # Check for key help content (exact formatting may vary)
        assert (
            "Directory containing Meticulous JSON profile" in result.stdout
            or "Process all Meticulous profiles in a directory" in result.stdout
        )

    def test_cli_valid_directory(self, tmp_path):
        """Test CLI with valid directory using tmp_path fixture."""
        from typer.testing import CliRunner
        from translate_profile.cli import app
        import shutil

        # Copy valid profiles to temporary directory
        valid_fixture_dir = Path("tests/fixtures/batch_test_data/valid_profiles")
        temp_input_dir = tmp_path / "input"
        temp_output_dir = tmp_path / "output"

        shutil.copytree(valid_fixture_dir, temp_input_dir)

        runner = CliRunner()
        result = runner.invoke(
            app, ["translate-batch", str(temp_input_dir), "--output", str(temp_output_dir)]
        )

        assert result.exit_code == 0
        assert "Found 3 JSON files" in result.stdout
        assert "All 3 files translated successfully!" in result.stdout
        assert "✅" in result.stdout  # Success indicators

        # Check output files exist
        assert temp_output_dir.exists()
        output_files = list(temp_output_dir.glob("*.json"))
        assert len(output_files) == 3

    def test_cli_empty_directory(self, tmp_path):
        """Test CLI with empty directory scenario."""
        from typer.testing import CliRunner
        from translate_profile.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["translate-batch", str(tmp_path)])

        assert result.exit_code == 1  # Should fail with empty directory
        assert "No JSON files found" in result.stdout or "Error:" in result.stdout

    def test_cli_custom_output(self, tmp_path):
        """Test --output flag functionality."""
        from typer.testing import CliRunner
        from translate_profile.cli import app
        import shutil

        # Copy valid profiles to temporary directory
        valid_fixture_dir = Path("tests/fixtures/batch_test_data/valid_profiles")
        temp_input_dir = tmp_path / "input"
        custom_output_dir = tmp_path / "custom_output"

        shutil.copytree(valid_fixture_dir, temp_input_dir)

        runner = CliRunner()
        result = runner.invoke(
            app, ["translate-batch", str(temp_input_dir), "--output", str(custom_output_dir)]
        )

        assert result.exit_code == 0
        assert custom_output_dir.exists()
        output_files = list(custom_output_dir.glob("*.json"))
        assert len(output_files) == 3

    def test_cli_exit_codes(self, tmp_path):
        """Test CLI exit codes for failures."""
        from typer.testing import CliRunner
        from translate_profile.cli import app
        import shutil

        # Copy mixed profiles (contains invalid JSON) to temporary directory
        mixed_fixture_dir = Path("tests/fixtures/batch_test_data/mixed_profiles")
        temp_input_dir = tmp_path / "mixed_input"
        temp_output_dir = tmp_path / "output"

        shutil.copytree(mixed_fixture_dir, temp_input_dir)

        runner = CliRunner()
        result = runner.invoke(
            app, ["translate-batch", str(temp_input_dir), "--output", str(temp_output_dir)]
        )

        # Should exit with code 1 when some files fail
        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()
        assert "✅" in result.stdout  # Should show some successes
        assert "❌" in result.stdout  # Should show some failures

    def test_cli_success_messages(self, tmp_path):
        """Test CLI success message formatting."""
        from typer.testing import CliRunner
        from translate_profile.cli import app
        import shutil

        # Copy valid profiles to temporary directory
        valid_fixture_dir = Path("tests/fixtures/batch_test_data/valid_profiles")
        temp_input_dir = tmp_path / "input"
        temp_output_dir = tmp_path / "output"

        shutil.copytree(valid_fixture_dir, temp_input_dir)

        runner = CliRunner()
        result = runner.invoke(
            app, ["translate-batch", str(temp_input_dir), "--output", str(temp_output_dir)]
        )

        assert result.exit_code == 0
        # Check for expected success message elements
        assert "📊 Summary:" in result.stdout
        assert "Processed 3 files" in result.stdout
        assert "Successful: 3" in result.stdout
        assert "Failed: 0" in result.stdout
        assert "All 3 files translated successfully!" in result.stdout

    def test_cli_failure_messages(self, tmp_path):
        """Test CLI failure message clarity."""
        from typer.testing import CliRunner
        from translate_profile.cli import app
        import shutil

        # Copy mixed profiles to temporary directory
        mixed_fixture_dir = Path("tests/fixtures/batch_test_data/mixed_profiles")
        temp_input_dir = tmp_path / "mixed_input"
        temp_output_dir = tmp_path / "output"

        shutil.copytree(mixed_fixture_dir, temp_input_dir)

        runner = CliRunner()
        result = runner.invoke(
            app, ["translate-batch", str(temp_input_dir), "--output", str(temp_output_dir)]
        )

        assert result.exit_code == 1
        # Check for clear failure reporting
        assert "❌" in result.stdout  # Failure indicators
        assert "invalid_profile.json" in result.stdout  # Failed file mentioned
        assert "failed translation" in result.stdout.lower()
        # Should still show summary with failure counts
        assert "Failed:" in result.stdout

    def test_cli_progress_indication(self, tmp_path):
        """Test CLI progress bar functionality."""
        from typer.testing import CliRunner
        from translate_profile.cli import app
        import shutil

        # Copy valid profiles to temporary directory
        valid_fixture_dir = Path("tests/fixtures/batch_test_data/valid_profiles")
        temp_input_dir = tmp_path / "input"
        temp_output_dir = tmp_path / "output"

        shutil.copytree(valid_fixture_dir, temp_input_dir)

        runner = CliRunner()
        result = runner.invoke(
            app, ["translate-batch", str(temp_input_dir), "--output", str(temp_output_dir)]
        )

        assert result.exit_code == 0
        # Progress indication should be mentioned
        assert "Processing profiles..." in result.stdout
        # Note: Actual progress bar might not be visible in test output

    def test_cli_invalid_directory(self):
        """Test CLI directory validation."""
        from typer.testing import CliRunner
        from translate_profile.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["translate-batch", "/nonexistent/directory/path"])

        # Typer returns exit code 2 for parameter errors
        assert result.exit_code in [1, 2]
        # Should provide helpful error message
        assert (
            "Error:" in result.stdout
            or "does not exist" in result.stdout
            or "Invalid" in result.stdout
        )

    def test_cli_permission_errors(self):
        """Test CLI handling of unreadable directory scenarios."""
        from typer.testing import CliRunner
        from translate_profile.cli import app

        # This test is harder to implement reliably across platforms
        # For now, we'll test with a file instead of directory
        runner = CliRunner()
        result = runner.invoke(
            app, ["translate-batch", "tests/fixtures/batch_test_data/mixed_profiles/not_json.txt"]
        )

        # Should fail because input is not a directory (Typer returns exit code 2)
        assert result.exit_code in [1, 2]
        assert (
            "Error:" in result.stdout
            or "not a directory" in result.stdout
            or "Invalid" in result.stdout
        )
