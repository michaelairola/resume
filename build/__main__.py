import argparse
from pathlib import Path
from asyncio import run

from . import build
from . import Config 
from . import server

parser = argparse.ArgumentParser(description="Build")
parser.add_argument(
    "project_dir", nargs='?',            
    default=Path.cwd(), type=Path,
    help="Optional project directory path where pyproject.toml file is (default: current directory)"
)
parser.add_argument(
    "-d", "--dev", action="store_true", help="Run a development server."
)
parser.add_argument(
    "-p", "--port", default=8000, required=False, help="Port to run development server on."
)

def main():
    args = parser.parse_args()
    config = Config.from_(args.project_dir)
    build(config)
    if args.dev:
        run(server(args.port, config))

if __name__ == "__main__": 
    main()