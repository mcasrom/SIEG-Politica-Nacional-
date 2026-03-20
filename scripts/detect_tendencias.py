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
        f.write(f"[{ts}] [TENDENCIAS] {msg}\n")

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Crear tabla si no existe
    c.execute("""
        CREATE TABLE IF NOT EXISTS tendencias_diarias (
            fecha TEXT,
            tipo TEXT,
            clave TEXT,
            total INTEGER,
            PRIMARY KEY (fecha, tipo, clave)
        )
    """)

    # Limpiar tendencias previas
    c.execute("DELETE FROM tendencias_diarias")

    contadores = {}

    # ---------------------------------------------------------
    # 1) Tendencias por tema
    # ---------------------------------------------------------
    c.execute("""
        SELECT DATE(created_at) AS fecha, temas
        FROM noticias_norm
        WHERE temas IS NOT NULL AND temas != ''
    """)
    rows = c.fetchall()

    for fecha, temas in rows:
        if not fecha:
            continue
        for t in temas.split(","):
            t = t.strip()
            if not t:
                continue
            key = (fecha, "tema", t)
            contadores[key] = contadores.get(key, 0) + 1

    # ---------------------------------------------------------
    # 2) Tendencias por narrativa
    # ---------------------------------------------------------
    c.execute("""
        SELECT DATE(created_at) AS fecha, narrativas
        FROM noticias_norm
        WHERE narrativas IS NOT NULL AND narrativas != ''
    """)
    rows = c.fetchall()

    for fecha, narr in rows:
        if not fecha:
            continue
        for n in narr.split(","):
            n = n.strip()
            if not n or n == "ninguna":
                continue
            key = (fecha, "narrativa", n)
            contadores[key] = contadores.get(key, 0) + 1

    # ---------------------------------------------------------
    # 3) Tendencias por partido
    # ---------------------------------------------------------
    c.execute("""
        SELECT DATE(created_at) AS fecha, partido
        FROM noticias_norm
        WHERE partido IS NOT NULL AND partido != ''
    """)
    rows = c.fetchall()

    for fecha, partido in rows:
        if not fecha:
            continue
        p = partido.strip()
        if not p:
            continue
        key = (fecha, "partido", p)
        contadores[key] = contadores.get(key, 0) + 1

    # ---------------------------------------------------------
    # Guardar resultados
    # ---------------------------------------------------------
    data = [(f, t, k, v) for (f, t, k), v in contadores.items()]

    c.executemany("""
        INSERT OR REPLACE INTO tendencias_diarias (fecha, tipo, clave, total)
        VALUES (?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()

    log(f"Tendencias calculadas: {len(data)} filas")

if __name__ == "__main__":
    main()
