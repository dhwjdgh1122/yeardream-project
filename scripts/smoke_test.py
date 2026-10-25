"""Check documented Uvicorn startup using only local requests and stdlib."""

import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def run():
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    command = [sys.executable, '-B', '-m', 'uvicorn', 'backend.app.main:app',
               '--host', '127.0.0.1', '--port', str(port)]
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic() + 15
            while True:
                try:
                    with urlopen(base + '/api/health', timeout=1) as response:
                        assert json.load(response) == {'status': 'ok'}
                    break
                except (URLError, TimeoutError):
                    if process.poll() is not None or time.monotonic() >= deadline:
                        log.seek(0)
                        raise RuntimeError('Uvicorn startup failed:\n' + log.read().decode('utf-8', errors='replace'))
                    time.sleep(0.1)
            with urlopen(base, timeout=3) as response:
                assert 'JSON 다운로드' in response.read().decode('utf-8')
            with urlopen(base + '/openapi.json', timeout=3) as response:
                schema = json.load(response)
                assert '/api/analyze' in schema['paths']
            # Invalid input must fail before collection or result-file writes.
            request = Request(base + '/api/analyze', method='POST',
                              data=b'{"url":"http://127.0.0.1","collection_mode":"invalid"}',
                              headers={'Content-Type': 'application/json'})
            try:
                with urlopen(request, timeout=3):
                    raise AssertionError('Invalid collection mode was accepted')
            except HTTPError as error:
                assert error.code == 422
            print('Startup checks passed: Uvicorn CLI, health, UI, OpenAPI, input validation; local requests only')
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == '__main__':
    run()
