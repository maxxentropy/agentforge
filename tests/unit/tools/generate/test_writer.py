"""
Tests for Code Writer
=====================
"""

from datetime import datetime
from pathlib import Path

import pytest

from agentforge.core.generate.domain import FileAction, GeneratedFile, WriteError
from agentforge.core.generate.writer import CodeWriter, WriteOperation

# =============================================================================
# CodeWriter Basic Tests
# =============================================================================


class TestCodeWriterBasic:
    """Basic write operation tests."""

    @pytest.fixture
    def writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            backup_dir=Path(".backups"),
            add_header=False,
            atomic_writes=True,
        )

    def test_write_single_file(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("src/module.py"),
            content="x = 1\n",
        )
        paths = writer.write([file])

        assert len(paths) == 1, "Expected len(paths) to equal 1"
        assert paths[0] == tmp_path / "src/module.py", "Expected paths[0] to equal tmp_path / 'src/module.py'"
        assert (tmp_path / "src/module.py").read_text() == "x = 1\n", "Expected (tmp_path / 'src/module.py'... to equal 'x = 1\n'"

    def test_write_multiple_files(self, writer, tmp_path):
        files = [
            GeneratedFile(path=Path("src/a.py"), content="a = 1\n"),
            GeneratedFile(path=Path("src/b.py"), content="b = 2\n"),
        ]
        paths = writer.write(files)

        assert len(paths) == 2, "Expected len(paths) to equal 2"
        assert (tmp_path / "src/a.py").read_text() == "a = 1\n", "Expected (tmp_path / 'src/a.py').rea... to equal 'a = 1\n'"
        assert (tmp_path / "src/b.py").read_text() == "b = 2\n", "Expected (tmp_path / 'src/b.py').rea... to equal 'b = 2\n'"

    def test_creates_parent_directories(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("deep/nested/dir/file.py"),
            content="x = 1\n",
        )
        writer.write([file])

        assert (tmp_path / "deep/nested/dir/file.py").exists(), "Expected (tmp_path / 'deep/nested/di...() to be truthy"

    def test_tracks_operations(self, writer, tmp_path):
        files = [
            GeneratedFile(path=Path("a.py"), content="a\n"),
            GeneratedFile(path=Path("b.py"), content="b\n"),
        ]
        writer.write(files)

        assert writer.operation_count == 2, "Expected writer.operation_count to equal 2"
        assert writer.has_pending_operations, "Expected writer.has_pending_operations to be truthy"


class TestCodeWriterBackup:
    """Tests for backup functionality."""

    @pytest.fixture
    def writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            backup_dir=Path(".backups"),
            add_header=False,
        )

    def test_backup_existing_file(self, writer, tmp_path):
        # Create existing file
        existing = tmp_path / "existing.py"
        existing.write_text("original content\n")

        # Overwrite it
        file = GeneratedFile(
            path=Path("existing.py"),
            content="new content\n",
            action=FileAction.MODIFY,
        )
        writer.write([file])

        # Check backup was created
        backup_dir = tmp_path / ".backups"
        assert backup_dir.exists(), "Expected backup_dir.exists() to be truthy"
        backups = list(backup_dir.iterdir())
        assert len(backups) == 1, "Expected len(backups) to equal 1"
        assert backups[0].read_text() == "original content\n", "Expected backups[0].read_text() to equal 'original content\n'"

    def test_no_backup_for_new_file(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("new.py"),
            content="new\n",
            action=FileAction.CREATE,
        )
        writer.write([file])

        backup_dir = tmp_path / ".backups"
        # Backup dir might exist but should be empty or not exist
        if backup_dir.exists():
            assert len(list(backup_dir.iterdir())) == 0, "Expected len(list(backup_dir.iterdir... to equal 0"


