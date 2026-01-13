"""Development helper: inspect the currently imported probe.core.map module and attach the compatibility helper if present.

Moved to `scripts/debug/` and intended for local debugging only.
"""

import probe.core.map as mod
from probe.core.map import Map
print('before:', hasattr(Map, 'get_domains_with_doc_type'))
print('helpers in module:', [n for n in dir(mod) if 'map_get_domains' in n or 'get_domains_with' in n])
if hasattr(mod, '_map_get_domains_with_doc_type'):
    Map.get_domains_with_doc_type = mod._map_get_domains_with_doc_type
print('after:', hasattr(Map, 'get_domains_with_doc_type'))
# show signature
import inspect
if hasattr(Map, 'get_domains_with_doc_type'):
    print('sig:', inspect.signature(Map.get_domains_with_doc_type))