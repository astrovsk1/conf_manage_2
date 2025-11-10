import csv
import collections
import sys


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
        self.show_load_order = False

    def load_from_csv(self, config_file):
        with open(config_file, 'r') as f:
            for row in csv.DictReader(f):
                param = row.get('parameter', '').lower()
                val = row.get('value', '').strip()
                if param in ['test_repo_mode', 'ascii_tree_mode', 'show_load_order']:
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

    def get_direct_dependencies(self):
        package = self.config.package_name.upper() if self.config.test_repo_mode else self.config.package_name
        deps = self._get_deps(package)
        print(f"Пакет: {package} (версия: {self.config.package_version})")
        print(f"Прямые зависимости: {deps}")
        return deps

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

    def print_statistics(self):
        print(f"Всего пакетов: {len(self.graph)}")
        print(f"Всего зависимостей: {sum(len(deps) for deps in self.graph.values())}")
        print(f"Обнаружено циклов: {len(self.cycles)}")
        for cycle in self.cycles:
            print(f"  - {cycle}")

    def calculate_load_order(self):
        if not self.config.show_load_order:
            return

        visited = set()
        stack = []

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for neighbor in self.graph.get(node, []):
                dfs(neighbor)
            stack.append(node)

        start_node = self.config.package_name.upper() if self.config.test_repo_mode else self.config.package_name
        dfs(start_node)

        print(f"Порядок загрузки:")
        for i, package in enumerate(stack, 1):
            print(f"  {i}. {package}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py config.csv")
        return

    config = Config()
    config.load_from_csv(sys.argv[1])

    print("Конфигурация:")
    for attr in ['package_name', 'package_version', 'repository_url', 'test_repo_mode',
                 'ascii_tree_mode', 'max_depth', 'package_filter', 'output_filename', 'show_load_order']:
        print(f"{attr}: {getattr(config, attr)}")

    graph = DependencyGraph(config)

    print("\nПрямые зависимости:")
    graph.get_direct_dependencies()

    dependency_graph = graph.build_graph()

    print("\nГраф зависимостей:")
    for pkg, deps in dependency_graph.items():
        print(f"{pkg} -> {deps}")

    print("\nASCII-ДЕРЕВО")
    graph.print_tree()

    print("\nВывод:")
    graph.print_statistics()

    graph.calculate_load_order()


if __name__ == '__main__':
    main()