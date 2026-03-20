#!/usr/bin/env python3
import sqlite3
import os
import datetime

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")

RETENTION_DAYS = 365  # 1 año

def main():
    if not os.path.exists(DB_PATH):
        print("DB no existe.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    limite = (datetime.date.today() - datetime.timedelta(days=RETENTION_DAYS)).isoformat()
    c.execute("DELETE FROM noticias_norm WHERE ingest_date < ?", (limite,))
    borradas = c.rowcount
    conn.commit()
    conn.close()

    print(f"Eliminadas {borradas} noticias anteriores a {limite}")

if __name__ == "__main__":
    main()
