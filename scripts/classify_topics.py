#!/usr/bin/env python3
import sqlite3
import re
import os
import datetime

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "pipeline.log")

def log(msg):
    ts = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [TOPICS] {msg}\n")

# TEMAS cargado desde config/politica_config.json
import json as _json_topics
TOPICS = _json_topics.load(open(
    os.path.join(BASE_DIR, "config", "politica_config.json"), encoding="utf-8"
))["temas"]


def classify(text):
    text = text.lower()
    detected = []

    for topic, keywords in TOPICS.items():
        for kw in keywords:
            if kw in text:
                detected.append(topic)
                break

    if not detected:
        return "otros"

    return ",".join(detected)

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Añadir columna si no existe
    try:
        c.execute("ALTER TABLE noticias_norm ADD COLUMN temas TEXT")
        log("Columna 'temas' añadida a noticias_norm")
    except:
        pass  # ya existe

    c.execute("SELECT id, title, summary FROM noticias_norm")
    rows = c.fetchall()

    for _id, title, summary in rows:
        text = f"{title} {summary}"
        temas = classify(text)
        c.execute("UPDATE noticias_norm SET temas = ? WHERE id = ?", (temas, _id))

    conn.commit()
    conn.close()
    log(f"Clasificación temática completada para {len(rows)} noticias")

if __name__ == "__main__":
    main()
