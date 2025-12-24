import os
from pathlib import Path
import shutil
from functools import wraps
from asyncio import create_task, sleep
from datetime import datetime
import traceback

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .meta import dependency_graph
from .config import Config

def rm_file_if_exists(file_path: Path):
    if file_path.exists():
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)

def build_page(config: Config, filename: str) -> int:
    return_status = 0
    config.dist.mkdir(parents=True, exist_ok=True)
    FILE_PATH = config.dist / filename 
    rm_file_if_exists(FILE_PATH)
    try:
        rendered_file = Environment(loader=FileSystemLoader(config.templates))\
            .get_template(filename)\
            .render()
    except Exception as e:
        rendered_file = "\n".join([ 
            str(e), 
            "-"*40, 
            traceback.format_exc() 
        ])
        print(rendered_file)
        rendered_file = rendered_file.replace("\n", "<br/>")
        return_status = 1

    with open(FILE_PATH, "w") as f:
        f.write(rendered_file)
    return return_status

def build_pages(config: Config):
    for page in config.pages:
        build_page(config, page)


def copy_static_dir(config: Config):
    config.dist.mkdir(parents=True, exist_ok=True)
    DST = config.dist / "static"
    rm_file_if_exists(DST)
    shutil.copytree(config.static, DST)


def build(config: Config) -> bool:
    rm_file_if_exists(config.dist)
    print("building index...")
    build_pages(config)
    print("copying static files...")
    copy_static_dir(config)
    print("Done :)")
    return True


def copy_static_file(config: Config, file_path: str):
    config.dist.mkdir(parents=True, exist_ok=True)
    DST = config.dist / "static" / file_path.name
    rm_file_if_exists(DST)
    shutil.copy(file_path, DST)


def watch_for_file_changes(func):
    @wraps(func)
    async def wrapper(file_path, *args, **kwargs):
        last_modified = os.path.getmtime(file_path)
        while True:
            current_modified = os.path.getmtime(file_path)
            if current_modified != last_modified:
                print(f"File {file_path.name} has changed...", end=" ")
                func(file_path, *args, **kwargs)
                print(f"Rebuilt @ {datetime.fromtimestamp(current_modified)}")
                last_modified = current_modified
            await sleep(1)

    return wrapper


@watch_for_file_changes
def detect_changes_build_index(file_path, config, graph):
    if file_path.name in config.pages:
        build_page(config, file_path.name)
    parent_files = graph.get(file_path.name, [])
    for parent_file in parent_files:
        build_page(config, parent_file)


@watch_for_file_changes
def detect_changes_copy_static_file(file_path, config):
    copy_static_file(config, file_path)


def file_watcher(config: Config):
    graph = dependency_graph(config)
    for file_path in config.templates.rglob("*"):
        create_task(detect_changes_build_index(file_path, config, graph))
    for file_path in config.static.rglob("*"):
        create_task(detect_changes_copy_static_file(file_path, config))
