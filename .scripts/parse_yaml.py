import sys

import yaml

p = sys.argv[1]
try:
    s = open(p, "r", encoding="utf-8").read()
    yaml.safe_load(s)
    print("ok")
except Exception as e:
    print("err", e)
