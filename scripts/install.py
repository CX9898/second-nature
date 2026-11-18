#!/usr/bin/env python3
"""Install skills from this checkout into a local client."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import filecmp
import os
from pathlib import Path
import shutil
import sys
from tempfile import mkdtemp, TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parent.parent


def filesystem_path(path: Path) -> Path:
    # Windows may limit unprefixed paths, including files inside a staging directory.
    name = str(path)
    if os.name != "nt" or name.startswith("\\\\?\\"):
        return path
    if name.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + name[2:])
    return Path("\\\\?\\" + name)


def display_path(path: Path) -> str:
    name = str(path)
    if name.startswith("\\\\?\\UNC\\"):
        return "\\\\" + name[8:]
    return name.removeprefix("\\\\?\\")


def same_package(source: Path, target: Path) -> bool:
    source_entries = {path.relative_to(source) for path in source.rglob("*")}
    target_entries = {path.relative_to(target) for path in target.rglob("*")}
    if source_entries != target_entries:
        return False

    for relative in source_entries:
        original, installed = source / relative, target / relative
        if original.is_symlink() or installed.is_symlink():
            if not (original.is_symlink() and installed.is_symlink()):
                return False
            if original.readlink() != installed.readlink():
                return False
        elif original.is_dir():
            if not installed.is_dir():
                return False
        elif not filecmp.cmp(original, installed, shallow=False):
            return False
        elif os.name != "nt" and (original.stat().st_mode ^ installed.stat().st_mode) & 0o111:
            return False
    return True


@contextmanager
def locked_backup(target: Path):
    # Keep staged and backed-up SKILL.md files outside the client's discovery root.
    work_root = filesystem_path(target.parent.with_name(f".{target.parent.name}-second-nature"))
    work_root.mkdir(parents=True, exist_ok=True)
    # Keep the lock file. The OS releases the lock when the handle closes or the process exits.
    with (work_root / f"{target.name}.lock").open("a+b") as lock:
        try:
            if os.name == "nt":
                import msvcrt

                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise OSError(f"could not lock {display_path(target)} for installation: {exc}") from exc
        yield work_root / f"{target.name}.previous"


def archive_backup(previous: Path, name: str) -> Path:
    backup_root = Path(mkdtemp(prefix=f"{name}-", dir=previous.parent))
    return previous.rename(backup_root / name)


def install_skill(source: Path, target: Path, previous: Path) -> str:
    source = filesystem_path(source)
    target = filesystem_path(target)
    location = display_path(target)
    existing = os.path.lexists(target)
    if os.path.lexists(previous):
        if existing:
            backup = archive_backup(previous, target.name)
            print(f"BACKUP {source.name}: {display_path(backup)}")
        else:
            previous.rename(target)
            existing = True

    if existing:
        if not (target / "SKILL.md").is_file():
            raise FileExistsError(f"destination exists without SKILL.md: {location}")
        if same_package(source, target):
            return f"SKIP {source.name}: up to date at {location}"
        if target.is_symlink() or target.resolve() != target:
            raise OSError(f"installed skill points to another location: {location}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="staging-", dir=previous.parent) as temporary:
        staged = Path(temporary) / source.name
        shutil.copytree(source, staged, symlinks=True)
        try:
            if existing:
                target.rename(previous)
            if os.path.lexists(target):
                raise FileExistsError(f"destination appeared during installation: {location}")
            staged.rename(target)
        except (OSError, KeyboardInterrupt):
            if os.path.lexists(previous) and not os.path.lexists(target):
                try:
                    previous.rename(target)
                except OSError as exc:
                    raise OSError(f"could not restore {location}; backup at {display_path(previous)}") from exc
            raise

    if existing:
        backup = archive_backup(previous, target.name)
        return f"UPDATED {source.name}: {location} (backup: {display_path(backup)})"
    return f"INSTALLED {source.name}: {location}"


def install_at_location(source: Path, target: Path, legacy: Path | None, skills_root: Path) -> str:
    if target.parent.is_relative_to(skills_root):
        raise OSError(f"destination must be outside the source skills directory: {skills_root}")
    with locked_backup(target) as previous:
        # Serialize destination selection so concurrent runs agree where a skill belongs.
        if (
            legacy is not None
            and legacy != target
            and not os.path.lexists(filesystem_path(target))
            and not os.path.lexists(previous)
        ):
            if legacy.parent.is_relative_to(skills_root):
                raise OSError(f"destination must be outside the source skills directory: {skills_root}")
            with locked_backup(legacy) as legacy_previous:
                if os.path.lexists(legacy_previous) or (filesystem_path(legacy) / "SKILL.md").is_file():
                    return install_skill(source, legacy, legacy_previous)
        return install_skill(source, target, previous)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills", nargs="*", metavar="skill", help="skill names (default: all)")
    location = parser.add_mutually_exclusive_group()
    location.add_argument(
        "--client", choices=("codex", "claude"), default="codex", help="local client (default: codex)"
    )
    location.add_argument("--dest", type=Path, help="explicit skills directory")
    args = parser.parse_args(argv)

    try:
        skills_root = (REPO_ROOT / "skills").resolve()
        available = {
            path.name: path
            for path in sorted(skills_root.iterdir())
            if not path.name.startswith(".") and path.is_dir() and (path / "SKILL.md").is_file()
        }
        unknown = sorted(set(args.skills) - available.keys())
        if unknown:
            parser.error(f"unknown skill(s): {', '.join(unknown)}")
        if not available:
            parser.error(f"no skills found in {skills_root}")

        legacy = None
        if args.dest is not None:
            destination = args.dest.expanduser().resolve()
        elif args.client == "claude":
            destination = (Path.home() / ".claude" / "skills").resolve()
        else:
            user_home = Path.home()
            destination = (user_home / ".agents" / "skills").resolve()
            codex_home = os.getenv("CODEX_HOME")
            legacy_home = Path(codex_home).expanduser() if codex_home else user_home / ".codex"
            legacy = (legacy_home / "skills").resolve()

        if destination == destination.parent:
            parser.error(f"destination cannot be a filesystem root: {destination}")
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    failed = False
    for name in dict.fromkeys(args.skills or available):
        target = destination / name
        try:
            legacy_target = (
                legacy / name if legacy is not None and filesystem_path(legacy).is_dir() else None
            )
            print(install_at_location(available[name], target, legacy_target, skills_root))
        except (OSError, RuntimeError) as exc:
            failed = True
            print(f"ERROR {name}: {exc}", file=sys.stderr)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
