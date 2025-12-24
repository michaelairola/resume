from functools import wraps
from asyncio import create_task, sleep
import asyncio
import os
from datetime import datetime

import shutil

from . import build_index, create_dir_if_not_exist, rm_file_if_exists
from . import TEMPLATES, STATIC_DIR, DIST_DIR

def copy_static_file(file_path: str):
    create_dir_if_not_exist()
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
                print(f"File {file_path.name} has changed...", end=' ')
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

def watch_template_changes():
    for file_path in TEMPLATES.rglob("*"):
        create_task(detect_changes_build_index(file_path))
    for file_path in STATIC_DIR.rglob("*"):
        create_task(detect_changes_copy_static_file(file_path))