class TestCodeWriterRollback:
    """Tests for rollback functionality."""

    @pytest.fixture
    def writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            backup_dir=Path(".backups"),
            add_header=False,
        )

    def test_rollback_removes_new_file(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("new.py"),
            content="new\n",
        )
        writer.write([file])
        assert (tmp_path / "new.py").exists(), "Expected (tmp_path / 'new.py').exists() to be truthy"

        writer.rollback()
        assert not (tmp_path / "new.py").exists(), "Assertion failed"

    def test_rollback_restores_modified_file(self, writer, tmp_path):
        # Create existing file
        existing = tmp_path / "existing.py"
        existing.write_text("original\n")

        # Modify it
        file = GeneratedFile(
            path=Path("existing.py"),
            content="modified\n",
            action=FileAction.MODIFY,
        )
        writer.write([file])
        assert existing.read_text() == "modified\n", "Expected existing.read_text() to equal 'modified\n'"

        # Rollback
        writer.rollback()
        assert existing.read_text() == "original\n", "Expected existing.read_text() to equal 'original\n'"

    def test_rollback_restores_deleted_file(self, writer, tmp_path):
        # Create file to delete
        to_delete = tmp_path / "delete_me.py"
        to_delete.write_text("delete me\n")

        # Delete it
        file = GeneratedFile(
            path=Path("delete_me.py"),
            content="",
            action=FileAction.DELETE,
        )
        writer.write([file])
        assert not to_delete.exists(), "Assertion failed"

        # Rollback
        writer.rollback()
        assert to_delete.exists(), "Expected to_delete.exists() to be truthy"
        assert to_delete.read_text() == "delete me\n", "Expected to_delete.read_text() to equal 'delete me\n'"

    def test_rollback_clears_operations(self, writer, tmp_path):
        file = GeneratedFile(path=Path("test.py"), content="x\n")
        writer.write([file])
        assert writer.operation_count == 1, "Expected writer.operation_count to equal 1"

        writer.rollback()
        assert writer.operation_count == 0, "Expected writer.operation_count to equal 0"

    def test_rollback_returns_count(self, writer, tmp_path):
        files = [
            GeneratedFile(path=Path("a.py"), content="a\n"),
            GeneratedFile(path=Path("b.py"), content="b\n"),
        ]
        writer.write(files)

        count = writer.rollback()
        assert count == 2, "Expected count to equal 2"


class TestCodeWriterHeader:
    """Tests for header comment functionality."""

    @pytest.fixture
    def writer(self, tmp_path):
        w = CodeWriter(
            project_root=tmp_path,
            add_header=True,
        )
        w.set_metadata(spec_name="TestSpec", phase="red")
        return w

    def test_adds_header_to_python_files(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("test.py"),
            content="x = 1\n",
        )
        writer.write([file])

        content = (tmp_path / "test.py").read_text()
        assert "Generated by AgentForge" in content, "Expected 'Generated by AgentForge' in content"
        assert "Spec: TestSpec" in content, "Expected 'Spec: TestSpec' in content"
        assert "Phase: red" in content, "Expected 'Phase: red' in content"
        assert "x = 1" in content, "Expected 'x = 1' in content"

    def test_preserves_shebang(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("script.py"),
            content="#!/usr/bin/env python3\nx = 1\n",
        )
        writer.write([file])

        content = (tmp_path / "script.py").read_text()
        assert content.startswith("#!/usr/bin/env python3"), "Expected content.startswith() to be truthy"
        assert "Generated by AgentForge" in content, "Expected 'Generated by AgentForge' in content"

    def test_preserves_encoding(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("encoded.py"),
            content="# -*- coding: utf-8 -*-\nx = 1\n",
        )
        writer.write([file])

        content = (tmp_path / "encoded.py").read_text()
        assert content.startswith("# -*- coding: utf-8 -*-"), "Expected content.startswith() to be truthy"
        assert "Generated by AgentForge" in content, "Expected 'Generated by AgentForge' in content"

    def test_no_header_for_non_python(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("data.json"),
            content='{"key": "value"}\n',
        )
        writer.write([file])

        content = (tmp_path / "data.json").read_text()
        assert "Generated by AgentForge" not in content, "Expected 'Generated by AgentForge' not in content"

    def test_header_disabled(self, tmp_path):
        writer = CodeWriter(
            project_root=tmp_path,
            add_header=False,
        )
        file = GeneratedFile(
            path=Path("test.py"),
            content="x = 1\n",
        )
        writer.write([file])

        content = (tmp_path / "test.py").read_text()
        assert "Generated by AgentForge" not in content, "Expected 'Generated by AgentForge' not in content"


class TestCodeWriterAtomicWrites:
    """Tests for atomic write functionality."""

    @pytest.fixture
    def atomic_writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            atomic_writes=True,
            add_header=False,
        )

    @pytest.fixture
    def non_atomic_writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            atomic_writes=False,
            add_header=False,
        )

    def test_atomic_write_creates_file(self, atomic_writer, tmp_path):
        file = GeneratedFile(
            path=Path("atomic.py"),
            content="atomic content\n",
        )
        atomic_writer.write([file])

        assert (tmp_path / "atomic.py").read_text() == "atomic content\n", "Expected (tmp_path / 'atomic.py').re... to equal 'atomic content\n'"

    def test_non_atomic_write_creates_file(self, non_atomic_writer, tmp_path):
        file = GeneratedFile(
            path=Path("non_atomic.py"),
            content="non atomic content\n",
        )
        non_atomic_writer.write([file])

        assert (tmp_path / "non_atomic.py").read_text() == "non atomic content\n", "Expected (tmp_path / 'non_atomic.py'... to equal 'non atomic content\n'"

    def test_atomic_write_no_temp_files_left(self, atomic_writer, tmp_path):
        file = GeneratedFile(
            path=Path("test.py"),
            content="x = 1\n",
        )
        atomic_writer.write([file])

        # No .tmp files should remain
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0, "Expected len(tmp_files) to equal 0"


class TestCodeWriterErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            add_header=False,
        )

    def test_rollback_on_error(self, writer, tmp_path):
        # Create first file
        good_file = GeneratedFile(
            path=Path("good.py"),
            content="good\n",
        )

        # Try to write to a directory (will fail)
        (tmp_path / "is_a_dir").mkdir()
        bad_file = GeneratedFile(
            path=Path("is_a_dir"),  # Can't write to directory
            content="bad\n",
        )

        with pytest.raises(WriteError):
            writer.write([good_file, bad_file])

        # Good file should be rolled back
        assert not (tmp_path / "good.py").exists(), "Assertion failed"

    def test_write_error_includes_path(self, writer, tmp_path):
        (tmp_path / "is_a_dir").mkdir()
        file = GeneratedFile(
            path=Path("is_a_dir"),
            content="content\n",
        )

        with pytest.raises(WriteError) as exc_info:
            writer.write([file])

        assert exc_info.value.path == Path("is_a_dir"), "Expected exc_info.value.path to equal Path('is_a_dir')"


class TestCodeWriterDeleteAction:
    """Tests for file deletion."""

    @pytest.fixture
    def writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            add_header=False,
        )

    def test_delete_existing_file(self, writer, tmp_path):
        # Create file
        target = tmp_path / "to_delete.py"
        target.write_text("delete me\n")

        file = GeneratedFile(
            path=Path("to_delete.py"),
            content="",
            action=FileAction.DELETE,
        )
        writer.write([file])

        assert not target.exists(), "Assertion failed"

    def test_delete_nonexistent_file_succeeds(self, writer, tmp_path):
        file = GeneratedFile(
            path=Path("does_not_exist.py"),
            content="",
            action=FileAction.DELETE,
        )
        # Should not raise
        writer.write([file])


class TestCodeWriterCleanup:
    """Tests for backup cleanup."""

    @pytest.fixture
    def writer(self, tmp_path):
        return CodeWriter(
            project_root=tmp_path,
            backup_dir=Path(".backups"),
            add_header=False,
        )

    def test_cleanup_removes_old_backups(self, writer, tmp_path):
        # Create backup directory with old file
        backup_dir = tmp_path / ".backups"
        backup_dir.mkdir()

        old_backup = backup_dir / "old_backup.py"
        old_backup.write_text("old\n")

        # Set modification time to 10 days ago
        import os
        old_time = datetime.utcnow().timestamp() - (10 * 24 * 60 * 60)
        os.utime(old_backup, (old_time, old_time))

        removed = writer.cleanup_backups(max_age_days=7)

        assert removed == 1, "Expected removed to equal 1"
        assert not old_backup.exists(), "Assertion failed"

    def test_cleanup_preserves_recent_backups(self, writer, tmp_path):
        # Create backup directory with recent file
        backup_dir = tmp_path / ".backups"
        backup_dir.mkdir()

        recent_backup = backup_dir / "recent_backup.py"
        recent_backup.write_text("recent\n")

        removed = writer.cleanup_backups(max_age_days=7)

        assert removed == 0, "Expected removed to equal 0"
        assert recent_backup.exists(), "Expected recent_backup.exists() to be truthy"

    def test_clear_history(self, writer, tmp_path):
        file = GeneratedFile(path=Path("test.py"), content="x\n")
        writer.write([file])
        assert writer.operation_count == 1, "Expected writer.operation_count to equal 1"

        writer.clear_history()
        assert writer.operation_count == 0, "Expected writer.operation_count to equal 0"


class TestWriteOperation:
    """Tests for WriteOperation dataclass."""

    def test_default_values(self):
        op = WriteOperation(
            path=Path("test.py"),
            action=FileAction.CREATE,
        )
        assert op.backup_path is None, "Expected op.backup_path is None"
        assert op.original_existed is False, "Expected op.original_existed is False"
        assert op.timestamp is not None, "Expected op.timestamp is not None"

    def test_with_backup(self):
        op = WriteOperation(
            path=Path("test.py"),
            action=FileAction.MODIFY,
            backup_path=Path(".backups/test.py"),
            original_existed=True,
        )
        assert op.backup_path == Path(".backups/test.py"), "Expected op.backup_path to equal Path('.backups/test.py')"
        assert op.original_existed is True, "Expected op.original_existed is True"
