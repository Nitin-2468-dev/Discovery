"""Generate `tests/fixtures/sample.pdf` using reportlab.

Run this script manually if you want to create a committed fixture for CI.
Requires: `reportlab` package.
"""
import io
from pathlib import Path

from reportlab.pdfgen import canvas

out = Path(__file__).parent.parent / "fixtures" / "sample.pdf"
out.parent.mkdir(parents=True, exist_ok=True)

buf = io.BytesIO()
c = canvas.Canvas(buf)
c.drawString(72, 720, "Sample fixture PDF text")
c.showPage()
c.save()

with open(out, "wb") as f:
    f.write(buf.getvalue())

print(f"Wrote {out}")
