import tomllib
import traceback

s = open('pyproject.toml','rb').read().decode('utf-8')
try:
    tomllib.loads(s)
    print('OK')
except Exception:
    traceback.print_exc()
