from pathlib import Path

p = Path("constraints.log")
s = p.read_text()
lines = s.splitlines(True)
for line in lines[-12:]:
    print(repr(line))
