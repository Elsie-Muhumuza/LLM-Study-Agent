# app/db.py
"""Database helpers for Kambari Altar agent (sqlite)."""

import sqlite3
from pathlib import Path

DB_PATH = Path("kambari.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    preferred_name TEXT
);

CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    kind TEXT,
    description TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS passages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER,
    title TEXT,
    reference TEXT,
    theme TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER,
    passage_id INTEGER,
    week_number INTEGER,
    scheduled_date TEXT
);

CREATE TABLE IF NOT EXISTS generated_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER,
    role TEXT,
    content TEXT,
    sent_to_admin INTEGER DEFAULT 0,
    created_at TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db(preload_members: list | None = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    if preload_members:
        for name, phone, pref in preload_members:
            cur.execute("INSERT INTO members (name, phone, preferred_name) VALUES (?, ?, ?)",
                        (name, phone, pref))
        conn.commit()
    conn.close()

def list_members():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, preferred_name, phone FROM members ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_member(name: str, phone: str = "", preferred_name: str | None = None):
    pref = preferred_name or (name.split()[0] if name else "")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO members (name, phone, preferred_name) VALUES (?, ?, ?)", (name, phone, pref))
    conn.commit()
    conn.close()
