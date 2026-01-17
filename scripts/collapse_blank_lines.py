import re
from pathlib import Path

files = ["README.md", "SCOPE.md", "docs/fetcher.md", "docs/seeds.md"]
for f in files:
    p = Path(f)
    s = p.read_text()
    # replace 3+ newlines with exactly 2 newlines (i.e., a single blank line between paragraphs)
    new = re.sub(r"\n{3,}", "\n\n", s)
    if new != s:
        p.write_text(new)
        print(f"normalized {f}")
    else:
        print(f"no change {f}")
