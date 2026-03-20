#!/usr/bin/env python3
import os
import json
import glob
import datetime
import sqlite3
import hashlib
from textblob import TextBlob

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
PARTIDOS_PATH = os.path.join(BASE_DIR, "config", "partidos_keywords.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "pipeline.log")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [NLP] {msg}\n")

def load_partidos():
    with open(PARTIDOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def detectar_partidos(texto, partidos_keywords):
    texto_up = texto.upper()
    partidos = []
    for partido, keywords in partidos_keywords.items():
        for kw in keywords:
            if kw.upper() in texto_up:
                partidos.append(partido)
                break
    return partidos

def analizar_sentimiento(texto):
    blob = TextBlob(texto)
    polaridad = blob.sentiment.polarity
    if polaridad > 0:
        return "POS", polaridad, 0, 1 - polaridad
    elif polaridad < 0:
        return "NEG", 0, -polaridad, 1 + polaridad
    else:
        return "NEU", 0, 0, 1

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS noticias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        title TEXT,
        summary TEXT,
        link TEXT,
        published TEXT,
        partidos TEXT,
        sentiment_label TEXT,
        sentiment_pos REAL,
        sentiment_neg REAL,
        sentiment_neu REAL,
        created_at TEXT
    )
    """)
    conn.commit()
    return conn

def get_latest_raw_file():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "rss_raw_*.json")))
    return files[-1] if files else None

def process_file(path, partidos_keywords):
    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    conn = init_db()
    c = conn.cursor()
    count = 0

    for e in entries:
        texto = f"{e.get('title','')} {e.get('summary','')}"
        partidos = detectar_partidos(texto, partidos_keywords)
        if not partidos:
            continue

        label, pos, neg, neu = analizar_sentimiento(texto)
        partidos_str = ",".join(partidos)
        now = datetime.datetime.now().isoformat()

        c.execute("""
        INSERT OR IGNORE INTO noticias (
            source, source_type, title, summary, link, published,
            partidos, sentiment_label, sentiment_pos,
            sentiment_neg, sentiment_neu, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e.get("source",""),
            e.get("source_type",""),
            e.get("title",""),
            e.get("summary",""),
            e.get("link",""),
            e.get("published",""),
            partidos_str,
            label,
            pos,
            neg,
            neu,
            now
        ))
        count += 1

    conn.commit()
    conn.close()
    log(f"Procesadas {count} noticias desde {path}")

if __name__ == "__main__":
    try:
        partidos_keywords = load_partidos()
        latest = get_latest_raw_file()
        if latest:
            log(f"Procesando archivo {latest}")
            process_file(latest, partidos_keywords)
        else:
            log("No hay archivos RAW para procesar")
    except Exception as e:
        log(f"ERROR: {e}")
