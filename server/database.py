# server/database.py

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.getcwd(), "history.db")

def init_db():
    """Создаёт таблицу history, если её нет."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT NOT NULL,
                result TEXT NOT NULL,
                float_mode BOOLEAN NOT NULL,
                ts TEXT NOT NULL
            )
        """)
        conn.commit()

def add_record(expression: str, result: str, float_mode: bool):
    """Добавляет новую запись в таблицу."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        c.execute("""
            INSERT INTO history (expression, result, float_mode, ts)
            VALUES (?, ?, ?, ?)
        """, (expression, result, float_mode, timestamp))
        conn.commit()

def get_all_records():
    """Возвращает ВСЮ историю (список словарей)."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT expression, result, float_mode, ts FROM history ORDER BY id ASC")
        rows = c.fetchall()
        data = []
        for row in rows:
            data.append({
                "expression": row[0],
                "result": row[1],
                "float_mode": bool(row[2]),
                "timestamp": row[3]
            })
        return data
