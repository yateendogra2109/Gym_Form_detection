from __future__ import annotations

import sqlite3
from pathlib import Path


class SessionLogger:
    def __init__(self, db_path: str = "gymcv.db") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rep_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                exercise TEXT NOT NULL,
                rep_index INTEGER NOT NULL,
                form_score REAL NOT NULL,
                asymmetry_score REAL,
                fatigue_flag INTEGER NOT NULL,
                rom REAL,
                velocity REAL,
                xp_gained INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS session_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                exercise TEXT NOT NULL,
                reps INTEGER NOT NULL,
                avg_form_score REAL NOT NULL,
                avg_asymmetry_score REAL,
                fatigue_events INTEGER NOT NULL,
                total_xp INTEGER NOT NULL
            )
            """
        )
        self.conn.commit()

    def log_rep(
        self,
        exercise: str,
        rep_index: int,
        form_score: float,
        asymmetry_score: float | None,
        fatigue_flag: bool,
        rom: float,
        velocity: float,
        xp_gained: int,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO rep_events (exercise, rep_index, form_score, asymmetry_score, fatigue_flag, rom, velocity, xp_gained)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (exercise, rep_index, form_score, asymmetry_score, int(fatigue_flag), rom, velocity, xp_gained),
        )
        self.conn.commit()

    def log_session(
        self,
        exercise: str,
        reps: int,
        avg_form_score: float,
        avg_asymmetry_score: float | None,
        fatigue_events: int,
        total_xp: int,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO session_summary (exercise, reps, avg_form_score, avg_asymmetry_score, fatigue_events, total_xp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (exercise, reps, avg_form_score, avg_asymmetry_score, fatigue_events, total_xp),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

