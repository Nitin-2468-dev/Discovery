import ast
from pathlib import Path
p = Path('probe/core/map.py')
src = p.read_text()
mod = ast.parse(src)
for node in ast.walk(mod):
    if isinstance(node, ast.FunctionDef):
        if node.returns and isinstance(node.returns, ast.Name) and node.returns.id == 'int':
            has_bare = False
            for n in ast.walk(node):
                if isinstance(n, ast.Return) and n.value is None:
                    print(f"Function {node.name} at line {node.lineno} has bare return")
                    has_bare = True
            if not has_bare:
                print(f"Function {node.name} at line {node.lineno} has no bare returns")
