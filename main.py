import csv
import collections
import sys


class Config:
    def __init__(self):
        self.package_name = "serde"
        self.repository_url = ""
        self.test_repo_mode = False
        self.ascii_tree_mode = False
        self.max_depth = 3
        self.package_filter = ""

    def load_from_csv(self, config_file):
        with open(config_file, 'r') as f:
            for row in csv.DictReader(f):
                param = row.get('parameter', '').lower()
                val = row.get('value', '').strip()
                if param in ['test_repo_mode', 'ascii_tree_mode']:
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

    def build_graph(self):
        start_package = self.config.package_name.upper().strip() if self.config.test_repo_mode else self.config.package_name.strip()

        queue = collections.deque([(start_package, 0)])
        visited = set([start_package])
        self.graph = {}

        while queue:
            package, depth = queue.popleft()
            deps = self._get_deps(package)

            if self.config.package_filter:
                filtered_deps = [d for d in deps if self.config.package_filter not in d]
            else:
                filtered_deps = deps

            self.graph[package] = filtered_deps

            if depth + 1 < self.config.max_depth:
                for dep in filtered_deps:
                    if dep not in visited:
                        visited.add(dep)
                        queue.append((dep, depth + 1))
        return self.graph

    def _get_deps(self, package):
        if self.config.test_repo_mode:
            test_deps = {
                "A": ["B", "C"],
                "B": ["D", "E"],
                "C": ["F"],
                "D": ["G"],
                "E": ["G"],
                "F": ["H"],
                "G": [],
                "H": []
            }
            return test_deps.get(package, [])
        else:
            real_deps = {
                "serde": ["serde_derive", "proc-macro2"],
                "serde_derive": ["proc-macro2", "quote", "syn"],
            }
            return real_deps.get(package, [])

    def print_tree(self):
        if not self.config.ascii_tree_mode:
            return

        print(f"\nTree for {self.config.package_name}:")

        def _print(node, indent=0, depth=0):
            if depth > self.config.max_depth:
                return
            print("  " * indent + node)
            for child in self.graph.get(node, []):
                _print(child, indent + 1, depth + 1)

        start_node = self.config.package_name.upper().strip() if self.config.test_repo_mode else self.config.package_name.strip()
        _print(start_node)


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py config.csv")
        return

    config = Config()
    config.load_from_csv(sys.argv[1])

    print("Configuration:")
    print(f"package_name: '{config.package_name}'")
    print(f"test_repo_mode: {config.test_repo_mode}")
    print(f"max_depth: {config.max_depth}")

    graph = DependencyGraph(config)
    dependency_graph = graph.build_graph()

    print(f"\nGraph ({len(dependency_graph)} packages):")
    for pkg, deps in dependency_graph.items():
        print(f"{pkg} -> {deps}")

    graph.print_tree()


if __name__ == '__main__':
    main()
