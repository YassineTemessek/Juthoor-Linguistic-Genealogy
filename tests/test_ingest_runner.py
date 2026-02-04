"""
Tests for the LV0 ingest runner module.

These tests verify the pipeline orchestration logic.
"""

import pytest
from pathlib import Path


class TestIterRequested:
    """Test tag parsing utility."""

    def test_single_tag(self):
        from juthoor_datacore_lv0.ingest.runner import _iter_requested

        result = _iter_requested(["arabic"])
        assert result == {"arabic"}

    def test_multiple_tags(self):
        from juthoor_datacore_lv0.ingest.runner import _iter_requested

        result = _iter_requested(["arabic", "english"])
        assert result == {"arabic", "english"}

    def test_comma_separated(self):
        from juthoor_datacore_lv0.ingest.runner import _iter_requested

        result = _iter_requested(["arabic,english,quranic_arabic"])
        assert result == {"arabic", "english", "quranic_arabic"}

    def test_mixed_format(self):
        from juthoor_datacore_lv0.ingest.runner import _iter_requested

        result = _iter_requested(["arabic,english", "latin"])
        assert result == {"arabic", "english", "latin"}

    def test_empty(self):
        from juthoor_datacore_lv0.ingest.runner import _iter_requested

        result = _iter_requested([])
        assert result == set()

    def test_whitespace_handling(self):
        from juthoor_datacore_lv0.ingest.runner import _iter_requested

        result = _iter_requested(["  arabic  ,  english  "])
        assert result == {"arabic", "english"}


class TestExistsAny:
    """Test path existence checking."""

    def test_exists_any_none_exist(self, tmp_path):
        from juthoor_datacore_lv0.ingest.runner import _exists_any

        paths = [tmp_path / "nonexistent1.txt", tmp_path / "nonexistent2.txt"]
        assert _exists_any(paths) is False

    def test_exists_any_one_exists(self, tmp_path):
        from juthoor_datacore_lv0.ingest.runner import _exists_any

        existing = tmp_path / "existing.txt"
        existing.write_text("test")
        paths = [tmp_path / "nonexistent.txt", existing]
        assert _exists_any(paths) is True

    def test_exists_any_all_exist(self, tmp_path):
        from juthoor_datacore_lv0.ingest.runner import _exists_any

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("test1")
        file2.write_text("test2")
        assert _exists_any([file1, file2]) is True

    def test_exists_any_empty(self):
        from juthoor_datacore_lv0.ingest.runner import _exists_any

        assert _exists_any([]) is False


class TestFileStats:
    """Test file statistics gathering."""

    def test_file_stats_existing(self, tmp_path):
        from juthoor_datacore_lv0.ingest.runner import _file_stats

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        stats = _file_stats(test_file)
        assert stats["exists"] is True
        assert stats["bytes"] == 11
        assert str(test_file) in stats["path"]

    def test_file_stats_nonexistent(self, tmp_path):
        from juthoor_datacore_lv0.ingest.runner import _file_stats

        nonexistent = tmp_path / "nonexistent.txt"
        stats = _file_stats(nonexistent)
        assert stats["exists"] is False
        assert str(nonexistent) in stats["path"]


class TestStep:
    """Test the Step dataclass."""

    def test_step_creation(self):
        from juthoor_datacore_lv0.ingest.runner import Step

        step = Step(
            name="test:step",
            tags=frozenset({"test", "example"}),
            cmd=["python", "script.py"],
            required_all_inputs=(Path("/input1"), Path("/input2")),
            outputs=(Path("/output"),),
        )

        assert step.name == "test:step"
        assert "test" in step.tags
        assert "example" in step.tags
        assert len(step.cmd) == 2
        assert len(step.required_all_inputs) == 2
        assert len(step.outputs) == 1

    def test_step_frozen(self):
        from juthoor_datacore_lv0.ingest.runner import Step

        step = Step(
            name="test",
            tags=frozenset({"test"}),
            cmd=["echo"],
        )

        # Should be immutable
        with pytest.raises(AttributeError):
            step.name = "modified"


class TestBuildSteps:
    """Test step generation."""

    def test_build_steps_returns_list(self, tmp_path):
        from juthoor_datacore_lv0.ingest.runner import build_steps

        steps = build_steps(
            python_exe="python",
            repo_root=tmp_path,
            resources_dir=None,
        )

        assert isinstance(steps, list)
        assert len(steps) > 0

    def test_build_steps_has_expected_tags(self, tmp_path):
        from juthoor_datacore_lv0.ingest.runner import build_steps

        steps = build_steps(
            python_exe="python",
            repo_root=tmp_path,
            resources_dir=None,
        )

        all_tags = set()
        for step in steps:
            all_tags.update(step.tags)

        assert "arabic" in all_tags
        assert "quranic_arabic" in all_tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
