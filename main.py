import csv
import collections
import sys
import graphviz
import os

os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

class Config:
    def __init__(self):
        self.package_name = "serde"
        self.package_version = "1.0"
        self.repository_url = ""
        self.test_repo_mode = False
        self.ascii_tree_mode = False
        self.max_depth = 3
        self.package_filter = ""
        self.output_filename = "graph.png"
        self.generate_image = False

    def load_from_csv(self, config_file):
        with open(config_file, 'r') as f:
            for row in csv.DictReader(f):
                param = row.get('parameter', '').lower()
                val = row.get('value', '').strip()
                if param in ['test_repo_mode', 'ascii_tree_mode', 'generate_image']:
                    setattr(self, param, val.lower() in ['true', '1', 'yes'])
                elif param == 'max_depth':
                    try:
                        self.max_depth = int(val)
                    except ValueError:
                        pass
                elif hasattr(self, param):
                    setattr(self, param, val)


class DependencyGraph:
    def __init__(self, config):
        self.config = config
        self.graph = {}
        self.cycles = []

    def build_graph(self):
        start_package = self.config.package_name.upper() if self.config.test_repo_mode else self.config.package_name
        queue = collections.deque([(start_package, 0, [])])
        visited = set([start_package])
        self.graph = {}
        self.cycles = []

        while queue:
            package, depth, path = queue.popleft()
            current_path = path + [package]

            if package in path:
                cycle_path = path[path.index(package):] + [package]
                cycle_str = " -> ".join(cycle_path)
                if cycle_str not in self.cycles:
                    self.cycles.append(cycle_str)
                if package not in self.graph:
                    self.graph[package] = []
                continue

            deps = self._get_deps(package)
            filtered_deps = [d for d in deps if not self.config.package_filter or self.config.package_filter not in d]

            for dep in deps:
                if dep in current_path:
                    cycle_path = current_path + [dep]
                    cycle_str = " -> ".join(cycle_path)
                    if cycle_str not in self.cycles:
                        self.cycles.append(cycle_str)

            self.graph[package] = filtered_deps

            if depth + 1 < self.config.max_depth:
                for dep in filtered_deps:
                    if dep not in visited:
                        visited.add(dep)
                        queue.append((dep, depth + 1, current_path))

        return self.graph

    def _get_deps(self, package):
        if self.config.test_repo_mode:
            test_deps = {
                "A": ["B", "C"], "B": ["D", "E"], "C": ["F", "A"],
                "D": ["G"], "E": ["G", "B"], "F": ["H", "A"],
                "G": [], "H": []
            }
            return test_deps.get(package, [])
        else:
            real_deps = {
                "serde": ["serde_derive", "proc-macro2"],
                "serde_derive": ["proc-macro2", "quote", "syn"],
                "proc-macro2": ["unicode-ident", "quote"],
                "quote": ["proc-macro2"],
                "syn": ["proc-macro2", "quote", "unicode-ident"],
                "unicode-ident": []
            }
            return real_deps.get(package, [])

    def print_tree(self):
        if not self.config.ascii_tree_mode:
            return

        start = self.config.package_name.upper() if self.config.test_repo_mode else self.config.package_name

        def _print(node, indent=0, depth=0, visited=None):
            if visited is None:
                visited = set()
            if depth > self.config.max_depth or node in visited:
                return
            visited.add(node)
            print("  " * indent + node)
            for child in self.graph.get(node, []):
                _print(child, indent + 1, depth + 1, visited.copy())

        _print(start)

    def generate_graphviz(self):
        if not self.config.generate_image:
            return

        try:
            # Пробуем найти Graphviz в стандартных путях
            import os
            possible_paths = [
                'C:/Program Files/Graphviz/bin/',
                'C:/Program Files (x86)/Graphviz/bin/',
                'D:/Program Files/Graphviz/bin/'
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    os.environ["PATH"] += os.pathsep + path
                    break

            dot = graphviz.Digraph(comment='Dependency Graph')

            for package in self.graph:
                dot.node(package)

            for package, deps in self.graph.items():
                for dep in deps:
                    dot.edge(package, dep)

            dot.render(self.config.output_filename, format='png', cleanup=True)
            print(f"Граф сохранен в файл: {self.config.output_filename}")

        except Exception as e:
            print(f"Graphviz не доступен: {e}")
            print("Создаю текстовый файл с описанием графа...")

            dot_content = "digraph G {\n"
            for package, deps in self.graph.items():
                for dep in deps:
                    dot_content += f'  "{package}" -> "{dep}";\n'
            dot_content += "}"

            dot_filename = self.config.output_filename.replace('.png', '.dot')
            with open(dot_filename, 'w') as f:
                f.write(dot_content)

            print(f"Файл Graphviz сохранен: {dot_filename}")
            print("Установите Graphviz с https://graphviz.org/download/")

    def print_graphviz_text(self):
        print("Graphviz представление:")
        print("digraph G {")
        for package, deps in self.graph.items():
            for dep in deps:
                print(f'  "{package}" -> "{dep}";')
        print("}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py config.csv")
        return

    config = Config()
    config.load_from_csv(sys.argv[1])

    print("Конфигурация:")
    for attr in ['package_name', 'package_version', 'repository_url', 'test_repo_mode',
                 'ascii_tree_mode', 'max_depth', 'package_filter', 'output_filename', 'generate_image']:
        print(f"{attr}: {getattr(config, attr)}")

    graph = DependencyGraph(config)
    dependency_graph = graph.build_graph()

    print("\nГраф зависимостей:")
    for pkg, deps in dependency_graph.items():
        print(f"{pkg} -> {deps}")

    print("\nASCII-ДЕРЕВО")
    graph.print_tree()

    graph.print_graphviz_text()
    graph.generate_graphviz()


if __name__ == '__main__':
    main()