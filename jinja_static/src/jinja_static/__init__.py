import argparse
from pathlib import Path
from asyncio import run

from .files import build
from .config import Config
from .server import server


def main():
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
    args = parser.parse_args()
    config = Config.from_(args.project_dir)
    build(config)
    if args.dev:
        run(server(args.port, config))
