"""Utility: quickly check whether map.py defines the compatibility helper.

Moved to scripts/debug and intended for local developer use only.
"""

code = open("probe/core/map.py").read()
G = {}
try:
    exec(code, G)
    print("exec succeeded, helper present:", "_map_get_domains_with_doc_type" in G)
except Exception as e:
    import traceback

    print("exec exception:", type(e), e)
    traceback.print_exc()
