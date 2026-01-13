"""Developer helper: print a segment of map.py with repr() for debugging line endings/whitespace issues.

Moved to scripts/debug for developer use.
"""

p='probe/core/map.py'
for i,line in enumerate(open(p).read().splitlines(),1):
    if 288 <= i <= 340:
        print(i, repr(line))