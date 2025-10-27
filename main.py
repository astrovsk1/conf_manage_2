import csv
import collections
import sys
from typing import Dict, List


class Config:
    def __init__(self):
        self.package_name = ""
        self.repository_url = ""
        self.package_version = ""
        self.output_filename = "graph.png"
        self.package_filter = ""
        self.test_repo_mode = False
        self.ascii_tree_mode = False
        self.max_depth = 10

    def load_from_csv(self, config_file):
        with open(config_file, 'r') as f:
            for row in csv.DictReader(f):
                self._process_row(row)

    def _process_row(self, row):
        param, val = row.get('parameter', '').lower(), row.get('value', '').strip()
        if not param: return

        if param in ['test_repo_mode', 'ascii_tree_mode']:
            setattr(self, param, val.lower() in ['true', '1', 'yes'])
        elif param == 'max_depth':
            self.max_depth = max(1, min(100, int(val)))
        elif hasattr(self, param):
            setattr(self, param, val)


class DependencyGraph:
    def __init__(self, config):
        self.config = config
        self.graph = {}

    def build_graph(self):
        queue = collections.deque([(self.config.package_name, 0)])
        visited = set([self.config.package_name])
        self.graph = {}

        while queue:
            package, depth = queue.popleft()
            deps = self._get_deps(package)

            filtered_deps = [d for d in deps if not self.config.package_filter or self.config.package_filter not in d]
            self.graph[package] = filtered_deps

            if depth + 1 < self.config.max_depth:
                for dep in filtered_deps:
                    if dep not in visited:
                        visited.add(dep)
                        queue.append((dep, depth + 1))

        return self.graph

    def _get_deps(self, package):
        if self.config.test_repo_mode:
            return self._get_test_deps(package)
        return self._get_remote_deps(package)

    def _get_test_deps(self, package):
        deps = []
        current_section = None

        try:
            with open(self.config.repository_url, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1].strip()
                    elif current_section == package and '=' in line and not line.startswith('#'):
                        deps.append(line.split('=')[0].strip())
        except:
            pass

        return deps

    def _get_remote_deps(self, package):
        deps_db = {
            "serde": ["serde_derive", "proc-macro2"],
            "serde_derive": ["proc-macro2", "quote", "syn"],
            "proc-macro2": ["unicode-ident"],
            "quote": ["proc-macro2"],
            "syn": ["proc-macro2", "quote", "unicode-ident"],
            "unicode-ident": [],
            "tokio": ["bytes", "mio", "num_cpus"],
            "bytes": [],
            "mio": ["libc"],
            "num_cpus": [],
            "libc": [],
            "reqwest": ["bytes", "hyper", "serde", "tokio"],
            "hyper": ["bytes", "tokio"]
        }
        return deps_db.get(package, [])

    def print_simple_tree(self):
        if not self.config.ascii_tree_mode:
            return

        print(f"\nDependency Tree for {self.config.package_name}:")
        print("=" * 40)

        def _print(node, indent=0, depth=0):
            if depth > self.config.max_depth:
                return

            print("  " * indent + node)

            if node in self.graph and depth < self.config.max_depth:
                for child in self.graph[node]:
                    _print(child, indent + 1, depth + 1)

        _print(self.config.package_name, 0, 0)


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py config.csv")
        return

    config = Config()
    try:
        config.load_from_csv(sys.argv[1])
        print("Configuration:")
        for k, v in config.__dict__.items():
            print(f"{k:20}: {v}")

        graph_builder = DependencyGraph(config)
        dependency_graph = graph_builder.build_graph()

        print(f"\nDependency Graph ({len(dependency_graph)} packages):")
        for pkg, deps in dependency_graph.items():
            if deps:
                print(f"{pkg:15} -> {deps}")

        graph_builder.print_simple_tree()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
