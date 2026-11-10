"""Build an index or render a saved index without external dependencies."""

import argparse
import json
from pathlib import Path

from catalog import Catalog


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--source", type=Path, required=True)
    build.add_argument("--config", type=Path)
    build.add_argument("--page-size", type=int)
    build.add_argument("--output", type=Path, required=True)
    report = commands.add_parser("report")
    report.add_argument("--index", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "build":
        config = json.loads(args.config.read_text()) if args.config else {}
        if args.page_size is not None:
            config["page_size"] = args.page_size
        catalog = Catalog.from_config(config)
        catalog.set_books(json.loads(args.source.read_text()))
        catalog.prepare()
        catalog.save(args.output)
    else:
        from reporting import write_report

        write_report(Catalog.load(args.index), args.output)
    print(f"Created: {args.output}")


if __name__ == "__main__":
    main()
