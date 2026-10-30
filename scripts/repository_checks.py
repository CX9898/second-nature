"""Check publication boundaries and the repository's manual evaluation definitions."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import yaml


def _git(root: Path, *arguments: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in (0, 1) or (
        result.returncode == 1 and arguments[0] != "check-ignore"
    ):
        raise ValueError(result.stderr.decode(errors="replace").strip() or "Git failed")
    return result.stdout


@dataclass(frozen=True)
class RepositoryFiles:
    root: Path
    publishable: frozenset[Path]

    @classmethod
    def discover(cls, root: Path) -> RepositoryFiles:
        root = root.resolve()
        output = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        names = set(output.split(b"\0")) - {b""}
        ignored = set()
        if names:
            ignored = set(
                _git(
                    root,
                    "check-ignore",
                    "--no-index",
                    "--stdin",
                    "-z",
                    input_bytes=b"\0".join(sorted(names)) + b"\0",
                ).split(b"\0")
            )
        paths = frozenset(
            Path(os.fsdecode(name))
            for name in names - ignored
            if (root / os.fsdecode(name)).is_file()
        )
        return cls(root, paths)

    def target_error(self, path: Path, *, kind: str | None = None) -> str | None:
        """Require the actual target and its distribution path to stay in the repo."""
        path = Path(os.path.normpath(path))
        try:
            relative = path.relative_to(self.root)
            resolved_relative = path.resolve().relative_to(self.root)
        except (ValueError, OSError, RuntimeError):
            return "target is outside the repository"
        if not path.exists():
            return "target does not exist"
        if kind == "directory" and not path.is_dir():
            return "target must be a directory"
        if kind == "file" and not path.is_file():
            return "target must be a file"
        if path.is_dir():
            if not any(relative in item.parents for item in self.publishable):
                return "target directory has no distributable files (it may be ignored)"
        elif relative not in self.publishable:
            return "target is not distributable (it may be ignored)"
        if path.is_file() and resolved_relative not in self.publishable:
            return "resolved target is not distributable (it may be ignored)"
        return None


def _is_public_document(path: Path) -> bool:
    if path in (Path("README.md"), Path("AGENTS.md")):
        return True
    if path.suffix.lower() != ".md":
        return False
    if path.parts[0] in ("docs", "skills"):
        return True
    return path.parts[0] == "evals" and path.name == "README.md" and len(path.parts) in (2, 3)


def _markdown_body(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        end = next(
            (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
            None,
        )
        if end is not None:
            return "\n" * (end + 1) + "".join(lines[end + 1 :])
    return text


def _links(tokens, line: int = 1):
    for token in tokens:
        token_line = token.map[0] + 1 if token.map else line
        if token.type in ("link_open", "image"):
            target = token.attrGet("href" if token.type == "link_open" else "src")
            if target is not None:
                yield token_line, target
        if token.children:
            yield from _links(token.children, token_line)


def check_document_links(files: RepositoryFiles) -> list[str]:
    errors: list[str] = []
    parser = MarkdownIt("commonmark")
    default_validate_link = parser.validateLink
    # Parse file URIs for rejection; Markdown normally treats them as plain text.
    parser.validateLink = lambda target: target.lower().startswith("file:") or default_validate_link(target)
    for document in sorted(filter(_is_public_document, files.publishable)):
        source = files.root / document
        source_error = files.target_error(source, kind="file")
        if source_error:
            errors.append(f"{document}: {source_error}")
            continue
        try:
            tokens = parser.parse(_markdown_body(source.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{document}: cannot read Markdown: {exc}")
            continue
        for line, target in _links(tokens):
            try:
                url = urlsplit(target)
                if url.scheme == "file":
                    error = "file URI targets are not distributable; use repository-relative paths"
                elif url.scheme or url.netloc or not url.path:
                    continue
                else:
                    path = source.parent / unquote(url.path)
                    error = files.target_error(path)
            except ValueError as exc:
                error = f"invalid target: {exc}"
            if error:
                errors.append(f"{document}:{line}: {target!r}: {error}")
    return errors


def _evaluation_path_error(files: RepositoryFiles, value, *, kind: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return "must be a nonempty repository-relative path"
    path = Path(value)
    if path.is_absolute():
        return "must be a repository-relative path"
    try:
        return files.target_error(files.root / path, kind=kind)
    except (ValueError, OSError) as exc:
        return f"invalid path: {exc}"


def check_evaluations(files: RepositoryFiles) -> list[str]:
    errors: list[str] = []
    definitions = sorted(
        path
        for path in files.publishable
        if len(path.parts) == 3 and path.parts[0] == "evals" and path.name == "cases.yaml"
    )
    for definition in definitions:
        prefix = str(definition)
        try:
            data = yaml.safe_load((files.root / definition).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            errors.append(f"{prefix}: cannot read evaluation YAML: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{prefix}: evaluation must be a mapping")
            continue
        skill = definition.parent.name
        if data.get("skill") != skill:
            errors.append(f"{prefix}: skill must match the evaluation directory {skill!r}")
        skill_error = files.target_error(files.root / "skills" / skill / "SKILL.md", kind="file")
        if skill_error:
            errors.append(f"{prefix}: corresponding skills/{skill}/SKILL.md: {skill_error}")
        if "fixture" in data:
            error = _evaluation_path_error(files, data["fixture"], kind="directory")
            if error:
                errors.append(f"{prefix}: fixture: {error}")
        cases = data.get("cases")
        if not isinstance(cases, list) or not cases:
            errors.append(f"{prefix}: cases must be a nonempty list")
            continue
        seen_ids: set[str] = set()
        for index, case in enumerate(cases, start=1):
            case_prefix = f"{prefix}: case {index}"
            if not isinstance(case, dict):
                errors.append(f"{case_prefix}: must be a mapping")
                continue
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id.strip():
                errors.append(f"{case_prefix}: id must be a nonempty string")
            elif case_id in seen_ids:
                errors.append(f"{case_prefix}: duplicate id {case_id!r}")
            else:
                seen_ids.add(case_id)
            if not isinstance(case.get("request"), str) or not case["request"].strip():
                errors.append(f"{case_prefix}: request must be a nonempty string")
            if not isinstance(case.get("expected_trigger"), bool):
                errors.append(f"{case_prefix}: expected_trigger must be a boolean")
            if "input_files" in case:
                inputs = case["input_files"]
                if not isinstance(inputs, list):
                    errors.append(f"{case_prefix}: input_files must be a list")
                    continue
                for value in inputs:
                    error = _evaluation_path_error(files, value, kind="file")
                    if error:
                        errors.append(f"{case_prefix}: input_files {value!r}: {error}")
    return errors


def check_repository(root: Path) -> list[str]:
    files = RepositoryFiles.discover(root)
    return check_document_links(files) + check_evaluations(files)
