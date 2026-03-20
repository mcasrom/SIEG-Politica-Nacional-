#!/usr/bin/env python3
import sqlite3
import os
import re

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")

PARTIDOS = ["PP", "PSOE", "VOX", "SUMAR", "PODEMOS", "ERC", "JUNTS", "PNV", "BILDU", "CS"]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Añadir columna si no existe
c.execute("PRAGMA table_info(noticias_norm)")
cols = [col[1] for col in c.fetchall()]
if "partidos_detectados" not in cols:
    c.execute("ALTER TABLE noticias_norm ADD COLUMN partidos_detectados TEXT")

rows = c.execute("SELECT id, title, summary FROM noticias_norm").fetchall()

for id_, title, summary in rows:
    texto = f"{title} {summary}".upper()
    encontrados = [p for p in PARTIDOS if p in texto]
    if encontrados:
        c.execute("UPDATE noticias_norm SET partidos_detectados=? WHERE id=?", (",".join(encontrados), id_))

conn.commit()
conn.close()

print("Coocurrencias detectadas.")
