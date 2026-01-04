import sqlite3
import json
from datetime import datetime

DB_PATH = "meals.db"

# -----------------------------
# Meal Data
# -----------------------------
def fetch_meals():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, category, ingredients, notes FROM meals")
    rows = cursor.fetchall()
    conn.close()
    return rows


# -----------------------------
# Saved Plans
# -----------------------------
def save_weekly_plan(name, weekly_plan):
    from meal_logic import serialize_weekly_plan

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT,
            plan_json TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO saved_plans (name, created_at, plan_json)
        VALUES (?, ?, ?)
    """, (name, datetime.now().isoformat(), json.dumps(serialize_weekly_plan(weekly_plan))))
    conn.commit()
    conn.close()


def fetch_saved_plans():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at, plan_json FROM saved_plans ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
