from pathlib import Path

p = Path("probe/core/map.py")
for i, line in enumerate(p.read_text().splitlines(), 1):
    if 320 <= i <= 340:
        print(f"{i}: {line}")
