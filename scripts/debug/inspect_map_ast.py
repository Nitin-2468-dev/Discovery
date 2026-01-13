"""Developer helper: inspect the AST of probe/core/map.py to locate helper definitions.

Moved to scripts/debug for developer use.
"""

import ast
p = 'probe/core/map.py'
src = open(p).read()
mod = ast.parse(src)
funcs = [n.name for n in ast.walk(mod) if isinstance(n, ast.FunctionDef)]
classes = [n.name for n in ast.walk(mod) if isinstance(n, ast.ClassDef)]
print('classes:', classes)
print('functions:', funcs)
print('_map_get_domains_with_doc_type' in funcs)
# Find the try/except location
for node in mod.body:
    if isinstance(node, ast.Try):
        print('found module-level try with handlers:', node.handlers)
        for h in node.handlers:
            print('handler type:', type(h).__name__)
            for stmt in h.body:
                if isinstance(stmt, ast.FunctionDef):
                    print('func in except:', stmt.name)

# show the index of _map_get_domains_with_doc_type in body
for i,stmt in enumerate(mod.body[:380]):
    if isinstance(stmt, ast.FunctionDef) and stmt.name == '_map_get_domains_with_doc_type':
        print('helper at module.body index', i)
        break
