#!/usr/bin/env python3
"""Validate skills, distributable documentation links, and manual evaluation cases."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import stat
import sys

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def validate_skill_name(name: str) -> str | None:
    """Return a human-readable error, or None for a portable skill name."""
    if not 1 <= len(name) <= 64:
        return "must contain between 1 and 64 characters"
    if NAME_PATTERN.fullmatch(name) is None:
        return (
            "must use lowercase ASCII letters, digits, and single hyphens; "
            "a hyphen cannot be first or last"
        )
    return None


def parse_skill_document(text: str) -> tuple[dict, str]:
    """Read delimited YAML frontmatter without interpreting the Markdown body."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with a YAML frontmatter delimiter (---)")
    end = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if end is None:
        raise ValueError("YAML frontmatter is missing its closing delimiter (---)")
    try:
        metadata = yaml.safe_load("".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("YAML frontmatter must be a mapping")
    return metadata, "".join(lines[end + 1 :])


def validate_skill(path: Path) -> list[str]:
    """Collect content errors for one skill; filesystem errors propagate."""
    errors: list[str] = []
    try:
        is_directory = stat.S_ISDIR(path.stat().st_mode)
    except FileNotFoundError:
        return ["skill directory does not exist"]
    if not is_directory:
        return ["skill path must be a directory"]
    skill_file = path / "SKILL.md"
    try:
        text = skill_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ["missing SKILL.md"]
    except UnicodeDecodeError:
        return ["SKILL.md must use UTF-8 encoding"]

    try:
        metadata, body = parse_skill_document(text)
    except ValueError as exc:
        return [str(exc)]

    name = metadata.get("name")
    if not isinstance(name, str):
        errors.append("name is required and must be a string")
    else:
        name_error = validate_skill_name(name)
        if name_error:
            errors.append(f"name {name_error}")
        if name != path.name:
            errors.append(f"name must match directory name {path.name!r}")

    description = metadata.get("description")
    if not isinstance(description, str):
        errors.append("description is required and must be a string")
    else:
        if not description.strip():
            errors.append("description must not be empty")
        if len(description) > 1024:
            errors.append("description must not exceed 1024 characters")
        if "<" in description or ">" in description:
            errors.append("description must not contain angle brackets")
        if description.lstrip().upper().startswith("TODO:"):
            errors.append("replace the TODO description before publishing this skill")

    if not body.strip():
        errors.append("Markdown body must not be empty")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path", type=Path, help="validate one skill directory only; skip repository checks"
    )
    args = parser.parse_args(argv)

    try:
        if args.path is not None:
            paths = [args.path.absolute()]
        else:
            skills_root = REPO_ROOT / "skills"
            paths = sorted(
                path
                for path in skills_root.iterdir()
                if not path.name.startswith(".") and stat.S_ISDIR(path.stat().st_mode)
            )
        failed = 0
        for path in paths:
            try:
                errors = validate_skill(path)
            except OSError as exc:
                errors = [f"cannot read skill: {exc}"]
            if errors:
                failed += 1
                print(f"FAIL {path}", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
            else:
                print(f"OK   {path}")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    repository_errors: list[str] = []
    if args.path is None:
        from repository_checks import check_repository

        try:
            repository_errors = check_repository(REPO_ROOT)
        except (OSError, ValueError) as exc:
            repository_errors = [str(exc)]
        if repository_errors:
            print("FAIL repository static checks", file=sys.stderr)
            for error in repository_errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print("OK   repository documentation links and evaluation definitions")

    if failed or repository_errors:
        print(
            f"Validation failed: {failed} of {len(paths)} skill(s); "
            f"{len(repository_errors)} repository error(s).",
            file=sys.stderr,
        )
        return 1
    print(f"Validated {len(paths)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
