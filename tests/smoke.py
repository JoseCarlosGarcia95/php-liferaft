#!/usr/bin/env python3
"""Exercise a local Docker runtime using benign CLI and FastCGI requests."""

import argparse
import json
from pathlib import Path
import socket
import struct
import subprocess
import time
import uuid


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def record(kind, data=b""):
    return struct.pack("!BBHHBB", 1, kind, 1, len(data), 0, 0) + data


def params(values):
    result = bytearray()
    for key, value in values.items():
        key, value = key.encode(), str(value).encode()
        for length in (len(key), len(value)):
            result.extend(bytes([length]) if length < 128 else struct.pack("!I", length | 0x80000000))
        result.extend(key + value)
    return bytes(result)


def read_exact(connection, length):
    result = bytearray()
    while len(result) < length:
        part = connection.recv(length - len(result))
        if not part:
            raise RuntimeError("FPM closed an incomplete FastCGI response")
        result.extend(part)
    return bytes(result)


def robust_request(*args, **kwargs):
    for attempt in range(4):
        try:
            return request(*args, **kwargs)
        except (ConnectionResetError, BrokenPipeError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(0.5)


def request(port, body, boundary, cleanup, sid, *, seed=False, defaults=False, serializer="php"):
    settings = f"session.upload_progress.cleanup={cleanup}\nsession.serialize_handler={serializer}"
    if not defaults:
        settings += "\nsession.upload_progress.freq=1\nsession.upload_progress.min_freq=0"
    values = {
        "REQUEST_METHOD": "GET" if seed else "POST",
        "SCRIPT_FILENAME": "/var/www/html/upload.php", "SCRIPT_NAME": "/upload.php",
        "QUERY_STRING": "seed=1" if seed else "", "REQUEST_URI": "/upload.php",
        "SERVER_PROTOCOL": "HTTP/1.1", "GATEWAY_INTERFACE": "CGI/1.1",
        "SERVER_NAME": "localhost", "SERVER_PORT": "80", "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_TYPE": f"multipart/form-data; boundary={boundary}",
        "CONTENT_LENGTH": 0 if seed else len(body),
        "HTTP_COOKIE": f"PHPSESSID={sid}", "PHP_VALUE": settings,
    }
    with socket.create_connection(("127.0.0.1", port), timeout=20) as connection:
        connection.sendall(record(1, struct.pack("!HB5x", 1, 0)))
        connection.sendall(record(4, params(values)) + record(4))
        if not seed:
            for start in range(0, len(body), 16384):
                connection.sendall(record(5, body[start:start + 16384]))
        connection.sendall(record(5))
        stdout, stderr = bytearray(), bytearray()
        while True:
            version, kind, _, length, padding, _ = struct.unpack("!BBHHBB", read_exact(connection, 8))
            if version != 1:
                raise RuntimeError("invalid FastCGI version")
            data = read_exact(connection, length)
            read_exact(connection, padding)
            if kind == 6:
                stdout.extend(data)
            elif kind == 7:
                stderr.extend(data)
            elif kind == 3:
                app_status, protocol_status = struct.unpack("!IB3x", data)
                if app_status or protocol_status:
                    raise RuntimeError(f"FastCGI request failed: {app_status}/{protocol_status}")
                break
    response = bytes(stdout).split(b"\r\n\r\n", 1)
    if len(response) != 2:
        raise RuntimeError(f"invalid FPM response: {stdout!r}; {stderr!r}")
    try:
        return json.loads(response[1])
    except ValueError as error:
        raise RuntimeError(f"non-JSON FPM response: {stdout!r}; {stderr!r}") from error


def multipart():
    boundary = "phpup-benign-regression"
    body = f"--{boundary}\r\nContent-Disposition: form-data; name=\"PHP_SESSION_UPLOAD_PROGRESS\"\r\n\r\ntest\r\n".encode()
    for name, size in (("first", 131072), ("second", 31)):
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{name}.txt\"\r\nContent-Type: text/plain\r\n\r\n".encode()
        body += b"x" * size + b"\r\n"
    # Force more request reads after FILE_END, before the final progress update.
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"after_files\"\r\n\r\n".encode()
    body += b"y" * 131072 + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return body, boundary


def smoke(cli_image, fpm_image, version, final_counter=False, module=None):
    mounts = []
    if module:
        mounts = ["-v", f"{Path(module).resolve()}:/override/session.so:ro"]
    php_options = ["-n", "-d", "extension=/override/session.so"] if module else []
    actual = docker("run", "--rm", *mounts, cli_image, *php_options, "-r", "echo PHP_VERSION;")
    assert actual == version, (actual, version)
    enabled = json.loads(docker("run", "--rm", *mounts, cli_image, *php_options, "-r", "echo json_encode(get_loaded_extensions());"))
    assert {"session", "filter", "tokenizer", "json"}.issubset(set(enabled)), enabled
    assert "session" not in docker("run", "--rm", cli_image, "-n", "-m").splitlines()
    fixtures = Path(__file__).resolve().parent / "fixtures"
    fpm_options = ["-n", "-d", "extension=/override/session.so"] if module else []
    container = docker("run", "--rm", "-d", "-p", "127.0.0.1::9000", "-v", f"{fixtures}:/var/www/html:ro", *mounts, fpm_image, *fpm_options)
    results = []
    try:
        port = int(docker("port", container, "9000/tcp").rsplit(":", 1)[1])
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("FPM did not start")
        body, boundary = multipart()
        for defaults, cleanup, serializer in ((True, 1, "php"), (False, 0, "php"), (False, 1, "php"), (False, 0, "php_binary"), (False, 0, "php_serialize")):
            result = robust_request(port, body, boundary, cleanup, uuid.uuid4().hex, defaults=defaults, serializer=serializer)
            assert result["version"] == version, result
            assert result["files"] == {"first": {"size": 131072, "error": 0}, "second": {"size": 31, "error": 0}}, result
            if cleanup:
                assert result["progress"] is None, result
            else:
                progress = result["progress"]
                assert progress["done"] is True, result
                assert [file["bytes_processed"] for file in progress["files"]] == [131072, 31], result
                if final_counter:
                    assert progress["bytes_processed"] == len(body), result
            results.append({"defaults": defaults, "cleanup": cleanup, "serializer": serializer, "progress": result["progress"]})
        sid = uuid.uuid4().hex
        assert robust_request(port, b"", boundary, 0, sid, seed=True)["seeded"]
        cancelled = robust_request(port, body, boundary, 0, sid)
        assert not cancelled["files"] or any(file["error"] == 8 for file in cancelled["files"].values()), cancelled
    finally:
        logs = docker("logs", container)
        docker("stop", container)
    print(json.dumps({"version": version, "cli": cli_image, "fpm": fpm_image, "module": str(module) if module else None, "results": results, "cancellation": "passed", "fpm_logs": logs}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True)
    parser.add_argument("--fpm", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--require-final-counter", action="store_true")
    parser.add_argument("--module", type=Path)
    args = parser.parse_args()
    smoke(args.cli, args.fpm, args.version, args.require_final_counter, args.module)
