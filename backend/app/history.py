"""Local analysis snapshots and append-only human review records (schema v1)."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class HistoryStore:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=3)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise sqlite3.DatabaseError('Unsupported history database version')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY, saved_at TEXT NOT NULL, url TEXT NOT NULL,
                    collection_mode TEXT NOT NULL, request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL, response_sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS candidates (
                    analysis_id TEXT NOT NULL REFERENCES analyses(id),
                    id TEXT NOT NULL, kind TEXT NOT NULL, item_json TEXT NOT NULL,
                    PRIMARY KEY(analysis_id, id)
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL, candidate_id TEXT NOT NULL,
                    decision TEXT NOT NULL, reviewer TEXT NOT NULL, reason TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    FOREIGN KEY(analysis_id, candidate_id) REFERENCES candidates(analysis_id, id)
                );
                PRAGMA user_version=1;
            ''')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def save(self, request, response):
        analysis_id = uuid4().hex
        snapshot = json.dumps(response, ensure_ascii=False, sort_keys=True)
        with self.connect() as db:
            db.execute('INSERT INTO analyses VALUES (?, ?, ?, ?, ?, ?, ?)', (
                analysis_id, now(), response['url'], response['collection_mode'],
                json.dumps(request, ensure_ascii=False), snapshot,
                hashlib.sha256(snapshot.encode('utf-8')).hexdigest()))
            for kind, key in [('feature', 'findings'), ('content', 'content_candidates')]:
                for index, item in enumerate(response.get(key, [])):
                    db.execute('INSERT INTO candidates VALUES (?, ?, ?, ?)', (
                        analysis_id, f'{kind}-{index + 1}', kind,
                        json.dumps(item, ensure_ascii=False)))
        return analysis_id

    def list(self, limit=20, offset=0):
        with self.connect() as db:
            total = db.execute('SELECT COUNT(*) FROM analyses').fetchone()[0]
            rows = db.execute('''SELECT a.id, a.saved_at, a.url, a.collection_mode,
                (SELECT COUNT(*) FROM candidates c WHERE c.analysis_id=a.id) AS candidate_count
                FROM analyses a ORDER BY a.saved_at DESC, a.id DESC LIMIT ? OFFSET ?''',
                (limit, offset)).fetchall()
            return {'total': total, 'items': [dict(row) for row in rows]}

    def get(self, analysis_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM analyses WHERE id=?', (analysis_id,)).fetchone()
            if row is None:
                raise KeyError(analysis_id)
            snapshot = row['response_json']
            if hashlib.sha256(snapshot.encode('utf-8')).hexdigest() != row['response_sha256']:
                raise sqlite3.DatabaseError('History snapshot checksum mismatch')
            candidates = []
            for candidate in db.execute('SELECT * FROM candidates WHERE analysis_id=? ORDER BY id',
                                        (analysis_id,)):
                reviews = [dict(review) for review in db.execute('''SELECT id, decision, reviewer,
                    reason, reviewed_at FROM reviews WHERE analysis_id=? AND candidate_id=?
                    ORDER BY id''', (analysis_id, candidate['id']))]
                candidates.append({'id': candidate['id'], 'kind': candidate['kind'],
                                   'item': json.loads(candidate['item_json']), 'reviews': reviews})
            return {'id': analysis_id, 'saved_at': row['saved_at'],
                    'request': json.loads(row['request_json']), 'analysis': json.loads(snapshot),
                    'response_sha256': row['response_sha256'], 'candidates': candidates}

    def review(self, analysis_id, candidate_id, payload):
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM candidates WHERE analysis_id=? AND id=?',
                              (analysis_id, candidate_id)).fetchone():
                raise KeyError(candidate_id)
            record = {**payload, 'reviewed_at': now()}
            cursor = db.execute('''INSERT INTO reviews
                (analysis_id, candidate_id, decision, reviewer, reason, reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (analysis_id, candidate_id, record['decision'], record['reviewer'],
                 record['reason'], record['reviewed_at']))
            return {'id': cursor.lastrowid, **record}
