"""Exercise local installs without writing to real client directories."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import install


class InstallTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.checkout = self.root / "checkout"
        self.destination = self.root / "client" / "skills"
        self.write(self.checkout / "skills/demo/SKILL.md", "Initial skill")
        self.write(self.checkout / "skills/demo/LICENSE", "License")
        self.write(self.checkout / "skills/demo/references/guide.md", "Reference")

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_installer(self, *arguments):
        output = StringIO()
        with (
            patch.object(install, "REPO_ROOT", self.checkout),
            redirect_stdout(output),
            redirect_stderr(output),
        ):
            result = install.main(list(arguments))
        return result, output.getvalue()

    def test_rerun_discovering_new_skills_keeps_identical_install(self):
        self.write(self.checkout / "skills/sample/SKILL.md.template", "Template")
        self.write(self.checkout / "evals/demo/SKILL.md", "Fixture")
        result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 0, output)
        self.assertIn("INSTALLED demo", output)
        self.assertEqual({path.name for path in self.destination.iterdir()}, {"demo"})
        self.assertEqual((self.destination / "demo/LICENSE").read_text(), "License")
        self.assertEqual((self.destination / "demo/references/guide.md").read_text(), "Reference")

        self.write(self.checkout / "skills/new-skill/SKILL.md", "New skill")
        result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 0, output)
        self.assertIn("SKIP demo", output)
        self.assertIn("INSTALLED new-skill", output)
        self.assertTrue((self.destination / "new-skill/SKILL.md").is_file())

    def test_updates_old_codex_install_in_place_with_backup(self):
        user_home = self.root / "user"
        legacy = self.root / "custom-codex-config" / "skills"
        self.write(legacy / "demo/SKILL.md", "Old skill")
        self.write(legacy / "demo/references/obsolete.md", "Local reference")
        self.write(self.checkout / "skills/another-skill/SKILL.md", "Another skill")

        with (
            patch.object(Path, "home", return_value=user_home),
            patch.object(install.os, "getenv", return_value=str(legacy.parent)),
        ):
            result, output = self.run_installer()

        self.assertEqual(result, 0, output)
        self.assertIn("UPDATED demo", output)
        self.assertEqual((legacy / "demo/SKILL.md").read_text(), "Initial skill")
        self.assertFalse((legacy / "demo/references/obsolete.md").exists())
        self.assertFalse((user_home / ".agents/skills/demo").exists())
        self.assertTrue((user_home / ".agents/skills/another-skill/SKILL.md").is_file())
        backup = Path(output.split("(backup: ", 1)[1].split(")\n", 1)[0])
        self.assertEqual((backup / "SKILL.md").read_text(), "Old skill")
        self.assertEqual((backup / "references/obsolete.md").read_text(), "Local reference")

    def test_selects_only_named_skill_in_claude_user_directory(self):
        user_home = self.root / "user"
        self.write(self.checkout / "skills/other/SKILL.md", "Unselected skill")
        with patch.object(Path, "home", return_value=user_home):
            result, output = self.run_installer("--client", "claude", "demo")
        self.assertEqual(result, 0, output)
        self.assertEqual(
            {path.name for path in (user_home / ".claude/skills").iterdir()}, {"demo"}
        )

    def test_unrelated_destination_is_preserved(self):
        unrelated = self.destination / "demo/notes.md"
        self.write(unrelated, "Keep these notes")
        result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 1, output)
        self.assertIn("destination exists without SKILL.md", output)
        self.assertEqual(unrelated.read_text(), "Keep these notes")

    def test_failed_update_restores_original_and_can_retry(self):
        target = self.destination / "demo"
        self.write(target / "SKILL.md", "Old skill")
        rename = Path.rename

        def fail_to_publish(path, destination):
            if path.parent.name.startswith("staging-"):
                raise PermissionError("simulated failure publishing the staged copy")
            return rename(path, destination)

        with patch.object(Path, "rename", fail_to_publish):
            result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 1, output)
        self.assertIn("simulated failure", output)
        self.assertEqual((target / "SKILL.md").read_text(), "Old skill")

        result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 0, output)
        self.assertIn("UPDATED demo", output)
        self.assertEqual((target / "SKILL.md").read_text(), "Initial skill")

    def test_retry_recovers_interrupted_legacy_update_in_place(self):
        user_home = self.root / "user"
        legacy = user_home / ".codex/skills/demo"
        self.write(legacy / "SKILL.md", "Original legacy skill")
        with install.locked_backup(legacy) as previous:
            legacy.rename(previous)

        with (
            patch.object(Path, "home", return_value=user_home),
            patch.object(install.os, "getenv", return_value=None),
        ):
            result, output = self.run_installer()

        self.assertEqual(result, 0, output)
        self.assertIn("UPDATED demo", output)
        self.assertTrue((legacy / "SKILL.md").is_file())
        self.assertFalse((user_home / ".agents/skills/demo").exists())
        backup = Path(output.split("(backup: ", 1)[1].split(")\n", 1)[0])
        self.assertEqual((backup / "SKILL.md").read_text(), "Original legacy skill")

    def test_reports_busy_destination_and_can_retry_after_lock_is_released(self):
        with install.locked_backup(self.destination / "demo"):
            result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 1, output)
        self.assertIn("could not lock", output)

        result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 0, output)
        self.assertIn("INSTALLED demo", output)

    def test_deep_destination_paths(self):
        with TemporaryDirectory(dir=install.filesystem_path(self.root)) as temporary:
            base = Path(install.display_path(Path(temporary)))
            destination = base / ("a" * 80) / ("b" * 100) / "skills"
            result, output = self.run_installer("--dest", str(destination))
            self.assertEqual(result, 0, output)
            reference = install.filesystem_path(destination / "demo/references/guide.md")
            self.assertEqual(reference.read_text(), "Reference")

    @unittest.skipIf(os.name == "nt", "POSIX executable mode")
    def test_executable_mode_changes_trigger_update(self):
        source = self.checkout / "skills/demo/scripts/example.sh"
        self.write(source, "#!/bin/sh\n")
        result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 0, output)

        source.chmod(0o755)
        result, output = self.run_installer("--dest", str(self.destination))
        self.assertEqual(result, 0, output)
        self.assertIn("UPDATED demo", output)
        target = self.destination / "demo/scripts/example.sh"
        self.assertTrue(target.stat().st_mode & 0o100)
