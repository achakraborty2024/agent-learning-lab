"""Append-only lesson revisions and externally scored attempts in SQLite."""
import json
import sqlite3
from datetime import datetime, timezone

class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS revisions (
          id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, lesson_id TEXT NOT NULL,
          status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts (
          id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, payload TEXT NOT NULL);
        ''')

    def revision(self, run_id, lesson_id, status, payload):
        with self.db:
            self.db.execute('INSERT INTO revisions(run_id,lesson_id,status,payload,created_at) VALUES (?,?,?,?,?)',
                (run_id, lesson_id, status, json.dumps(payload), datetime.now(timezone.utc).isoformat()))

    def attempt(self, run_id, payload):
        with self.db:
            self.db.execute('INSERT INTO attempts(run_id,payload) VALUES (?,?)', (run_id, json.dumps(payload)))

    def active(self, run_id):
        rows = self.db.execute('''SELECT lesson_id,status,payload FROM revisions WHERE id IN
            (SELECT MAX(id) FROM revisions WHERE run_id=? GROUP BY lesson_id) ORDER BY id''', (run_id,))
        return [dict(json.loads(payload), lesson_id=lid) for lid, status, payload in rows if status == 'promoted']

    def close(self):
        self.db.close()
