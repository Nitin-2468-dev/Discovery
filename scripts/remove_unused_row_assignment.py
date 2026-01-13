from pathlib import Path
p = Path('probe/core/map.py')
s = p.read_text()
marker = 'INSERT INTO domains (domain_name, pages_crawled, documents_found, yield_score)'
idx = s.find(marker)
if idx == -1:
    print('Marker not found')
else:
    # search for 'row = cursor.fetchone()' after marker
    after = s[idx:]
    target = '\n        row = cursor.fetchone()\n'
    if target in after:
        new_after = after.replace(target, '\n', 1)
        new_s = s[:idx] + new_after
        p.write_text(new_s)
        print('Removed unused row assignment after INSERT INTO domains')
    else:
        print('No unused row assignment found after marker')
