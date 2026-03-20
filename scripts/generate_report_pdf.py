#!/usr/bin/env python3
"""
generate_report_pdf.py
SIEG - Centro OSINT · Política Nacional

Genera informe PDF diario con KPIs, valoración de líderes,
narrativas activas, alertas y comparativa CIS vs SIEG.
Usable desde línea de comandos y desde el dashboard Streamlit.

Uso:
    python3 scripts/generate_report_pdf.py
    python3 scripts/generate_report_pdf.py --output /ruta/informe.pdf

Autor : M. Castillo · mybloggingnotes@gmail.com
© 2026 M. Castillo - Todos los derechos reservados
"""

import os
import json
import sqlite3
import argparse
from datetime import datetime, timedelta

import pandas as pd
from fpdf import FPDF

BASE_DIR = os.path.expanduser("~/SIEG-Politica-Nacional")
DB_PATH  = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
CFG_PATH = os.path.join(BASE_DIR, "config", "politica_config.json")
OUT_DIR  = os.path.join(BASE_DIR, "data", "reports")

# ── Colores corporativos SIEG ─────────────────────────────
COLOR_HEADER  = (15,  40,  80)   # azul oscuro
COLOR_ACCENT  = (30,  90, 180)   # azul medio
COLOR_POS     = (44, 160,  44)   # verde
COLOR_NEG     = (214, 39,  40)   # rojo
COLOR_NEU     = (120, 120, 120)  # gris
COLOR_BG      = (245, 247, 252)  # fondo suave
COLOR_LINE    = (200, 210, 230)  # línea divisora
COLOR_TEXT    = (30,  30,  40)   # texto principal
COLOR_MUTED   = (110, 120, 140)  # texto secundario

