from pathlib import Path
from asyncio import (
    CancelledError,
    StreamReader,
    StreamWriter,
    all_tasks,
    create_task,
    run,
    sleep,
)
import traceback
import mimetypes
import asyncio

from . import DIST_DIR
from .file_watcher import file_watcher


async def receive_http_get_request(reader: StreamReader):
    request_data = b""
    while True:
        line = await reader.readline()
        if not line:
            # EOF reached without completing headers
            break
        request_data += line
        if line == b"\r\n":
            # Found the end of headers
            break
    headers = request_data.decode().split("\r\n")
    method, uri, _ = headers.pop(0).split(" ")
    return method, uri


def read_file(file_path: Path) -> tuple[str, str]:
    assert file_path.is_relative_to(DIST_DIR.resolve()), (
        f"File '{file_path}' is not located in distribution directory '{DIST_DIR}'"
    )
    with open(file_path, "r") as file:
        file_data = file.read()
    mime_type, _ = mimetypes.guess_type(file_path.name)
    return file_data, mime_type


async def send_http_response(
    writer: StreamWriter,
    response_body: str,
    status: int = 200,
    content_type: str = "text/plain",
):
    response_header = (
        f"HTTP/1.1 {status} OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        f"\r\n"
    )
    response = response_header + response_body
    writer.write(response.encode("utf-8"))
    await writer.drain()


async def handle_request(reader: StreamReader, writer: StreamWriter):
    try:
        method, uri = await receive_http_get_request(reader)
        # TODO make more robust, parse URI with urllib.
        uri = uri.removeprefix("/")
        uri = uri or "index.html"
        FILE_PATH = (DIST_DIR / uri).resolve()

        if FILE_PATH.name == "500.html":
            raise Exception(
                "Internal Server Test",
                "This should always return an 500 internal server error.",
            )
        assert method == "GET", (
            "This is a Static server! You can only make GET requests."
        )
        assert FILE_PATH.is_file(), f"No File '{FILE_PATH}' found."

        response_body, mime_type = read_file(FILE_PATH)
        await send_http_response(writer, response_body, content_type=mime_type)
    except AssertionError as e:
        response_body = ",".join(e.args)
        await send_http_response(writer, response_body, status=400)
    except Exception as e:
        response_body = "\n".join(
            ["EXCEPTION:", *e.args, "-" * 40, traceback.format_exc()]
        )
        print(response_body)
        await send_http_response(writer, response_body, status=500)
    finally:
        writer.close()
        await writer.wait_closed()


async def server():
    PORT = 8000
    file_watcher()
    server = await asyncio.start_server(handle_request, "127.0.0.1", PORT)
    print(f"Serving on port {PORT}")
    async with server:
        await server.serve_forever()
