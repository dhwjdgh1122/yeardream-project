import pytest

from backend.app import main


@pytest.fixture(autouse=True)
def isolate_history_database(monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'history_path', tmp_path / 'history.sqlite3')
    monkeypatch.setattr(main, 'jobs', main.AnalysisJobs())
