"""Exercise repository contracts in isolated, uncommitted Git worktrees."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import new_skill
from repository_checks import check_repository
import validate


class RepositoryToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        self.write(".gitignore", "/.local/\n__pycache__/\n")
        self.write(
            "skills/demo/SKILL.md",
            "---\nname: demo\ndescription: Use for demonstration tasks.\n---\n\n# Demo\n",
        )

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_evaluation(self, **changes):
        definition = {
            "skill": "demo",
            "fixture": "evals/demo/fixtures/project",
            "cases": [
                {
                    "id": "representative-request",
                    "request": "Review these documents.",
                    "expected_trigger": True,
                    "input_files": ["evals/demo/inputs/example.md"],
                }
            ],
        }
        definition.update(changes)
        self.write("evals/demo/cases.yaml", yaml.safe_dump(definition))

    def test_uncommitted_repository_and_markdown_reference_links(self):
        self.write(
            "README.md",
            "[Guide][guide]\n\n![Diagram][image]\n\n"
            "[Skills](skills/) and [section](#heading)\n\n"
            "[External](https://example.com/missing)\n\n"
            "`[Code](missing.md)`\n\n```md\n[Example](missing.md)\n```\n\n"
            "[guide]: docs/guide.md\n[image]: assets/example.svg\n",
        )
        self.write("docs/guide.md", "# Guide\n")
        self.write("assets/example.svg", "<svg/>\n")
        self.assertEqual(check_repository(self.root), [])

    def test_local_existing_file_cannot_be_linked_from_public_documents(self):
        self.write(".local/research/notes.md", "# Private notes\n")
        self.write("README.md", "[Research](.local/research/notes.md)\n")
        errors = check_repository(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("not distributable", errors[0])

    def test_common_output_roots_are_ignored_without_hiding_fixture_resources(self):
        rules = Path(__file__).resolve().parents[1] / ".gitignore"
        self.write(".gitignore", rules.read_text(encoding="utf-8"))
        local_paths = [
            ".local/research/note.md", "tmp/probe.md", "temp/probe.md",
            ".tmp/probe.md", "research/note.md", "docs/research/note.md",
            "outputs/report.json", "reports/report.json", "logs/check.log",
            "evals/runs/run/report.json", "evals/results/report.json",
            "demo-workspace/iteration-1/output.md",
        ]
        public_paths = [
            "docs/design.md", "evals/demo/cases.yaml",
            "skills/demo/references/research/note.md",
            "evals/demo/fixtures/project/tmp/input.json",
            "evals/demo/inputs/reports/example.md",
        ]
        for path in local_paths + public_paths:
            with self.subTest(path=path):
                result = subprocess.run(
                    ["git", "check-ignore", "-q", "--", path], cwd=self.root
                )
                self.assertEqual(result.returncode, 0 if path in local_paths else 1)

    def test_default_research_notes_are_not_public_document_dependencies(self):
        rules = Path(__file__).resolve().parents[1] / ".gitignore"
        self.write(".gitignore", rules.read_text(encoding="utf-8"))
        self.write("docs/research/notes.md", "# Local research\n")
        self.write("README.md", "[Research](docs/research/notes.md)\n")
        errors = check_repository(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("not distributable", errors[0])

    def test_missing_reference_image_and_outside_paths_fail(self):
        self.write(
            "README.md",
            "[Guide][missing]\n\n![Image](assets/missing.png)\n\n"
            "[Outside](../outside.md)\n\n[missing]: docs/missing.md\n",
        )
        errors = check_repository(self.root)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("docs/missing.md" in error for error in errors))
        self.assertTrue(any("assets/missing.png" in error for error in errors))
        self.assertTrue(any("outside the repository" in error for error in errors))

    def test_ignored_directory_is_not_a_distributable_link_target(self):
        self.write(".local/tmp/run.txt", "temporary\n")
        self.write("README.md", "[Runs](.local/)\n")
        errors = check_repository(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("no distributable files", errors[0])

    def test_file_uri_links_and_images_are_rejected(self):
        self.write(
            "README.md",
            "[Local notes](file:///home/example/notes.md)\n\n"
            "![Local image](file://localhost/.local/image.png)\n",
        )
        errors = check_repository(self.root)
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("file URI targets are not distributable" in error for error in errors))

    def test_ignored_target_fails_even_when_it_was_previously_added_to_git(self):
        self.write("notes.md", "# Local notes\n")
        subprocess.run(["git", "add", "notes.md"], cwd=self.root, check=True)
        self.write(".gitignore", "/notes.md\n")
        self.write("README.md", "[Notes](notes.md)\n")
        errors = check_repository(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("not distributable", errors[0])

    def test_fixture_and_input_documents_can_contain_intentional_bad_links(self):
        self.write("README.md", "[Evaluation](evals/demo/)\n")
        self.write("evals/demo/README.md", "[Cases](cases.yaml)\n")
        self.write("evals/demo/fixtures/project/README.md", "[Broken](missing.md)\n")
        self.write("evals/demo/inputs/example.md", "![Broken](missing.png)\n")
        self.write_evaluation()
        self.assertEqual(check_repository(self.root), [])

    def test_case_ids_trigger_types_and_input_paths_are_checked(self):
        self.write("evals/demo/fixtures/project/README.md", "# Fixture\n")
        self.write(".local/input.md", "local only\n")
        self.write_evaluation(
            cases=[
                {"id": "same", "request": "First", "expected_trigger": True},
                {
                    "id": "same",
                    "request": "Second",
                    "expected_trigger": "true",
                    "input_files": [".local/input.md", "evals/demo/inputs/missing.md"],
                },
            ]
        )
        errors = check_repository(self.root)
        self.assertEqual(len(errors), 4)
        self.assertTrue(any("duplicate id" in error for error in errors))
        self.assertTrue(any("must be a boolean" in error for error in errors))
        self.assertTrue(any("not distributable" in error for error in errors))
        self.assertTrue(any("does not exist" in error for error in errors))

    def test_evaluation_requires_matching_skill_and_repository_fixture(self):
        self.write_evaluation(skill="another", fixture="../outside")
        errors = check_repository(self.root)
        self.assertTrue(any("skill must match" in error for error in errors))
        self.assertTrue(any("fixture: target is outside" in error for error in errors))

    def test_path_option_stays_independent_of_repository_checks(self):
        self.write("README.md", "[Broken](missing.md)\n")
        with (
            patch.object(validate, "REPO_ROOT", self.root),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(validate.main(["--path", str(self.root / "skills/demo")]), 0)
            self.assertEqual(validate.main([]), 1)

    def test_new_skill_carries_license_and_never_overwrites_existing_draft(self):
        license_text = "MIT License\n\nCopyright (c) Example\n"
        self.write("LICENSE", license_text)
        self.write(
            "templates/skill/SKILL.md.template",
            "---\nname: placeholder\ndescription: 'TODO: describe the trigger.'\n---\n\n# Draft\n",
        )
        with (
            patch.object(new_skill, "REPO_ROOT", self.root),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(new_skill.main(["new-skill", "--resources", "references"]), 0)
            draft = self.root / "skills/new-skill"
            self.assertEqual((draft / "LICENSE").read_text(encoding="utf-8"), license_text)
            self.assertTrue((draft / "references").is_dir())
            (draft / "SKILL.md").write_text("custom draft\n", encoding="utf-8")
            self.assertEqual(new_skill.main(["new-skill"]), 1)
            self.assertEqual((draft / "SKILL.md").read_text(encoding="utf-8"), "custom draft\n")


if __name__ == "__main__":
    unittest.main()
