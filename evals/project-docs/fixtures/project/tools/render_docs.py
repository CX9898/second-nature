"""Render the quick-start document without external dependencies."""
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
version = json.loads((root / 'project.json').read_text())['version']
template = (root / 'docs/quickstart.md.in').read_text()
(root / 'docs/quickstart.md').write_text(template.replace('@VERSION@', version))
print('Rendered docs/quickstart.md')
