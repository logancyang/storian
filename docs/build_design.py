"""Inline docs/survey.json into docs/design.src.html -> docs/design.html (single self-contained file)."""
import json
from pathlib import Path

here = Path(__file__).parent
survey = json.dumps(json.loads((here / "survey.json").read_text()), ensure_ascii=False).replace("</", "<\\/")
html = (here / "design.src.html").read_text().replace("__SURVEY__", survey)
(here / "design.html").write_text(html)
print(f"wrote {here / 'design.html'} ({len(html) // 1024} KB)")
