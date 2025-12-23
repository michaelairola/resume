import time
import os
import shutil
from functools import wraps
from pathlib import Path
from asyncio import (
    CancelledError,
    StreamReader,
    StreamWriter,
    all_tasks,
    create_task,
    run, 
    sleep
)
import mimetypes
import asyncio
from datetime import datetime
import http.server
import socketserver
from functools import partial
import traceback

from jinja2 import Environment, FileSystemLoader, select_autoescape


REPO_ROOT = Path(__file__).parent
TEMPLATES = REPO_ROOT / "templates"
DIST_DIR = REPO_ROOT / "dist"
STATIC_DIR = REPO_ROOT / "static"


def create_dist_if_not_exist():
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def rm_file_if_exists(filepath: Path):
    if filepath.exists():
        if filepath.is_dir():
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)


def index_html():
    return Environment(
        loader=FileSystemLoader(TEMPLATES)
    ).get_template('index.html').render()


def build_index() -> str:
    create_dist_if_not_exist()
    INDEX_HTML = DIST_DIR / "index.html"
    rm_file_if_exists(INDEX_HTML)
    with open(INDEX_HTML, 'w') as f:
        f.write(index_html())

def copy_static_file(file_path: str):
    create_dist_if_not_exist()
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


def copy_static_dir():
    create_dist_if_not_exist()
    DST = DIST_DIR / "static"
    rm_file_if_exists(DST)
    shutil.copytree(STATIC_DIR, DST)


def build():
    build_index()
    copy_static_dir()

async def receive_http_get_request(reader: StreamReader):
    request_data = b""  
    while True:
        line = await reader.readline()
        if not line:
            # EOF reached without completing headers
            break
        request_data += line
        if line == b'\r\n':
            # Found the end of headers
            break
    headers = request_data.decode().split('\r\n')
    method, uri, _ = headers.pop(0).split(" ")
    return method, uri

def read_file(file_path: Path) -> tuple[str, str]:
    assert file_path.is_relative_to(DIST_DIR.resolve()), f"File '{file_path}' is not located in distribution directory '{DIST_DIR}'" 
    with open(file_path, 'r') as file:
        file_data = file.read()
    mime_type, _ = mimetypes.guess_type(file_path.name)
    return file_data, mime_type

async def send_http_response(writer: StreamWriter, response_body: str, status: int = 200, content_type: str = "text/plain"):
    response_header = (
        f"HTTP/1.1 {status} OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        f"\r\n"
    )
    response = response_header + response_body
    writer.write(response.encode('utf-8'))
    await writer.drain()


async def handle_request(reader: StreamReader, writer: StreamWriter):
    try:
        method, uri = await receive_http_get_request(reader)
        # TODO make more robust, parse URI with urllib. 
        uri = uri.removeprefix("/")
        uri = uri or "index.html"
        FILE_PATH = (DIST_DIR / uri).resolve()
        
        if FILE_PATH.name == "500.html":
            raise Exception("Internal Server Test", "This should always return an 500 internal server error.")
        assert method == "GET", "This is a Static server! You can only make GET requests."
        assert FILE_PATH.is_file(), f"No File '{FILE_PATH}' found."

        response_body, mime_type = read_file(FILE_PATH)
        await send_http_response(
            writer,
            response_body,
            content_type=mime_type
        )
    except AssertionError as e:
        response_body = ",".join(e.args)
        await send_http_response(
            writer, response_body, status=400
        )
    except Exception as e:
        response_body = "\n".join([ "EXCEPTION:", *e.args, '-'*40, traceback.format_exc() ])        
        print(response_body)
        await send_http_response(
            writer, response_body, status=500
        )
    finally:
        writer.close()
        await writer.wait_closed()

async def dev_server():
    PORT = 8000
    build()
    watch_template_changes()   
    server = await asyncio.start_server(
        handle_request, '127.0.0.1', PORT)
    print(f"Serving on port {PORT}")
    async with server:
        await server.serve_forever()


run(dev_server())



