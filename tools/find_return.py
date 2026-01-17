from pathlib import Path

s = Path("probe/core/map.py").read_text()
needle = "return edge_id if edge_id != 0 else None"
idx = s.find(needle)
print("idx=", idx)
if idx != -1:
    start = s.rfind("\n", 0, idx)
    end = s.find("\n", idx)
    line = s[start + 1 : end]
    print("line repr:", repr(line))
    print("line bytes:", line.encode())
else:
    print("not found")
