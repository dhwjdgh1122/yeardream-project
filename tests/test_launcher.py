import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

import run_app
from backend.app import paths


def test_frozen_output_is_beside_executable(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'YearDream.exe'))
    assert paths.output_root() == tmp_path
    assert paths.resource_root() == Path(paths.__file__).resolve().parents[2]


def test_source_output_ignores_working_directory(monkeypatch, tmp_path):
    monkeypatch.delattr(sys, 'frozen', raising=False)
    monkeypatch.chdir(tmp_path)
    assert paths.output_root() == paths.resource_root()


def test_browser_opens_after_startup(monkeypatch):
    addresses = []
    monkeypatch.setattr(run_app.webbrowser, 'open', addresses.append)
    run_app.open_when_ready(SimpleNamespace(started=True), 'http://127.0.0.1:1234', threading.Event())
    assert addresses == ['http://127.0.0.1:1234']
    stopped = threading.Event()
    stopped.set()
    run_app.open_when_ready(SimpleNamespace(started=True), 'unused', stopped)
    assert len(addresses) == 1


@pytest.mark.parametrize('port', ['-1', '65536'])
def test_invalid_port_rejected(port):
    with pytest.raises(SystemExit) as error:
        run_app.run(['--port', port, '--no-browser'])
    assert error.value.code == 2


def test_launcher_reserves_loopback_and_reports_output(monkeypatch, tmp_path):
    monkeypatch.setattr(run_app, 'output_root', lambda: tmp_path)
    observed = []
    class Server:
        def __init__(self, config):
            assert config.host == '127.0.0.1' and config.workers == 1
        def run(self, sockets):
            observed.append(sockets[0].getsockname())
    monkeypatch.setattr(run_app.uvicorn, 'Server', Server)
    assert run_app.run(['--port', '0', '--no-browser']) == 0
    assert observed[0][0] == '127.0.0.1' and observed[0][1] > 0


def test_write_permission_failure_is_reported(monkeypatch, tmp_path):
    monkeypatch.setattr(run_app, 'output_root', lambda: tmp_path / 'missing')
    assert run_app.run(['--port', '0', '--no-browser']) == 1
