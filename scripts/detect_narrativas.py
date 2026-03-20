#!/usr/bin/env python3
import sqlite3
import os
import datetime

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "pipeline.log")

def log(msg):
    ts = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [NARRATIVAS] {msg}\n")

# NARRATIVAS cargado desde config/politica_config.json
import json as _json_narrativas
NARRATIVAS = _json_narrativas.load(open(
    os.path.join(BASE_DIR, "config", "politica_config.json"), encoding="utf-8"
))["narrativas"]


def detectar_narrativas(texto):
    texto = texto.lower()
    detectadas = []

    for narrativa, keywords in NARRATIVAS.items():
        for kw in keywords:
            if kw in texto:
                detectadas.append(narrativa)
                break

    if not detectadas:
        return "ninguna"

    return ",".join(detectadas)

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Añadir columna si no existe
    try:
        c.execute("ALTER TABLE noticias_norm ADD COLUMN narrativas TEXT")
        log("Columna 'narrativas' añadida a noticias_norm")
    except:
        pass

    c.execute("SELECT id, title, summary FROM noticias_norm")
    rows = c.fetchall()

    for _id, title, summary in rows:
        texto = f"{title} {summary}"
        narr = detectar_narrativas(texto)
        c.execute("UPDATE noticias_norm SET narrativas = ? WHERE id = ?", (narr, _id))

    conn.commit()
    conn.close()
    log(f"Narrativas detectadas en {len(rows)} noticias")

if __name__ == "__main__":
    main()
