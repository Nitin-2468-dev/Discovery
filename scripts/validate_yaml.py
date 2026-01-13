import sys

import yaml

p = ".github/workflows/ci.yml"
src = open(p).read()
try:
    obj = yaml.safe_load(src)
    print("yaml parse ok")
except Exception as e:
    print("yaml parse error:", e)
    sys.exit(1)
