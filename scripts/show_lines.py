from pathlib import Path
p = Path('tests/test_offline_e2e.py').read_text().splitlines()
for i in range(len(p)):
    if 168 <= i+1 <= 180:
        print(f"{i+1:4d}: {p[i]}")
