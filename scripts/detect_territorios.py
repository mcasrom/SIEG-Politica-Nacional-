#!/usr/bin/env python3
import sqlite3
import os
import re

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")

# Territorios + coordenadas
TERRITORIOS = {
    "Andalucía": (37.5443, -4.7278),
    "Aragón": (41.5976, -0.9057),
    "Asturias": (43.3614, -5.8593),
    "Baleares": (39.6953, 3.0176),
    "Canarias": (28.2916, -16.6291),
    "Cantabria": (43.1828, -3.9878),
    "Castilla y León": (41.8357, -4.3976),
    "Castilla-La Mancha": (39.2796, -3.0977),
    "Cataluña": (41.5912, 1.5209),
    "Comunidad Valenciana": (39.4699, -0.3763),
    "Extremadura": (39.4937, -6.0679),
    "Galicia": (42.7551, -7.8662),
    "La Rioja": (42.2871, -2.5396),
    "Madrid": (40.4168, -3.7038),
    "Murcia": (37.9922, -1.1307),
    "Navarra": (42.6954, -1.6761),
    "País Vasco": (43.0380, -2.6190),
    "Ceuta": (35.8894, -5.3213),
    "Melilla": (35.2923, -2.9381),

    "Girona": (41.9794, 2.8214),
    "Gerona": (41.9794, 2.8214),
    "Lleida": (41.6176, 0.6200),
    "Lérida": (41.6176, 0.6200),
    "Tarragona": (41.1189, 1.2445),
    "Barcelona": (41.3874, 2.1686),

    "Zaragoza": (41.6488, -0.8891),
    "Huesca": (42.1401, -0.4089),
    "Teruel": (40.3456, -1.1065),

    "Valladolid": (41.6523, -4.7245),
    "León": (42.5987, -5.5671),
    "Burgos": (42.3439, -3.6969),
    "Salamanca": (40.9701, -5.6635),
    "Segovia": (40.9429, -4.1088),
    "Ávila": (40.6565, -4.6815),
    "Soria": (41.7662, -2.4790),
    "Palencia": (42.0095, -4.5241),
    "Zamora": (41.5034, -5.7446),

    "Logroño": (42.4667, -2.45),
    "Pamplona": (42.8125, -1.6458),
    "Bilbao": (43.2630, -2.9350),
    "San Sebastián": (43.3183, -1.9812),
    "Vitoria": (42.8467, -2.6727),

    "A Coruña": (43.3623, -8.4115),
    "Lugo": (43.0120, -7.5559),
    "Ourense": (42.3358, -7.8639),
    "Pontevedra": (42.4310, -8.6444),

    "Sevilla": (37.3891, -5.9845),
    "Málaga": (36.7213, -4.4214),
    "Córdoba": (37.8882, -4.7794),
    "Granada": (37.1773, -3.5986),
    "Jaén": (37.7796, -3.7849),
    "Huelva": (37.2614, -6.9447),
    "Cádiz": (36.5271, -6.2886),
    "Almería": (36.8340, -2.4637),

    "Valencia": (39.4699, -0.3763),
    "Alicante": (38.3452, -0.4810),
    "Castellón": (39.9864, -0.0513),

    "Toledo": (39.8628, -4.0273),
    "Ciudad Real": (38.9863, -3.9291),
    "Cuenca": (40.0704, -2.1374),
    "Guadalajara": (40.6333, -3.1667),
    "Albacete": (38.9943, -1.8585)
}

def detectar_territorio(texto):
    texto = texto.lower()
    for t in TERRITORIOS.keys():
        if t.lower() in texto:
            return t
    return None

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Añadir columnas si no existen
c.execute("PRAGMA table_info(noticias_norm)")
cols = [col[1] for col in c.fetchall()]

if "territorio" not in cols:
    c.execute("ALTER TABLE noticias_norm ADD COLUMN territorio TEXT")

if "lat" not in cols:
    c.execute("ALTER TABLE noticias_norm ADD COLUMN lat REAL")

if "lon" not in cols:
    c.execute("ALTER TABLE noticias_norm ADD COLUMN lon REAL")

# Procesar noticias
rows = c.execute("SELECT id, title, summary FROM noticias_norm").fetchall()

for row in rows:
    id_, title, summary = row
    texto = f"{title} {summary}"
    territorio = detectar_territorio(texto)

    if territorio:
        lat, lon = TERRITORIOS[territorio]
        c.execute("UPDATE noticias_norm SET territorio=?, lat=?, lon=? WHERE id=?", (territorio, lat, lon, id_))

conn.commit()
conn.close()

print("Detección territorial + coordenadas completada.")
