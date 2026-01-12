"""Development helper: load a fresh copy of probe.core.map and attach the compatibility helper to the runtime Map class.

This script is for interactive debugging only. It is intentionally not part of the public API and lives under `scripts/debug/`.
"""

from importlib.machinery import SourceFileLoader
m = SourceFileLoader('map_fresh','probe/core/map.py').load_module()
print('fresh has helper?', hasattr(m,'_map_get_domains_with_doc_type'))
from probe.core.map import Map
if hasattr(m,'_map_get_domains_with_doc_type'):
    Map.get_domains_with_doc_type = m._map_get_domains_with_doc_type
print('Map has now?', hasattr(Map,'get_domains_with_doc_type'))