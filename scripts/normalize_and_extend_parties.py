#!/usr/bin/env python3
import sqlite3
import hashlib
import os

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")

# PARTIDOS cargado desde config/politica_config.json
import json as _json_partidos
PARTIDOS = _json_partidos.load(open(
    os.path.join(BASE_DIR, "config", "politica_config.json"), encoding="utf-8"
))["partidos"]


conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Crear tabla normalizada
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

def detectar_partidos(texto):
    texto = texto.lower()
    encontrados = []
    for partido, keywords in PARTIDOS.items():
        for kw in keywords:
            if kw.lower() in texto:
                encontrados.append(partido)
                break
    return list(set(encontrados))

for row in rows:
    data = dict(zip(cols, row))
    texto = f"{data.get('title','')} {data.get('summary','')}"
    partidos_detectados = detectar_partidos(texto)

    if not partidos_detectados:
        continue

    for p in partidos_detectados:
        c.execute("""
            INSERT OR IGNORE INTO noticias_norm (
                source, source_type, title, summary, link, published,
                partido, sentiment_label, sentiment_polarity,
                created_at, ingest_date, hash_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("source"),
            data.get("source_type"),
            data.get("title"),
            data.get("summary"),
            data.get("link"),
            data.get("published"),
            p,
            data.get("sentiment_label"),
            data.get("sentiment_polarity"),
            data.get("created_at"),
            data.get("ingest_date"),
            hashlib.md5(
                f"{data.get('source','')}|{data.get('title','')}|{p}|{data.get('published','')}".encode()
            ).hexdigest()
        ))

conn.commit()
conn.close()

print("Normalización completada. Tabla 'noticias_norm' creada con partidos individuales y SALF incluido.")
