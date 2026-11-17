"""Render a catalog using its bundled report template."""

from pathlib import Path


def write_report(catalog, output):
    template_path = Path(__file__).parent / "templates" / "card.txt"
    template = template_path.read_text()
    rows = [template.format(isbn=isbn, title=title).rstrip()
            for isbn, title in sorted(catalog.entries().items())]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(rows) + "\n")
