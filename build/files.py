import os
from pathlib import Path
import shutil
from functools import wraps
from asyncio import create_task, sleep
from datetime import datetime
import traceback

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES = Path.cwd() / "templates"
DIST_DIR = Path.cwd() / "dist"
STATIC_DIR = Path.cwd() / "static"

def rm_file_if_exists(filepath: Path):
    if filepath.exists():
        if filepath.is_dir():
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)


def build_index() -> int:
    return_status = 0
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_HTML = DIST_DIR / "index.html"
    rm_file_if_exists(INDEX_HTML)
    try:
        built_index = Environment(loader=FileSystemLoader(TEMPLATES))\
            .get_template("index.html")\
            .render()
    except Exception as e:
        built_index = "\n".join([ 
            str(e), 
            "-"*40, 
            traceback.format_exc() 
        ])
        print(built_index)
        built_index = built_index.replace("\n", "<br/>")
        return_status = 1

    with open(INDEX_HTML, "w") as f:
        f.write(built_index)
    return return_status


def copy_static_dir():
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DST = DIST_DIR / "static"
    rm_file_if_exists(DST)
    shutil.copytree(STATIC_DIR, DST)


def build() -> bool:
    print("building index...")
    build_index()
    print("copying static files...")
    copy_static_dir()
    print("Done :)")
    return True


def copy_static_file(file_path: str):
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DST = DIST_DIR / "static" / file_path.name
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
def detect_changes_build_index(file_path):
    build_index()


@watch_for_file_changes
def detect_changes_copy_static_file(file_path):
    copy_static_file(file_path)


def file_watcher():
    for file_path in TEMPLATES.rglob("*"):
        create_task(detect_changes_build_index(file_path))
    for file_path in STATIC_DIR.rglob("*"):
        create_task(detect_changes_copy_static_file(file_path))
