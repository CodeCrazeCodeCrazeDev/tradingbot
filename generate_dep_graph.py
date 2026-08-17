import os
import re
from collections import defaultdict

def get_imports(file_path):
    imports = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Match 'from .module import ...'
            match = re.match(r'from \.(\w+) import', line)
            if match:
                imports.append(match.group(1))
            # Match 'from . import ...'
            match = re.match(r'from \. import (\w+)', line)
            if match:
                imports.append(match.group(1))
    return imports

def generate_dependency_graph(directory):
    graph = defaultdict(list)
    files = [f for f in os.listdir(directory) if f.endswith('.py') and f != '__init__.py']

    for file in files:
        module_name = file[:-3]
        file_path = os.path.join(directory, file)
        imports = get_imports(file_path)
        for imp in imports:
            graph[module_name].append(imp)

    print("digraph G {")
    print("  rankdir=LR;")
    for node, edges in graph.items():
        for edge in edges:
            print(f"  {node} -> {edge};")
    print("}")

if __name__ == "__main__":
    generate_dependency_graph("trading_bot/core_agent_system")
