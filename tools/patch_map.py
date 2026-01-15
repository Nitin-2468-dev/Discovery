from pathlib import Path
p=Path('probe/core/map.py')
s=p.read_text()
# Replace the edge return to ensure int is always returned
s=s.replace('return edge_id if edge_id != 0 else None','# Normalize to integer return value (0 indicates no new row inserted)\n        return int(edge_id) if edge_id and edge_id != 0 else 0  # type: ignore[return-value]')
# Replace params = [] with typed list for scoring_reports query
s=s.replace('\n        params = []\n        if url:','\n        params: list[object] = []\n        if url:')
# Write back
p.write_text(s)
print('patched map.py')
