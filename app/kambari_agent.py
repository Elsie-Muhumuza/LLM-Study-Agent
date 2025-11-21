# app/kambari_agent.py
"""
Main entry for Kambari Altar Agent.

Provides:
- CLI: create_parables_series, generate_materials, send_thu_reminders, add_member, list_members
- Streamlit UI: preview schedule and click-to-send link for messages
"""

import os
from datetime import date, datetime, timedelta
import json
import textwrap
from pathlib import Path

from . import db
from .question_generator import generate_questions
import sqlite3
import urllib.parse

# Optional Streamlit import (only used when launching UI)
try:
    import streamlit as st
except Exception:
    st = None

# Built-in parables catalog file path (also included in repo)
PARABLES_JSON = Path("data/builtin_parables.json")
DB_PATH = Path("kambari.db")

# Admin phone for direct sends if API enabled (we default to click-to-send)
ADMIN_PHONE = os.getenv("ADMIN_PHONE")
WHATSAPP_MODE = os.getenv("WHATSAPP_MODE", "link")  # "link" or "api"
WHATSAPP_BASE_LINK = "https://wa.me/?text="

# -----------------------
# Series & schedule helpers
# -----------------------
def create_parables_series(start_date: date = None, parables: list | None = None):
    if start_date is None:
        start_date = date.today()
    # init DB if needed
    db.init_db()
    # create series
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO series (name, kind, description, created_at) VALUES (?, 'parables', ?, ?)",
                ("Parables of Jesus", "Parables series", datetime.utcnow().isoformat()))
    series_id = cur.lastrowid

    # Load builtin parables if not passed
    if parables is None:
        if PARABLES_JSON.exists():
            with open(PARABLES_JSON, "r", encoding="utf-8") as fh:
                parables = json.load(fh)
        else:
            # Minimal built-in fallback
            parables = [
                {"title":"Parable of the Sower","reference":"Matt 13:1-23","theme":"Kingdom growth"},
                {"title":"Parable of the Mustard Seed","reference":"Matt 13:31-32","theme":"Kingdom growth"},
                {"title":"Parable of the Lost Sheep","reference":"Luke 15:3-7","theme":"Repentance"}
            ]
    # Insert passages
    for p in parables:
        cur.execute("INSERT INTO passages (series_id, title, reference, theme, notes) VALUES (?, ?, ?, ?, ?)",
                    (series_id, p.get("title"), p.get("reference"), p.get("theme"), p.get("notes","")))
    conn.commit()

    # Build weekly schedule: group by theme then assign sequential Fridays
    cur.execute("SELECT id, title, reference, theme FROM passages WHERE series_id=? ORDER BY theme, id", (series_id,))
    rows = cur.fetchall()
    week_date = start_date
    week_num = 1
    for r in rows:
        pid, title, ref, theme = r
        # ensure schedule on Friday of that week (move to next Friday)
        # if start_date not Friday, find next Friday
        while week_date.weekday() != 4:  # 4 = Friday
            week_date += timedelta(days=1)
        cur.execute("INSERT INTO schedule (series_id, passage_id, week_number, scheduled_date) VALUES (?, ?, ?, ?)",
                    (series_id, pid, week_num, week_date.isoformat()))
        week_num += 1
        week_date += timedelta(weeks=1)
    conn.commit()
    conn.close()
    return series_id

