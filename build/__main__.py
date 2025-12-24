import argparse
from asyncio import run

from . import build
from . import server

parser = argparse.ArgumentParser(description="Build")

parser.add_argument(
    "-d", "--dev-server", action="store_true", help="Run a development server."
)

args = parser.parse_args()

build()
if args.dev_server:
    run(server())
