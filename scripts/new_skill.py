#!/usr/bin/env python3
"""Create an unpublished skill draft with the repository's MIT license."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

from validate import parse_skill_document, validate_skill_name


REPO_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIRECTORIES = {"scripts", "references", "assets"}


def parse_resources(value: str) -> list[str]:
    resources = [part.strip() for part in value.split(",")]
    if any(resource not in RESOURCE_DIRECTORIES for resource in resources):
        raise argparse.ArgumentTypeError(
            "resources must be a comma-separated list of scripts,references,assets"
        )
    return list(dict.fromkeys(resources))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", metavar="skill-name", help="name of the new skill directory")
    parser.add_argument(
        "--resources",
        type=parse_resources,
        default=[],
        metavar="scripts,references,assets",
        help="optional resource directories to create",
    )
    args = parser.parse_args(argv)

    name_error = validate_skill_name(args.name)
    if name_error:
        parser.error(f"skill-name {name_error}")

    target = REPO_ROOT / "skills" / args.name
    try:
        template = REPO_ROOT / "templates" / "skill" / "SKILL.md.template"
        metadata, body = parse_skill_document(template.read_text(encoding="utf-8"))
        metadata["name"] = args.name
        frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
        document = f"---\n{frontmatter}---\n{body}"
        license_bytes = (REPO_ROOT / "LICENSE").read_bytes()

        target.mkdir(parents=True, exist_ok=False)
        (target / "SKILL.md").write_text(document, encoding="utf-8")
        (target / "LICENSE").write_bytes(license_bytes)
        for resource in args.resources:
            resource_path = target / resource
            resource_path.mkdir()
            (resource_path / ".gitkeep").touch()
    except FileExistsError:
        print(f"ERROR: destination already exists: {target}", file=sys.stderr)
        return 1
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created SKILL.md and LICENSE in {target}")
    print("Replace the TODO: description and adapt the workflow before validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
