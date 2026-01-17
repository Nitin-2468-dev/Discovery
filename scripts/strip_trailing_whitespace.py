FILES = [
    "probe/core/map.py",
    "probe/core/schema.py",
    "scripts/show_map_lines.py",
    "scripts/plot_sweep.py",
]

for p in FILES:
    try:
        with open(p, "rb") as fh:
            data = fh.read().decode("utf-8")
    except Exception as e:
        print(f"Could not read {p}: {e}")
        continue
    # remove trailing whitespace on each line, keep final newline
    lines = data.splitlines()
    new_lines = [ln.rstrip() for ln in lines]
    new_data = "\n".join(new_lines) + "\n"
    if new_data != data:
        with open(p, "wb") as fh:
            fh.write(new_data.encode("utf-8"))
        print(f"Fixed trailing whitespace in {p}")
    else:
        print(f"No changes for {p}")
