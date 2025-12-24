
import os
from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES = REPO_ROOT / "templates"
DIST_DIR = REPO_ROOT / "dist"
STATIC_DIR = REPO_ROOT / "static"

def create_dir_if_not_exist():
    DIST_DIR.mkdir(parents=True, exist_ok=True)

def rm_file_if_exists(filepath: Path):
    if filepath.exists():
        if filepath.is_dir():
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)

def build_index() -> str:
    create_dir_if_not_exist()
    INDEX_HTML = DIST_DIR / "index.html"
    rm_file_if_exists(INDEX_HTML)
    with open(INDEX_HTML, 'w') as f:
        f.write(Environment(
        loader=FileSystemLoader(TEMPLATES)
    ).get_template('index.html').render())

def copy_static_dir():
    create_dir_if_not_exist()
    DST = DIST_DIR / "static"
    rm_file_if_exists(DST)
    shutil.copytree(STATIC_DIR, DST)


def build():
    print("building index...")
    build_index()
    print("copying static files...")
    copy_static_dir()
    print("Done :)")

