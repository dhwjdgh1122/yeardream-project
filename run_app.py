"""Console launcher shared by source runs and the Windows executable."""

import argparse
import multiprocessing
import socket
import tempfile
import threading
import webbrowser

import uvicorn

from backend.app.main import app
from backend.app.paths import output_root


def open_when_ready(server, address, stopped):
    while not stopped.wait(0.1):
        if server.started:
            webbrowser.open(address)
            return


def run(argv=None):
    parser = argparse.ArgumentParser(description='YearDream local website advertisement analyzer')
    parser.add_argument('--port', type=int, default=8000, help='Local port (default: 8000; 0: automatic)')
    parser.add_argument('--no-browser', action='store_true', help='Do not automatically open the UI')
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    try:
        # Check permissions without changing existing analysis files.
        with tempfile.TemporaryFile(dir=output_root()):
            pass
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            listener.bind(('127.0.0.1', args.port))
            listener.listen(128)
            port = listener.getsockname()[1]
            address = f'http://127.0.0.1:{port}'
            print(f'YearDream: {address}', flush=True)
            print(f'Result files: {output_root()}', flush=True)
            print('Stop: Ctrl+C in this window.', flush=True)
            server = uvicorn.Server(uvicorn.Config(
                app, host='127.0.0.1', port=port, loop='asyncio', http='h11', ws='none',
                workers=1, log_level='info',
            ))
            stopped = threading.Event()
            if not args.no_browser:
                threading.Thread(target=open_when_ready, args=(server, address, stopped), daemon=True).start()
            try:
                server.run(sockets=[listener])
            finally:
                stopped.set()
        return 0
    except OSError as error:
        print(f'Cannot start YearDream: {error}', flush=True)
        print('Check the port and folder write permissions. See the user manual.', flush=True)
        return 1


if __name__ == '__main__':
    multiprocessing.freeze_support()
    raise SystemExit(run())
