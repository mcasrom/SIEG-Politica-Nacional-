#!/usr/bin/env python3
import sqlite3
import os
import re

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")

# Reglas de contexto → territorio
REGLAS = {
    r"\bgovern\b": "Cataluña",
    r"\bgeneralitat\b": "Cataluña",
    r"\bparlament\b": "Cataluña",
    r"\bxunta\b": "Galicia",
    r"\bgobierno vasco\b": "País Vasco",
    r"\bejecutivo madrileño\b": "Madrid",
    r"\basamblea de madrid\b": "Madrid",
    r"\bconsell\b": "Comunidad Valenciana",
    r"\bcabildo\b": "Canarias",
    r"\bjunta\b": "Castilla y León",  # ambigua, pero útil
}

def detectar_por_contexto(texto):
    texto = texto.lower()
    for patron, territorio in REGLAS.items():
        if re.search(patron, texto):
            return territorio
    return None

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

rows = c.execute("SELECT id, title, summary FROM noticias_norm").fetchall()

for id_, title, summary in rows:
    texto = f"{title} {summary}".lower()
    territorio = detectar_por_contexto(texto)
    if territorio:
        c.execute("UPDATE noticias_norm SET territorio=? WHERE id=?", (territorio, id_))

conn.commit()
conn.close()

print("Detección territorial por contexto completada.")
