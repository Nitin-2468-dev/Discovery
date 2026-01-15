from pathlib import Path
lines = Path('probe/core/map.py').read_text().splitlines()
for i in range(384,396):
    print(f"{i+1:4d}: {repr(lines[i])}")
print('---')
for i in range(500,518):
    print(f"{i+1:4d}: {repr(lines[i])}")
