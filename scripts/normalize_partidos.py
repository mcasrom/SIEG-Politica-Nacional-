#!/usr/bin/env python3
import sqlite3
import hashlib
import os

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Crear tabla nueva normalizada
c.execute("""
CREATE TABLE IF NOT EXISTS noticias_norm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    source_type TEXT,
    title TEXT,
    summary TEXT,
    link TEXT,
    published TEXT,
    partido TEXT,
    sentiment_label TEXT,
    sentiment_polarity REAL,
    created_at TEXT,
    ingest_date TEXT,
    hash_id TEXT
);
""")

# Leer todas las noticias
rows = c.execute("SELECT * FROM noticias").fetchall()
cols = [d[0] for d in c.description]

for row in rows:
    data = dict(zip(cols, row))
    partido = (data.get("partido", "") or "").split(",")
    for p in partido:
        p = p.strip()
        if not p:
            continue
        data_copy = data.copy()
        data_copy["partido"] = p
        data_copy["hash_id"] = hashlib.md5(
            f"{data_copy.get('source','')}|{data_copy.get('title','')}|{p}|{data_copy.get('published','')}".encode()
        ).hexdigest()
        placeholders = ",".join("?" * len(data_copy))
        c.execute(
            f"INSERT OR IGNORE INTO noticias_norm ({','.join(data_copy.keys())}) VALUES ({placeholders})",
            list(data_copy.values())
        )

conn.commit()
conn.close()

print("Normalización completada. Tabla 'noticias_norm' creada.")