# -----------------------
# Material generation
# -----------------------
def generate_materials():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""SELECT s.id, s.scheduled_date, p.title, p.reference
                   FROM schedule s JOIN passages p ON s.passage_id = p.id
                   ORDER BY s.scheduled_date""")
    rows = cur.fetchall()
    created = 0
    for sched_id, sched_iso, title, ref in rows:
        questions = generate_questions(title, ref)
        # join to a single content blob for storage
        question_text = "\n\n".join(questions)
        w_text = f"*Kambari Altar — Study Questions ({sched_iso[:10]})*\n\n{question_text}\n\n🎯 *Take-home challenge:* Apply one small action this week and share next Friday."
        cur.execute("INSERT INTO generated_materials (schedule_id, role, content, created_at) VALUES (?, 'wednesday_questions', ?, ?)",
                    (sched_id, w_text, datetime.utcnow().isoformat()))
        # friday minutes template
        fm = textwrap.dedent(f"""\
            *Kambari Altar — Meeting Minutes Template ({sched_iso[:10]})*
            Topic: *{title}* ({ref})

            Summary:
            (Leader: paste a 3–5 line summary here.)

            Key points / insights:
            - 

            Take-home challenge feedback:
            - 

            Prayer points:
            - 

            Thank you message:
            Thanks everyone — we prayed, shared, and grew. Blessings! ☕️😊
        """)
        cur.execute("INSERT INTO generated_materials (schedule_id, role, content, created_at) VALUES (?, 'friday_minutes', ?, ?)",
                    (sched_id, fm, datetime.utcnow().isoformat()))
        created += 2
    conn.commit(); conn.close()
    return created

# -----------------------
# WhatsApp helpers (click-to-send)
# -----------------------
def whatsapp_prefill_link(text: str) -> str:
    # make safe for URL
    encoded = urllib.parse.quote(text)
    return WHATSAPP_BASE_LINK + encoded

# -----------------------
# CLI & small Streamlit UI
# -----------------------
def cli():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("init")
    sub.add_parser("create_parables_series")
    sub.add_parser("generate_materials")
    sub.add_parser("list_schedule")
    sub.add_parser("list_members")
    am = sub.add_parser("add_member"); am.add_argument("--name", required=True); am.add_argument("--phone", default=""); am.add_argument("--pref", default="")
    sendth = sub.add_parser("send_thu"); sendth.add_argument("--date", required=True, help="YYYY-MM-DD date of the Friday session")
    args = parser.parse_args()
    if args.cmd == "init":
        # optional preload of your confirmed list
        preload = [
            ("Alvin","+2567...","Alvin"),
            ("Horace of God","+2567...","Horace"),
            ("Roy","+2567...","Roy"),
            # NOTE: replace +2567... with real numbers or add via add_member CLI
        ]
        db.init_db(preload_members=preload)
        print("Initialized DB with preload (edit phone numbers as needed).")
    elif args.cmd == "create_parables_series":
        create_parables_series()
        print("Created parables series and schedule.")
    elif args.cmd == "generate_materials":
        c = generate_materials()
        print("Generated materials:", c)
    elif args.cmd == "list_schedule":
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("""SELECT sch.id, p.title, sch.scheduled_date FROM schedule sch JOIN passages p ON sch.passage_id=p.id ORDER BY sch.scheduled_date""")
        for r in cur.fetchall(): print(r)
        conn.close()
    elif args.cmd == "list_members":
        for m in db.list_members(): print(m)
    elif args.cmd == "add_member":
        db.add_member(args.name, args.phone, args.pref)
        print("Added member.")
    elif args.cmd == "send_thu":
        # finds the schedule for that date and prints click-to-send links for each member
        target = datetime.fromisoformat(args.date).date()
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT s.id, p.title, p.reference FROM schedule s JOIN passages p ON s.passage_id=p.id WHERE s.scheduled_date=?", (target.isoformat(),))
        r = cur.fetchone()
        if not r:
            print("No session on that date.")
            return
        sched_id, title, ref = r
        content = f"🌿 Hi! Quick reminder from Kambari Altar — our fellowship is on Friday at 6:00 AM. This week: *{title}* ({ref}). We’d love to have you — see you Friday! ❤️ — Elsie"
        # Print click-to-send link for admin to copy and share individually on WhatsApp
        link = whatsapp_prefill_link(content)
        print("Click-to-send WhatsApp link (open on mobile):", link)
    else:
        parser.print_help()

# Streamlit UI (very small preview)
def run_streamlit():
    if st is None:
        print("Streamlit not installed. Install with `pip install streamlit`.")
        return
    st.title("Kambari Altar — Schedule Preview")
    password = st.secrets.get("APP_PASSWORD") if st.secrets else os.getenv("APP_PASSWORD")
    if not password:
        st.warning("APP_PASSWORD not set. Set via Streamlit secrets or env var to protect the UI.")
    typed = st.text_input("Password (to unlock)", type="password")
    if typed != password:
        st.stop()
    st.success("Unlocked")
    # show schedule
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute("""SELECT sch.id, p.title, sch.scheduled_date FROM schedule sch JOIN passages p ON sch.passage_id=p.id ORDER BY sch.scheduled_date""")
    rows = cur.fetchall()
    for rid, title, sched in rows:
        st.subheader(f"{sched} — {title}")
        # fetch generated wednesday questions or generate on demand
        cur.execute("SELECT content FROM generated_materials WHERE schedule_id=? AND role='wednesday_questions' ORDER BY created_at DESC LIMIT 1", (rid,))
        gm = cur.fetchone()
        content = gm[0] if gm else "(No questions generated yet)"
        st.text_area("WED Questions", value=content, height=300)
        # click-to-send
        link = whatsapp_prefill_link(content)
        st.markdown(f"[Send to my phone (open on mobile)]({link})")
    conn.close()

if __name__ == "__main__":
    # If first arg is "ui" run streamlit style; else CLI
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "ui":
        run_streamlit()
    else:
        cli()
