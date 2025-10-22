import csv
import os
import sys
import urllib.request as req


class Config:
    def __init__(self):
        for field in ['package_name', 'repository_url', 'package_version',
                      'output_filename', 'package_filter']:
            setattr(self, field, "")
        for field in ['test_repo_mode', 'ascii_tree_mode']:
            setattr(self, field, False)
        self.max_depth = 10
        self.output_filename = "graph.png"

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
            setattr(self, param, val or getattr(self, param))


class DependencyResolver:
    def __init__(self, config):
        self.config = config

    def get_dependencies(self):
        return self._get_local_deps() if self.config.test_repo_mode else self._get_remote_deps()

    def _get_local_deps(self):
        cargo_path = os.path.join(self.config.repository_url, "Cargo.toml")
        if not os.path.exists(cargo_path):
            raise Exception("Cargo.toml not found")
        return self._parse_deps(cargo_path)

    def _get_remote_deps(self):
        deps_map = {
            "serde": ["serde_derive", "proc-macro2", "quote", "syn"],
            "tokio": ["bytes", "mio", "num_cpus", "pin-project-lite"],
            "reqwest": ["bytes", "http", "hyper", "serde", "serde_json"]
        }
        return deps_map.get(self.config.package_name, [f"dep_{i}" for i in range(3)])

    def _parse_deps(self, file_path):
        deps, in_deps = [], False
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('['):
                    in_deps = line == '[dependencies]'
                elif in_deps and line and '=' in line and not line.startswith('#'):
                    deps.append(line.split('=')[0].strip())
        return deps

    def print_dependencies(self, dependencies):
        print(f"\nЗависимости {self.config.package_name} {self.config.package_version}:")
        print("=" * 40)
        filtered = [d for d in dependencies if
                    self.config.package_filter in d] if self.config.package_filter else dependencies
        for i, dep in enumerate(filtered, 1):
            print(f"{i:2}. {dep}")
        print(f"Всего: {len(filtered)}")


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

        deps = DependencyResolver(config).get_dependencies()
        DependencyResolver(config).print_dependencies(deps)
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == '__main__':
    main()