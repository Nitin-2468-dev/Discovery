import yaml
import glob
import sys

ok = True
files = glob.glob('.github/workflows/*.yml') + glob.glob('.github/workflows/*.yaml')
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            yaml.safe_load(fh)
    except Exception as e:
        print('ERROR parsing', f, ':', e)
        ok = False
if not ok:
    sys.exit(1)
print('All workflow YAMLs parse')
