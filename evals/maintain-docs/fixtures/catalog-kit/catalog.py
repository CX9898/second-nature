"""A small, stateful book index used as documentation evidence."""

import json
from pathlib import Path


class Catalog:
    def __init__(self, page_size=5):
        if type(page_size) is not int or page_size < 1:
            raise ValueError("page_size must be a positive integer")
        self.page_size = page_size
        self._books = None
        self._index = None

    @classmethod
    def from_config(cls, config):
        if set(config) - {"page_size"}:
            raise ValueError("unknown configuration field")
        return cls(page_size=config.get("page_size", 20))

    @classmethod
    def load(cls, path):
        payload = json.loads(Path(path).read_text())
        catalog = cls(page_size=payload["page_size"])
        catalog.set_index(payload["entries"])
        return catalog

    def set_books(self, books):
        rows = list(books)
        if any(set(row) != {"isbn", "title"} for row in rows):
            raise ValueError("books require isbn and title")
        self._books = rows
        self._index = None

    def prepare(self):
        if self._books is None:
            raise RuntimeError("original book records are unavailable")
        self._index = {str(row["isbn"]): str(row["title"]) for row in self._books}

    def set_index(self, entries):
        self._index = {str(isbn): str(title) for isbn, title in entries.items()}
        self._books = None

    def lookup(self, isbn):
        return self.entries()[str(isbn)]

    def entries(self):
        if self._index is None:
            raise RuntimeError("catalog is not ready")
        return dict(self._index)

    def save(self, path):
        payload = {"page_size": self.page_size, "entries": self.entries()}
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