DEJAVU = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
DEJAVU_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def clean(text):
    """Limpia caracteres no latin-1 para fpdf2."""
    replacements = {
        '–': '-', '-': '-', '->': '->', '<-': '<-',
        '·': '.', '•': '*', '’': "'", '“': '"',
        '”': '"', '‘': "'", 'é': 'e', 'í': 'i',
        'ó': 'o', 'ú': 'u', 'á': 'a', 'à': 'a',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

class SIEGReport(FPDF):

    def __init__(self):
        super().__init__()
        self.add_font('DejaVu',  '', DEJAVU)
        self.add_font('DejaVu',  'B', DEJAVU_B)

    def header(self):
        # Barra superior
        self.set_fill_color(*COLOR_HEADER)
        self.rect(0, 0, 210, 14, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 9)
        self.set_y(4)
        self.cell(0, 6, "SIEG - Centro OSINT · Política Nacional · España", align="C")
        self.set_text_color(*COLOR_TEXT)
        self.ln(12)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*COLOR_LINE)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 8,
            f"© 2026 M. Castillo · mybloggingnotes@gmail.com · "
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
            f"Pág. {self.page_no()}",
            align="C"
        )

    def section_title(self, title):
        self.ln(4)
        self.set_fill_color(*COLOR_BG)
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.5)
        self.rect(10, self.get_y(), 190, 9, "FD")
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*COLOR_ACCENT)
        self.set_x(13)
        self.cell(0, 9, title)
        self.set_text_color(*COLOR_TEXT)
        self.ln(10)

    def kpi_box(self, x, y, w, h, label, value, delta="", color=None):
        color = color or COLOR_ACCENT
        self.set_fill_color(*COLOR_BG)
        self.set_draw_color(*COLOR_LINE)
        self.rect(x, y, w, h, "FD")
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*COLOR_MUTED)
        self.set_xy(x + 2, y + 2)
        self.cell(w - 4, 4, label.upper())
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(*color)
        self.set_xy(x + 2, y + 6)
        self.cell(w - 4, 8, str(value), align="C")
        if delta:
            self.set_font("DejaVu", "", 7)
            self.set_text_color(*COLOR_MUTED)
            self.set_xy(x + 2, y + 14)
            self.cell(w - 4, 4, delta, align="C")

    def bar_h(self, x, y, w_total, value, max_val, color, height=4):
        """Barra horizontal proporcional."""
        self.set_fill_color(220, 225, 235)
        self.rect(x, y, w_total, height, "F")
        bar_w = max(1, int((value / max_val) * w_total)) if max_val > 0 else 0
        self.set_fill_color(*color)
        self.rect(x, y, bar_w, height, "F")

    def sentiment_bar(self, x, y, w, sent_score):
        """Barra de sentimiento centrada en 0."""
        mid = x + w // 2
        # Fondo
        self.set_fill_color(220, 225, 235)
        self.rect(x, y, w, 3, "F")
        # Barra desde centro
        bar_w = int(abs(sent_score) * (w // 2))
        if sent_score >= 0:
            self.set_fill_color(*COLOR_POS)
            self.rect(mid, y, bar_w, 3, "F")
        else:
            self.set_fill_color(*COLOR_NEG)
            self.rect(mid - bar_w, y, bar_w, 3, "F")
        # Línea central
        self.set_draw_color(*COLOR_MUTED)
        self.set_line_width(0.3)
        self.line(mid, y, mid, y + 3)


def load_data():
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query("SELECT * FROM noticias_norm", conn)
    df_t = pd.read_sql_query("SELECT * FROM tendencias_diarias", conn)
    conn.close()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["fecha"]      = df["created_at"].dt.date
    return df, df_t

def load_config():
    with open(CFG_PATH, encoding="utf-8") as f:
        return json.load(f)

def generate(output_path=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = os.path.join(OUT_DIR, f"sieg_informe_{ts}.pdf")

    df, df_t = load_data()
    cfg      = load_config()
    lideres  = cfg.get("lideres", {})
    cis_data = cfg.get("cis_valoracion", {})

    hoy     = df["fecha"].max()
    df_hoy  = df[df["fecha"] == hoy]
    map_s   = {"POS": 1, "NEU": 0, "NEG": -1}
    df["sent_score"] = df["sentiment_label"].map(map_s)

    pdf = SIEGReport()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(10, 16, 10)

    # ── PORTADA ───────────────────────────────────────────
    pdf.add_page()

    # Bloque título
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.rect(0, 20, 210, 60, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 22)
    pdf.set_xy(10, 30)
    pdf.cell(0, 12, "SIEG - Centro OSINT", align="C")
    pdf.ln(13)
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Política Nacional · España", align="C")
    pdf.ln(11)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, "Informe de Inteligencia Narrativa", align="C")

    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_xy(10, 88)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(0, 6, f"Fecha: {datetime.now().strftime('%d de %B de %Y')}", align="C")
    pdf.ln(7)
    pdf.cell(0, 6, f"Período analizado: {df['fecha'].min()} -> {hoy}", align="C")
    pdf.ln(7)
    pdf.cell(0, 6, f"Total noticias: {len(df):,} · Fuentes: {df['source'].nunique()} · Partidos: {df['partido'].nunique()}", align="C")

    # Línea separadora
    pdf.set_draw_color(*COLOR_LINE)
    pdf.set_line_width(0.5)
    pdf.line(30, 115, 180, 115)

    pdf.set_xy(10, 118)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.multi_cell(0, 5,
        "Este informe es generado automáticamente por el Sistema de Inteligencia y "
        "Evaluación Geopolítica (SIEG). Los indicadores son estadísticos y aproximados. "
        "No evalúa la veracidad de noticias individuales.",
        align="C"
    )

    # ── PÁGINA 1: KPIs + ALERTAS ──────────────────────────
    pdf.add_page()
    pdf.section_title("1. Indicadores Clave del Período")

    # KPIs en grid 3x2
    sent_medio  = df["sent_score"].mean()
    pct_neg     = (df["sentiment_label"] == "NEG").mean() * 100
    dias        = df["fecha"].nunique()
    sent_color  = COLOR_POS if sent_medio > 0.1 else (COLOR_NEG if sent_medio < -0.1 else COLOR_NEU)

    y0 = pdf.get_y()
    pdf.kpi_box(10,  y0, 60, 22, "Noticias analizadas", f"{len(df):,}")
    pdf.kpi_box(75,  y0, 60, 22, "Partidos detectados", df["partido"].nunique())
    pdf.kpi_box(140, y0, 60, 22, "Fuentes activas", df["source"].nunique())
    pdf.set_y(y0 + 25)
    y1 = pdf.get_y()
    pdf.kpi_box(10,  y1, 60, 22, "Días cubiertos", dias)
    pdf.kpi_box(75,  y1, 60, 22, "Sentimiento medio", f"{sent_medio:+.2f}", "escala -1 a +1", sent_color)
    pdf.kpi_box(140, y1, 60, 22, "% Negativo", f"{pct_neg:.1f}%", "", COLOR_NEG if pct_neg > 15 else COLOR_NEU)
    pdf.set_y(y1 + 28)

    # Alertas
    pdf.section_title("2. Alertas de Actividad por Partido")
    fechas = sorted(df["fecha"].unique())

    if len(fechas) >= 2:
        ultimo   = fechas[-1]
        anterior = fechas[:-1]
        df_hoy2  = df[df["fecha"] == ultimo]
        df_ant   = df[df["fecha"].isin(anterior)]

        for partido in sorted(df["partido"].unique()):
            dh = df_hoy2[df_hoy2["partido"] == partido]
            da = df_ant[df_ant["partido"] == partido]
            if len(dh) == 0:
                continue
            pn_hoy = (dh["sentiment_label"] == "NEG").mean() * 100
            if len(da) > 0:
                pn_ant = da.groupby("fecha").apply(
                    lambda x: (x["sentiment_label"] == "NEG").mean() * 100
                ).mean()
                delta = pn_hoy - pn_ant
            else:
                delta = 0

            if delta > 10:
                icon, color = "^ ALERTA", COLOR_NEG
            elif delta > 4:
                icon, color = "~ Moderado", (255, 140, 0)
            elif delta < -10:
                icon, color = "v Mejora", COLOR_POS
            else:
                icon, color = "- Estable", COLOR_NEU

            pdf.set_font("DejaVu", "B", 8)
            pdf.set_text_color(*color)
            pdf.set_x(13)
            pdf.cell(25, 5, icon)
            pdf.set_font("DejaVu", "", 8)
            pdf.set_text_color(*COLOR_TEXT)
            lider = lideres.get(partido, {}).get("lider", "-")
            pdf.cell(0, 5,
                f"{partido} ({lider}) - neg. hoy: {pn_hoy:.1f}% · delta: {delta:+.1f}pp · {len(dh)} noticias")
            pdf.ln(6)

    # ── PÁGINA 2: VALORACIÓN LÍDERES ─────────────────────
    pdf.add_page(orientation="L")
    pdf.section_title("3. Valoración Mediática de Líderes")
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(0, 5, "Sentimiento medio de cobertura · escala -1 (negativo) a +1 (positivo) · mín. 10 noticias para fiabilidad")
    pdf.ln(7)

    ranking = []
    for partido, grupo in df.groupby("partido"):
        sent = grupo["sent_score"].mean()
        n    = len(grupo)
        lider = lideres.get(partido, {}).get("lider", "-")
        ranking.append((partido, lider, sent, n))
    ranking.sort(key=lambda x: -x[2])

    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(40, 5, "PARTIDO")
    pdf.cell(55, 5, "LÍDER")
    pdf.cell(20, 5, "SCORE", align="R")
    pdf.cell(10, 5, "")
    pdf.cell(60, 5, "BARRA SENTIMIENTO")
    pdf.cell(15, 5, "NOTS", align="R")
    pdf.ln(6)
    pdf.set_draw_color(*COLOR_LINE)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    for partido, lider, sent, n in ranking:
        fiable = n >= 10
        color  = COLOR_POS if sent > 0.1 else (COLOR_NEG if sent < -0.1 else COLOR_NEU)
        pdf.set_font("DejaVu", "B" if fiable else "", 8)
        pdf.set_text_color(*color)
        pdf.set_x(10)
        pdf.cell(40, 5, partido[:18])
        pdf.set_text_color(*COLOR_TEXT)
        pdf.set_font("DejaVu", "", 8)
        pdf.cell(55, 5, lider[:28])
        pdf.set_font("DejaVu", "B", 8)
        pdf.set_text_color(*color)
        pdf.cell(20, 5, f"{sent:+.3f}", align="R")
        pdf.cell(5, 5, "")
        y_bar = pdf.get_y() + 1
        pdf.sentiment_bar(pdf.get_x(), y_bar, 60, sent)
        pdf.cell(65, 5, "")
        pdf.set_text_color(*COLOR_MUTED if not fiable else COLOR_TEXT)
        pdf.set_font("DejaVu", "" if not fiable else "", 7)
        pdf.cell(15, 5, f"{n}{'*' if not fiable else ''}", align="R")
        pdf.ln(7)

    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.cell(0, 5, "* Muestra baja (< 10 noticias) - valoración no estadísticamente fiable")
    pdf.ln(8)

    # ── PÁGINA 3: NARRATIVAS + CIS ────────────────────────
    pdf.add_page()
    pdf.section_title("4. Narrativas Activas")

    narr_counts = {}
    for _, row in df.iterrows():
        if row.get("narrativas") and str(row["narrativas"]) not in ["ninguna", "nan"]:
            for n in str(row["narrativas"]).split(","):
                n = n.strip()
                if n:
                    narr_counts[n] = narr_counts.get(n, 0) + 1

    if narr_counts:
        top_narr = sorted(narr_counts.items(), key=lambda x: -x[1])[:10]
        max_n    = top_narr[0][1] if top_narr else 1

        for narr, cnt in top_narr:
            pdf.set_font("DejaVu", "B", 8)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.set_x(13)
            pdf.cell(55, 5, narr)
            pdf.set_font("DejaVu", "", 8)
            pdf.set_text_color(*COLOR_MUTED)
            pdf.cell(20, 5, f"{cnt} menciones")
            y_b = pdf.get_y() + 1
            pdf.bar_h(pdf.get_x(), y_b, 80, cnt, max_n, COLOR_ACCENT)
            pdf.ln(7)
    else:
        pdf.set_font("DejaVu", "", 8)
        pdf.cell(0, 6, "No se detectaron narrativas en el período.")
        pdf.ln(8)

    # CIS vs SIEG
    pdf.section_title("5. Comparativa CIS vs Valoración Mediática SIEG")
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(*COLOR_MUTED)
    cis_meta = cfg.get("cis_meta", {})
    pdf.cell(0, 5,
        f"CIS escala 0-10 normalizada a -1/+1 para comparar · "
        f"Último barómetro: {cis_meta.get('ultimo_barometro','-')}")
    pdf.ln(7)

    if cis_data:
        pdf.set_font("DejaVu", "B", 8)
        pdf.set_text_color(*COLOR_MUTED)
        pdf.cell(50, 5, "LÍDER")
        pdf.cell(20, 5, "CIS")
        pdf.cell(20, 5, "SIEG")
        pdf.cell(25, 5, "DIVERGENCIA")
        pdf.cell(0,  5, "INTERPRETACIÓN")
        pdf.ln(6)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        for lider, info in cis_data.items():
            hist    = {k: v for k, v in info.get("historico", {}).items() if v is not None}
            if not hist:
                continue
            cis_val  = hist[sorted(hist.keys())[-1]]
            partido  = info.get("partido", "-")
            df_p     = df[df["partido"] == partido]
            if df_p.empty:
                continue
            sieg_val = df_p["sent_score"].mean()
            cis_norm = (cis_val / 10) * 2 - 1
            div      = sieg_val - cis_norm
            div_color = COLOR_POS if div > 0.15 else (COLOR_NEG if div < -0.15 else COLOR_NEU)

            pdf.set_font("DejaVu", "", 8)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.set_x(10)
            pdf.cell(50, 5, lider[:28])
            pdf.cell(20, 5, f"{cis_val:.2f}/10")
            pdf.cell(20, 5, f"{sieg_val:+.3f}")
            pdf.set_text_color(*div_color)
            pdf.set_font("DejaVu", "B", 8)
            pdf.cell(25, 5, f"{div:+.3f}")
            pdf.set_font("DejaVu", "", 7)
            pdf.set_text_color(*COLOR_MUTED)
            if div > 0.3:
                interp = "Prensa mas favorable que CIS"
            elif div < -0.3:
                interp = "Prensa mas negativa que CIS"
            else:
                interp = "Convergencia CIS/prensa"
            pdf.cell(0, 5, interp)
            pdf.ln(6)

    # ── PIE INFORME ───────────────────────────────────────
    pdf.ln(6)
    pdf.set_draw_color(*COLOR_LINE)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(*COLOR_MUTED)
    pdf.multi_cell(0, 4,
        "AVISO LEGAL: Este informe es generado automáticamente con fines informativos y de investigación. "
        "Los indicadores son aproximados y no deterministas. No evalúa la veracidad de noticias individuales. "
        "Para verificación de hechos: Newtral, Maldita, EFE Verifica. "
        "© 2026 M. Castillo · mybloggingnotes@gmail.com · Todos los derechos reservados."
    )

    pdf.output(output_path)
    print(f"Informe generado: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIEG - Generador de informe PDF")
    parser.add_argument("--output", help="Ruta de salida del PDF", default=None)
    args = parser.parse_args()
    generate(args.output)
