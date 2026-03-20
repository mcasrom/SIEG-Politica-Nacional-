import sqlite3
import os
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime



# ---------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------
# BASE_DIR: local (Odroid) o Streamlit Cloud
_local = os.path.expanduser("~/SIEG-Politica-Nacional")
_cloud = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = _local if os.path.exists(_local) else _cloud
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "noticias.db")
DATA_DIR = os.path.join(BASE_DIR, "data")

st.set_page_config(
    page_title="SIEG – Centro OSINT · Política Nacional",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<div style='padding: 0.6rem 0 0.4rem 0; border-bottom: 1px solid rgba(128,128,128,0.15); margin-bottom: 1rem'>
    <div style='font-size:0.72rem; font-weight:600; letter-spacing:0.14em;
                text-transform:uppercase; opacity:0.40; margin-bottom:3px'>
        Sistema de Inteligencia y Evaluación Geopolítica
    </div>
    <div style='font-size:1.8rem; font-weight:700; line-height:1.1'>
        Centro OSINT · Política Nacional
    </div>
    <div style='font-size:0.82rem; opacity:0.40; margin-top:5px'>
        Vigilancia narrativa automatizada · España ·
        © 2026 <a href='mailto:mybloggingnotes@gmail.com'
                  style='opacity:0.75; text-decoration:none; color:inherit'>M. Castillo</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style='padding: 0.3rem 0 0.9rem 0;
            border-bottom: 1px solid rgba(128,128,128,0.2);
            margin-bottom: 0.9rem'>
    <div style='font-size:0.65rem; font-weight:600; letter-spacing:0.12em;
                text-transform:uppercase; opacity:0.38; margin-bottom:2px'>
        SIEG
    </div>
    <div style='font-size:1rem; font-weight:600; line-height:1.25'>
        Centro OSINT<br>Política Nacional
    </div>
    <div style='font-size:0.68rem; opacity:0.35; margin-top:4px'>
        © 2026 M. Castillo
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# CARGA DE DATOS
# ---------------------------------------------------------

def load_data():
    # Streamlit Cloud: usa CSV exportados. Local: usa SQLite
    csv_path = os.path.join(BASE_DIR, "data", "export", "noticias_norm.csv")
    cloud_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "export", "noticias_norm.csv")
    _csv = csv_path if os.path.exists(csv_path) else cloud_csv
    if not os.path.exists(DB_PATH) and os.path.exists(_csv):
        df = pd.read_csv(_csv)
    else:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM noticias_norm", conn)
        conn.close()


    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["fecha"] = df["created_at"].dt.date
    df["source_type"] = df["source_type"].fillna("(sin tipo)").replace("", "(sin tipo)")

    return df

# En Streamlit Cloud el repo se clona en el directorio de trabajo
CLOUD_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "export", "noticias_norm.csv")
csv_path_check = os.path.join(BASE_DIR, "data", "export", "noticias_norm.csv")
_csv_exists = os.path.exists(csv_path_check) or os.path.exists(CLOUD_CSV)
if not os.path.exists(DB_PATH) and not _csv_exists:
    st.error("❌ No se encontró la base de datos ni los datos exportados.")
    st.stop()

df = load_data()

# Timestamp última actualización
_last_update = df["created_at"].max() if not df.empty else "—"
st.sidebar.markdown(f"""
<div style='margin-top:0.5rem; padding:0.5rem 0;
            border-top:1px solid rgba(128,128,128,0.15);
            font-size:0.72rem; opacity:0.5'>
    <div style='font-weight:600; letter-spacing:0.05em; margin-bottom:2px'>
        ÚLTIMA ACTUALIZACIÓN
    </div>
    <div>{str(_last_update)[:16].replace("T", " ")}</div>
</div>
""", unsafe_allow_html=True)


if df.empty:
    st.warning("⚠ La tabla noticias_norm está vacía.")
    st.stop()

# ---------------------------------------------------------
# TABS PRINCIPALES
# ---------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Análisis General",
    "📈 Tendencias & Narrativas",
    "🗺️ Tendencias por Territorio",
    "🧭 Inteligencia Narrativa",
    "📖 Guía de uso"
])


# =========================================================
# TAB 1 — ANÁLISIS GENERAL
# =========================================================
# =========================================================
# TAB 1 — ANÁLISIS GENERAL (versión corregida)
# Sustituye el bloque "with tab1:" completo en app_dashboard.py
#
# CAMBIOS PRINCIPALES:
# - Alertas corregidas: funcionan con pocos días de datos
# - Mapa eliminado (sin lat/lon suficiente) → sustituido por presencia territorial
# - Coocurrencias mejoradas
# - Sin duplicados con otros tabs
# =========================================================

with tab1:

    # ---------------------------------------------------------
    # FILTROS SIDEBAR
    # ---------------------------------------------------------
    st.sidebar.header("Filtros globales")

    partidos_disponibles = sorted(df["partido"].dropna().unique().tolist())
    partidos_sel = st.sidebar.multiselect(
        "Partidos", partidos_disponibles, default=partidos_disponibles
    )

    tipos_fuente = sorted(df["source_type"].unique().tolist())
    tipos_sel = st.sidebar.multiselect(
        "Tipo de fuente", tipos_fuente, default=tipos_fuente
    )

    fechas_disponibles = sorted(df["fecha"].dropna().unique())
    if len(fechas_disponibles) >= 2:
        rango_fechas = st.sidebar.date_input(
            "Rango de fechas",
            value=(fechas_disponibles[0], fechas_disponibles[-1])
        )
    else:
        rango_fechas = (fechas_disponibles[0], fechas_disponibles[-1]) if fechas_disponibles else (None, None)

    sentimientos_sel = st.sidebar.multiselect(
        "Sentimientos", ["POS", "NEG", "NEU"], default=["POS", "NEG", "NEU"]
    )

    # Aplicar filtros
    df_f = df[
        df["partido"].isin(partidos_sel)
        & df["sentiment_label"].isin(sentimientos_sel)
        & df["source_type"].isin(tipos_sel)
    ].copy()

    if isinstance(rango_fechas, (list, tuple)) and len(rango_fechas) == 2:
        ini, fin = rango_fechas
        if ini and fin:
            df_f = df_f[(df_f["fecha"] >= ini) & (df_f["fecha"] <= fin)]

    if df_f.empty:
        st.warning("⚠ No hay datos para los filtros seleccionados.")
        st.stop()

    # ---------------------------------------------------------
    # KPIs PRINCIPALES
    # ---------------------------------------------------------
    map_sent = {"POS": 1, "NEU": 0, "NEG": -1}
    df_f["sent_score"] = df_f["sentiment_label"].map(map_sent)

    total_noticias = len(df_f)
    total_partidos  = df_f["partido"].nunique()
    total_fuentes   = df_f["source"].nunique()
    sent_media      = df_f["sent_score"].mean()
    pct_neg         = (df_f["sentiment_label"] == "NEG").mean() * 100
    dias_cubiertos  = df_f["fecha"].nunique()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📰 Noticias", f"{total_noticias:,}")
    col2.metric("🏛️ Partidos", f"{total_partidos}")
    col3.metric("📡 Fuentes", f"{total_fuentes}")
    col4.metric("📅 Días cubiertos", f"{dias_cubiertos}")
    col5.metric("Sentimiento medio", f"{sent_media:.2f}")
    col6.metric("⚠️ % Negativo", f"{pct_neg:.1f}%")

    st.markdown("---")

    # ---------------------------------------------------------
    # ALERTAS — versión robusta para pocos días de datos
    # ---------------------------------------------------------
# =========================================================
# SECCIÓN: VALORACIÓN MEDIÁTICA DE LÍDERES
# Añadir en Tab 1, justo después del bloque de KPIs
# (después de los st.columns de métricas y antes de las alertas)
#
# © 2026 M. Castillo · mybloggingnotes@gmail.com
# =========================================================

    st.subheader("🎙️ Valoración mediática de líderes")
    st.caption("Sentimiento medio de cobertura por partido · escala −1 (negativo) a +1 (positivo) · mínimo 10 noticias para fiabilidad")

    # Cargar config de líderes
    import json as _json_val
    _cfg_val = _json_val.load(open(
        os.path.join(BASE_DIR, "config", "politica_config.json"), encoding="utf-8"
    ))
    _lideres_cfg = _cfg_val.get("lideres", {})

    # Calcular valoración por partido desde df_f (respeta filtros activos)
    map_sent_val = {"POS": 1, "NEU": 0, "NEG": -1}
    df_val = df_f.copy()
    df_val["sent_score"] = df_val["sentiment_label"].map(map_sent_val)

    ranking = []
    for partido, grupo in df_val.groupby("partido"):
        total = len(grupo)
        sent  = grupo["sent_score"].mean()
        pct_pos = (grupo["sentiment_label"] == "POS").mean() * 100
        pct_neg = (grupo["sentiment_label"] == "NEG").mean() * 100
        lider   = _lideres_cfg.get(partido, {}).get("lider", "—")
        ideol   = _lideres_cfg.get(partido, {}).get("ideologia", "—")
        fiable  = total >= 10
        ranking.append({
            "partido":  partido,
            "lider":    lider,
            "ideologia":ideol,
            "total":    total,
            "sent":     sent,
            "pct_pos":  pct_pos,
            "pct_neg":  pct_neg,
            "fiable":   fiable,
        })

    ranking = sorted(ranking, key=lambda x: x["sent"], reverse=True)

    # Renderizar ranking visual
    for r in ranking:
        sent   = r["sent"]
        total  = r["total"]
        fiable = r["fiable"]

        # Color según sentimiento
        if not fiable:
            bar_color   = "rgba(150,150,150,0.4)"
            text_color  = "#888"
            badge_color = "#ccc"
            badge_text  = "⚠ muestra baja"
        elif sent >= 0.3:
            bar_color   = "rgba(44,160,44,0.75)"
            text_color  = "#2ca02c"
            badge_color = "#d4edda"
            badge_text  = "🟢 positivo"
        elif sent >= 0.05:
            bar_color   = "rgba(255,187,0,0.65)"
            text_color  = "#996600"
            badge_color = "#fff3cd"
            badge_text  = "🟡 moderado"
        elif sent >= -0.1:
            bar_color   = "rgba(150,150,150,0.5)"
            text_color  = "#555"
            badge_color = "#e9ecef"
            badge_text  = "⚪ neutro"
        else:
            bar_color   = "rgba(214,39,40,0.7)"
            text_color  = "#d62728"
            badge_color = "#f8d7da"
            badge_text  = "🔴 negativo"

        # Barra: mapear sent de [-1,1] a [0,100]%
        bar_pct = int((sent + 1) / 2 * 100)
        # Línea central en 50%
        sent_fmt = f"{sent:+.2f}"

        st.markdown(f"""
<div style='margin-bottom:10px; padding:10px 14px;
            border:1px solid rgba(128,128,128,0.15);
            border-radius:8px; background:rgba(128,128,128,0.03)'>
  <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px'>
    <div>
      <span style='font-weight:600; font-size:0.95rem'>{r["partido"]}</span>
      <span style='font-size:0.8rem; opacity:0.55; margin-left:8px'>{r["lider"]}</span>
      <span style='font-size:0.72rem; opacity:0.4; margin-left:6px'>· {r["ideologia"]}</span>
    </div>
    <div style='display:flex; align-items:center; gap:8px'>
      <span style='font-size:0.72rem; padding:2px 7px; border-radius:10px;
                   background:{badge_color}; color:{text_color}'>{badge_text}</span>
      <span style='font-weight:700; font-size:0.95rem; color:{text_color}'>{sent_fmt}</span>
      <span style='font-size:0.72rem; opacity:0.4'>{total} noticias</span>
    </div>
  </div>
  <div style='position:relative; height:8px; background:rgba(128,128,128,0.12);
              border-radius:4px; overflow:hidden'>
    <div style='position:absolute; left:0; top:0; height:100%;
                width:{bar_pct}%; background:{bar_color};
                border-radius:4px; transition:width 0.3s'></div>
    <div style='position:absolute; left:50%; top:0; height:100%;
                width:1px; background:rgba(128,128,128,0.3)'></div>
  </div>
  <div style='display:flex; justify-content:space-between; font-size:0.68rem;
              opacity:0.35; margin-top:3px'>
    <span>−1 negativo</span>
    <span>▲ {r["pct_pos"]:.0f}% pos · {r["pct_neg"]:.0f}% neg</span>
    <span>+1 positivo</span>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("🚨 Alertas de actividad por partido")

    fechas_unicas = sorted(df_f["fecha"].unique())
    n_dias = len(fechas_unicas)

    if n_dias == 0:
        st.info("Sin datos suficientes para alertas.")
    elif n_dias == 1:
        # Un solo día: ranking de negatividad absoluta
        st.caption(f"Solo hay datos de 1 día ({fechas_unicas[0]}). Mostrando ranking de negatividad.")
        for partido in sorted(df_f["partido"].unique()):
            df_tmp = df_f[df_f["partido"] == partido]
            neg = (df_tmp["sentiment_label"] == "NEG").sum()
            tot = len(df_tmp)
            pct = neg / tot * 100 if tot > 0 else 0
            icon = "🔴" if pct > 20 else ("🟠" if pct > 10 else "🟢")
            st.markdown(f"{icon} **{partido}** — {neg} noticias negativas de {tot} ({pct:.1f}%)")
    else:
        # 2+ días: comparar último día vs media del resto
        ultimo = fechas_unicas[-1]
        anteriores = fechas_unicas[:-1]

        for partido in sorted(df_f["partido"].unique()):
            df_p = df_f[df_f["partido"] == partido]

            df_hoy   = df_p[df_p["fecha"] == ultimo]
            df_antes = df_p[df_p["fecha"].isin(anteriores)]

            tot_hoy   = len(df_hoy)
            neg_hoy   = (df_hoy["sentiment_label"] == "NEG").sum()
            pct_neg_hoy = neg_hoy / tot_hoy * 100 if tot_hoy > 0 else 0

            if len(df_antes) > 0:
                # Negatividad media diaria en días anteriores
                neg_antes_dia = (
                    df_antes.groupby("fecha")
                    .apply(lambda x: (x["sentiment_label"] == "NEG").mean() * 100)
                )
                media_anterior = neg_antes_dia.mean()
                delta = pct_neg_hoy - media_anterior

                if delta > 10:
                    icon = "🔴"
                    msg = f"sube **{delta:+.1f}pp** vs días anteriores ({media_anterior:.1f}% → {pct_neg_hoy:.1f}%)"
                elif delta > 4:
                    icon = "🟠"
                    msg = f"leve aumento **{delta:+.1f}pp** ({media_anterior:.1f}% → {pct_neg_hoy:.1f}%)"
                elif delta < -10:
                    icon = "🔵"
                    msg = f"mejora **{delta:+.1f}pp** ({media_anterior:.1f}% → {pct_neg_hoy:.1f}%)"
                else:
                    icon = "🟢"
                    msg = f"estable ({pct_neg_hoy:.1f}% neg. hoy)"
            else:
                icon = "⚪"
                msg = f"solo datos de hoy ({pct_neg_hoy:.1f}% neg.)"

            vol_hoy = len(df_hoy)
            st.markdown(f"{icon} **{partido}** — {msg} · {vol_hoy} noticias hoy")

    st.markdown("---")

    # ---------------------------------------------------------
    # VOLUMEN POR PARTIDO Y DÍA
    # ---------------------------------------------------------
    st.subheader("📊 Volumen de noticias por partido")

    df_vol = (
        df_f.groupby(["fecha", "partido"])
        .size()
        .reset_index(name="noticias")
    )

    # Si hay más de 1 día: gráfico temporal. Si no: barras simples.
    if dias_cubiertos > 1:
        chart_vol = (
            alt.Chart(df_vol)
            .mark_line(point=True)
            .encode(
                x=alt.X("fecha:T", title="Fecha"),
                y=alt.Y("noticias:Q", title="Noticias"),
                color="partido:N",
                tooltip=["fecha:T", "partido:N", "noticias:Q"]
            )
            .properties(height=280)
        )
    else:
        df_vol_bar = df_f.groupby("partido").size().reset_index(name="noticias")
        chart_vol = (
            alt.Chart(df_vol_bar)
            .mark_bar()
            .encode(
                x=alt.X("noticias:Q"),
                y=alt.Y("partido:N", sort="-x"),
                color=alt.Color("noticias:Q", scale=alt.Scale(scheme="blues")),
                tooltip=["partido:N", "noticias:Q"]
            )
            .properties(height=280)
        )

    st.altair_chart(chart_vol, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # SENTIMIENTO POR PARTIDO (balance + distribución lado a lado)
    # ---------------------------------------------------------
    st.subheader("💬 Sentimiento por partido")

    c_sent1, c_sent2 = st.columns(2)

    # Balance de sentimiento
    df_balance = (
        df_f.groupby("partido")["sent_score"]
        .mean()
        .reset_index()
        .rename(columns={"sent_score": "balance"})
        .sort_values("balance")
    )

    chart_bal = (
        alt.Chart(df_balance)
        .mark_bar()
        .encode(
            x=alt.X("balance:Q", title="Balance (−1 a 1)"),
            y=alt.Y("partido:N", sort="x", title=""),
            color=alt.condition(
                "datum.balance > 0",
                alt.value("#2ca02c"),
                alt.value("#d62728")
            ),
            tooltip=["partido:N", alt.Tooltip("balance:Q", format=".3f")]
        )
        .properties(height=280, title="Balance de sentimiento")
    )

    with c_sent1:
        st.altair_chart(chart_bal, use_container_width=True)

    # Distribución POS/NEU/NEG
    df_dist = (
        df_f.groupby(["partido", "sentiment_label"])
        .size()
        .reset_index(name="count")
    )
    total_p = df_dist.groupby("partido")["count"].transform("sum")
    df_dist["pct"] = df_dist["count"] / total_p * 100

    chart_dist = (
        alt.Chart(df_dist)
        .mark_bar()
        .encode(
            x=alt.X("pct:Q", stack="normalize", title="Proporción"),
            y=alt.Y("partido:N", title=""),
            color=alt.Color(
                "sentiment_label:N",
                scale=alt.Scale(
                    domain=["POS", "NEU", "NEG"],
                    range=["#2ca02c", "#aec7e8", "#d62728"]
                ),
                legend=alt.Legend(title="Sentimiento")
            ),
            tooltip=["partido:N", "sentiment_label:N", alt.Tooltip("pct:Q", format=".1f")]
        )
        .properties(height=280, title="Distribución proporcional")
    )

    with c_sent2:
        st.altair_chart(chart_dist, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # TIPO DE FUENTE
    # ---------------------------------------------------------
    st.subheader("📡 Cobertura por tipo de fuente")

    df_fuente = (
        df_f.groupby(["source_type", "partido"])
        .size()
        .reset_index(name="count")
    )

    chart_fuente = (
        alt.Chart(df_fuente)
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Noticias"),
            y=alt.Y("source_type:N", title=""),
            color="partido:N",
            tooltip=["source_type:N", "partido:N", "count:Q"]
        )
        .properties(height=220)
    )

    st.altair_chart(chart_fuente, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # PRESENCIA TERRITORIAL (sin mapa, con barras)
    # ---------------------------------------------------------
    st.subheader("🗺️ Presencia territorial por partido")

    df_terr = df_f[
        df_f["territorio"].notna() & (df_f["territorio"] != "")
    ]

    if df_terr.empty:
        st.info("No hay datos territoriales suficientes en el rango seleccionado.")
    else:
        df_terr_g = (
            df_terr.groupby(["territorio", "partido"])
            .size()
            .reset_index(name="count")
        )

        chart_terr = (
            alt.Chart(df_terr_g)
            .mark_bar()
            .encode(
                x=alt.X("count:Q", title="Noticias"),
                y=alt.Y("territorio:N", sort="-x", title=""),
                color="partido:N",
                tooltip=["territorio:N", "partido:N", "count:Q"]
            )
            .properties(height=max(200, len(df_terr_g["territorio"].unique()) * 22))
        )

        st.altair_chart(chart_terr, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # COOCURRENCIAS ENTRE PARTIDOS
    # ---------------------------------------------------------
    st.subheader("🔗 Coocurrencias entre partidos (misma noticia/hash)")

    # Usa partidos_detectados si existe, si no usa hash_id
    if "partidos_detectados" in df_f.columns and df_f["partidos_detectados"].notna().any():
        cooc = {}
        for val in df_f["partidos_detectados"].dropna():
            lista = sorted(set([p.strip() for p in str(val).split(",") if p.strip()]))
            for i in range(len(lista)):
                for j in range(i + 1, len(lista)):
                    par = f"{lista[i]} – {lista[j]}"
                    cooc[par] = cooc.get(par, 0) + 1
    else:
        # Fallback: agrupar por hash_id
        df_group = df_f.groupby("hash_id")["partido"].apply(list).reset_index()
        cooc = {}
        for lista in df_group["partido"]:
            lista = sorted(set(lista))
            for i in range(len(lista)):
                for j in range(i + 1, len(lista)):
                    par = f"{lista[i]} – {lista[j]}"
                    cooc[par] = cooc.get(par, 0) + 1

    if cooc:
        df_cooc = (
            pd.DataFrame({"pareja": list(cooc.keys()), "coocurrencias": list(cooc.values())})
            .sort_values("coocurrencias", ascending=False)
            .head(20)
        )

        chart_cooc = (
            alt.Chart(df_cooc)
            .mark_bar()
            .encode(
                x=alt.X("coocurrencias:Q"),
                y=alt.Y("pareja:N", sort="-x", title=""),
                color=alt.Color("coocurrencias:Q", scale=alt.Scale(scheme="purples")),
                tooltip=["pareja:N", "coocurrencias:Q"]
            )
            .properties(height=max(200, len(df_cooc) * 22))
        )

        st.altair_chart(chart_cooc, use_container_width=True)
    else:
        st.info("No se detectaron coocurrencias en el período seleccionado.")

    st.markdown("---")

    # ---------------------------------------------------------
    # TOP FUENTES MÁS ACTIVAS
    # ---------------------------------------------------------
    st.subheader("📰 Top fuentes por volumen")

    df_top_fuentes = (
        df_f.groupby("source")
        .size()
        .reset_index(name="noticias")
        .sort_values("noticias", ascending=False)
        .head(15)
    )

    chart_top = (
        alt.Chart(df_top_fuentes)
        .mark_bar()
        .encode(
            x=alt.X("noticias:Q"),
            y=alt.Y("source:N", sort="-x", title=""),
            color=alt.Color("noticias:Q", scale=alt.Scale(scheme="teals")),
            tooltip=["source:N", "noticias:Q"]
        )
        .properties(height=320)
    )

    st.altair_chart(chart_top, use_container_width=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # NOTICIAS RECIENTES
    # ---------------------------------------------------------
    st.subheader("📋 Noticias recientes")

    cols_mostrar = [c for c in ["created_at", "source", "source_type", "title", "partido", "sentiment_label", "territorio", "link"] if c in df_f.columns]

    st.dataframe(
        df_f.sort_values("created_at", ascending=False)[cols_mostrar].head(50),
        use_container_width=True
    )

    # ---------------------------------------------------------
    # CONTROL DE CRECIMIENTO DE BD
    # ---------------------------------------------------------
    with st.expander("🗄️ Estado de la base de datos y control de crecimiento"):
        conn2 = sqlite3.connect(DB_PATH)

        df_ingesta = pd.read_sql_query(
            "SELECT DATE(created_at) as dia, COUNT(*) as total FROM noticias_norm GROUP BY dia ORDER BY dia DESC LIMIT 30",
            conn2
        )
        df_duplicados = pd.read_sql_query(
            "SELECT COUNT(*) as total, COUNT(DISTINCT hash_id) as unicos FROM noticias_norm",
            conn2
        )
        df_size = pd.read_sql_query(
            "SELECT COUNT(*) as filas FROM noticias_norm",
            conn2
        )

        conn2.close()

        c_db1, c_db2, c_db3 = st.columns(3)
        c_db1.metric("Filas totales", f"{df_size['filas'].iloc[0]:,}")
        c_db2.metric("Registros únicos (hash)", f"{df_duplicados['unicos'].iloc[0]:,}")
        dup = df_duplicados['total'].iloc[0] - df_duplicados['unicos'].iloc[0]
        c_db3.metric("Duplicados detectados", f"{dup:,}", delta=f"{'⚠️ revisar' if dup > 0 else 'OK'}", delta_color="inverse")

        if not df_ingesta.empty:
            chart_ingesta = (
                alt.Chart(df_ingesta)
                .mark_bar()
                .encode(
                    x=alt.X("dia:T", title="Día"),
                    y=alt.Y("total:Q", title="Noticias ingestadas"),
                    color=alt.Color("total:Q", scale=alt.Scale(scheme="blues")),
                    tooltip=["dia:T", "total:Q"]
                )
                .properties(height=200, title="Volumen de ingesta diaria (últimos 30 días)")
            )
            st.altair_chart(chart_ingesta, use_container_width=True)

        st.caption("💡 Si los duplicados crecen, revisar el pipeline de deduplicación por hash_id.")

    # ---------------------------------------------------------
    # METODOLOGÍA
    # ---------------------------------------------------------
    with st.expander("📘 Metodología y notas"):
        st.markdown("""
**Metodología:**
- Análisis OSINT basado en RSS de medios nacionales, autonómicos y locales.
- Normalización 1 noticia × 1 partido detectado.
- Detección de partidos mediante keywords, líderes y alias.
- Análisis de sentimiento léxico (TextBlob / RoBERTa-ES).
- Indicadores aproximados, no deterministas.

**Autoría:** M. Castillo · mybloggingnotes@gmail.com
""")

    st.caption("SIEG – Sistema de Inteligencia y Evaluación Geopolítica · M. Castillo")

# =========================================================
# TAB 2 — TENDENCIAS & NARRATIVAS
# =========================================================

with tab2:

    st.header("📈 Tendencias & Narrativas – Análisis OSINT Avanzado")

    # Cargar tendencias
    csv_tend = os.path.join(BASE_DIR, "data", "export", "tendencias_diarias.csv")
    if not os.path.exists(DB_PATH) and os.path.exists(csv_tend):
        df_t = pd.read_csv(csv_tend)
    else:
        conn = sqlite3.connect(DB_PATH)
        df_t = pd.read_sql_query("SELECT * FROM tendencias_diarias", conn)
        conn.close()

    df_t["fecha"] = pd.to_datetime(df_t["fecha"], errors="coerce")

    # -------------------------------
    # FILTROS
    # -------------------------------
    st.subheader("🎛️ Filtros de tendencias")

    tipos = sorted(df_t["tipo"].unique().tolist())
    tipo_sel = st.selectbox("Tipo de tendencia", tipos, index=0)

    claves = sorted(df_t[df_t["tipo"] == tipo_sel]["clave"].unique().tolist())
    claves_sel = st.multiselect("Claves", claves, default=claves[:5])

    rango_t = st.date_input(
        "Rango temporal",
        value=(df_t["fecha"].min(), df_t["fecha"].max())
    )

    df_tf = df_t[
        (df_t["tipo"] == tipo_sel)
        & (df_t["clave"].isin(claves_sel))
    ]

    if isinstance(rango_t, (list, tuple)) and len(rango_t) == 2:
        ini, fin = rango_t
        df_tf = df_tf[(df_tf["fecha"] >= pd.to_datetime(ini)) & (df_tf["fecha"] <= pd.to_datetime(fin))]

    if df_tf.empty:
        st.warning("⚠ No hay datos para los filtros seleccionados.")
        st.stop()

    # -------------------------------
    # GRÁFICO PRINCIPAL
    # -------------------------------
    st.subheader("📉 Evolución temporal")

    chart_tend = (
        alt.Chart(df_tf)
        .mark_line(point=True)
        .encode(
            x="fecha:T",
            y="total:Q",
            color="clave:N",
            tooltip=["fecha:T", "clave:N", "total:Q"]
        )
        .properties(height=350)
    )

    st.altair_chart(chart_tend, width='stretch')

    # -------------------------------
    # RANKING DEL DÍA
    # -------------------------------
    st.subheader("🏆 Ranking del día más reciente")

    ultimo_dia = df_tf["fecha"].max()
    df_day = df_tf[df_tf["fecha"] == ultimo_dia].sort_values("total", ascending=False)

    chart_rank = (
        alt.Chart(df_day)
        .mark_bar()
        .encode(
            x="total:Q",
            y="clave:N",
            color="clave:N",
            tooltip=["clave:N", "total:Q"]
        )
        .properties(height=300)
    )

    st.altair_chart(chart_rank, width='stretch')

    # -------------------------------
    # ALERTAS DE PICOS
    # -------------------------------
    st.subheader("🚨 Alertas automáticas de picos")

    alertas = []
    for clave in claves_sel:
        df_c = df_tf[df_tf["clave"] == clave].sort_values("fecha")
        if len(df_c) < 7:
            continue

        media = df_c["total"].rolling(7).mean().iloc[-1]
        hoy = df_c["total"].iloc[-1]

        if media == 0:
            continue

        variacion = ((hoy / media) - 1) * 100

        if variacion > 150:
            alertas.append(f"🔴 **{clave}** se dispara **{variacion:.1f}%** sobre la media semanal.")
        elif variacion > 60:
            alertas.append(f"🟠 **{clave}** sube **{variacion:.1f}%**.")
        elif variacion < -40:
            alertas.append(f"🔵 **{clave}** cae **{abs(variacion):.1f}%**.")
        else:
            alertas.append(f"🟢 **{clave}** estable ({variacion:.1f}%).")

    for a in alertas:
        st.markdown(a)

    # -------------------------------
    # TABLA DETALLADA
    # -------------------------------
    st.subheader("📋 Datos detallados")

    st.dataframe(
        df_tf.sort_values(["fecha", "total"], ascending=[False, False]),
        width='stretch'
    )

with tab3:

    st.header("🗺️ Tendencias por Territorio – Análisis Geopolítico")

    # -------------------------------
    # Cargar datos territoriales
    # -------------------------------
    df_geo = df.copy()
    df_geo["fecha"] = pd.to_datetime(df_geo["created_at"], errors="coerce").dt.date

    st.subheader("🎛️ Filtros territoriales")

    # Selección de nivel territorial
    nivel = st.selectbox("Nivel territorial", ["Territorio", "Provincia"])

    if nivel == "Territorio":
        territorios = sorted(df_geo["territorio"].dropna().unique().tolist())
        col_territorio = "territorio"
    else:
        territorios = sorted(df_geo["provincia"].dropna().unique().tolist())
        col_territorio = "provincia"

    territorios_sel = st.multiselect("Territorios", territorios, default=territorios[:5])

    # Selección de tipo de tendencia
    tipo_tend = st.selectbox("Tipo de tendencia", ["temas", "narrativas", "partido"])

    # Rango temporal
    rango_t = st.date_input(
    "Rango temporal",
    value=(df_geo["fecha"].min(), df_geo["fecha"].max()),
    key="territorio_rango_temporal"
    )

    df_tf = df_geo[
        df_geo[col_territorio].isin(territorios_sel)
        & (df_geo["fecha"] >= rango_t[0])
        & (df_geo["fecha"] <= rango_t[1])
    ]

    if df_tf.empty:
        st.warning("⚠ No hay datos para los filtros seleccionados.")
        st.stop()

    # -------------------------------
    # Procesar tendencias territoriales
    # -------------------------------
    registros = []

    for _, row in df_tf.iterrows():
        fecha = row["fecha"]
        territorio = row[col_territorio]

        if tipo_tend == "temas":
            valores = row["temas"].split(",") if row["temas"] else []
        elif tipo_tend == "narrativas":
            valores = row["narrativas"].split(",") if row["narrativas"] else []
        else:
            valores = [row["partido"]] if row["partido"] else []

        for v in valores:
            v = v.strip()
            if v and v != "ninguna":
                registros.append([fecha, territorio, v])

    df_tend = pd.DataFrame(registros, columns=["fecha", "territorio", "clave"])

    if df_tend.empty:
        st.warning("⚠ No hay datos para mostrar tendencias.")
        st.stop()

    df_tend_count = (
        df_tend.groupby(["fecha", "territorio", "clave"])
        .size()
        .reset_index(name="total")
    )

    # -------------------------------
    # Gráfico temporal por territorio
    # -------------------------------
    st.subheader("📉 Evolución temporal por territorio")

    chart_temp = (
        alt.Chart(df_tend_count)
        .mark_line(point=True)
        .encode(
            x="fecha:T",
            y="total:Q",
            color="territorio:N",
            tooltip=["fecha:T", "territorio:N", "clave:N", "total:Q"]
        )
        .properties(height=350)
    )

    st.altair_chart(chart_temp, width='stretch')

    # -------------------------------
    # Ranking territorial del día
    # -------------------------------
    st.subheader("🏆 Ranking territorial del día más reciente")

    ultimo_dia = df_tend_count["fecha"].max()
    df_day = df_tend_count[df_tend_count["fecha"] == ultimo_dia]

    chart_rank = (
        alt.Chart(df_day)
        .mark_bar()
        .encode(
            x="total:Q",
            y="territorio:N",
            color="territorio:N",
            tooltip=["territorio:N", "total:Q"]
        )
        .properties(height=300)
    )

    st.altair_chart(chart_rank, width='stretch')

    # -------------------------------
    # Alertas territoriales
    # -------------------------------
    st.subheader("🚨 Alertas territoriales")

    alertas = []

    for territorio in territorios_sel:
        df_c = df_tend_count[df_tend_count["territorio"] == territorio].sort_values("fecha")
        if len(df_c) < 7:
            continue

        media = df_c["total"].rolling(7).mean().iloc[-1]
        hoy = df_c["total"].iloc[-1]

        if media == 0:
            continue

        variacion = ((hoy / media) - 1) * 100

        if variacion > 150:
            alertas.append(f"🔴 **{territorio}** se dispara **{variacion:.1f}%**.")
        elif variacion > 60:
            alertas.append(f"🟠 **{territorio}** sube **{variacion:.1f}%**.")
        elif variacion < -40:
            alertas.append(f"🔵 **{territorio}** cae **{abs(variacion):.1f}%**.")
        else:
            alertas.append(f"🟢 **{territorio}** estable ({variacion:.1f}%).")

    for a in alertas:
        st.markdown(a)

    # -------------------------------
    # Tabla detallada
    # -------------------------------
    st.subheader("📋 Datos detallados")

    st.dataframe(
        df_tend_count.sort_values(["fecha", "total"], ascending=[False, False]),
        width='stretch'
    )
# =========================================================
# TAB 4 — INTELIGENCIA NARRATIVA
# =========================================================
# =========================================================
# TAB 4 — INTELIGENCIA NARRATIVA (reemplaza el bloque vacío)
# Pegar este bloque al final de app_dashboard.py,
# sustituyendo el "with tab4:" vacío existente.
# =========================================================


import json as _json_cfg
_sieg_cfg = _json_cfg.load(open(
    os.path.join(os.path.expanduser("~/SIEG-Politica-Nacional"),
    "config", "politica_config.json"), encoding="utf-8"))

# Mapa de líderes por partido (actualizable)
# LIDERES cargado desde config/politica_config.json
LIDERES = _sieg_cfg["lideres"]


# Narrativas y su connotación política inferida
# NARRATIVA_PERFIL cargado desde config/politica_config.json
NARRATIVA_PERFIL = _sieg_cfg["narrativas_perfil"]


with tab4:
    st.header("🧭 Inteligencia Narrativa – Análisis de Partidos y Discurso")

    # --------------------------------------------------------
    # DATOS BASE
    # --------------------------------------------------------
    conn = sqlite3.connect(DB_PATH)
    df_narr = pd.read_sql_query("SELECT * FROM noticias_norm WHERE partido IS NOT NULL", conn)
    df_tend_all = pd.read_sql_query("SELECT * FROM tendencias_diarias", conn)
    conn.close()

    df_narr["created_at"] = pd.to_datetime(df_narr["created_at"], errors="coerce")
    df_narr["fecha"] = df_narr["created_at"].dt.date
    df_tend_all["fecha"] = pd.to_datetime(df_tend_all["fecha"], errors="coerce")

    partidos_narr = sorted(df_narr["partido"].unique().tolist())

    # --------------------------------------------------------
    # SELECTOR DE PARTIDO
    # --------------------------------------------------------
    partido_sel = st.selectbox("🔍 Seleccionar partido para análisis", partidos_narr, key="tab4_partido")

    df_p = df_narr[df_narr["partido"] == partido_sel]
    info = LIDERES.get(partido_sel, {"lider": "Desconocido", "posicion": "—", "ideologia": "—"})

    st.markdown("---")

    # --------------------------------------------------------
    # FICHA DE PARTIDO
    # --------------------------------------------------------
    st.subheader(f"🏛️ Ficha: {partido_sel}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Líder", info["lider"])
    c2.metric("Posición", info["posicion"])
    c3.metric("Ideología", info["ideologia"])
    c4.metric("Noticias totales", f"{len(df_p):,}")

    st.markdown("---")

    # --------------------------------------------------------
    # KPIs NARRATIVOS
    # --------------------------------------------------------
    st.subheader("📊 KPIs Narrativos")

    map_sent = {"POS": 1, "NEU": 0, "NEG": -1}
    df_p = df_p.copy()
    df_p["sent_score"] = df_p["sentiment_label"].map(map_sent)

    sent_medio = df_p["sent_score"].mean()
    pct_neg = (df_p["sentiment_label"] == "NEG").mean() * 100
    pct_pos = (df_p["sentiment_label"] == "POS").mean() * 100
    pct_neu = (df_p["sentiment_label"] == "NEU").mean() * 100

    # Narrativa dominante del partido
    df_tend_partido = df_tend_all[
        (df_tend_all["tipo"] == "narrativa") |
        (df_tend_all["clave"] == partido_sel)
    ]
    # Narrativas en noticias del partido
    narr_counts = {}
    for _, row in df_p.iterrows():
        if row["narrativas"] and row["narrativas"] != "ninguna":
            for n in str(row["narrativas"]).split(","):
                n = n.strip()
                if n:
                    narr_counts[n] = narr_counts.get(n, 0) + 1

    narr_dominante = max(narr_counts, key=narr_counts.get) if narr_counts else "ninguna"

    # Temas dominantes
    tema_counts = {}
    for _, row in df_p.iterrows():
        if row["temas"]:
            for t in str(row["temas"]).split(","):
                t = t.strip()
                if t:
                    tema_counts[t] = tema_counts.get(t, 0) + 1

    tema_dominante = max(tema_counts, key=tema_counts.get) if tema_counts else "—"

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Sentimiento medio", f"{sent_medio:.2f}")
    k2.metric("% Positivo", f"{pct_pos:.1f}%")
    k3.metric("% Negativo", f"{pct_neg:.1f}%")
    k4.metric("% Neutro", f"{pct_neu:.1f}%")
    k5.metric("Narrativa dominante", narr_dominante)
    k6.metric("Tema dominante", tema_dominante)

    st.markdown("---")

    # --------------------------------------------------------
    # EVOLUCIÓN HISTÓRICA DEL SENTIMIENTO
    # --------------------------------------------------------
    st.subheader("📈 Histórico de sentimiento")

    df_hist = (
        df_p.groupby(["fecha", "sentiment_label"])
        .size()
        .reset_index(name="count")
    )

    chart_hist = (
        alt.Chart(df_hist)
        .mark_area(opacity=0.7)
        .encode(
            x="fecha:T",
            y=alt.Y("count:Q", stack="normalize", title="Proporción"),
            color=alt.Color(
                "sentiment_label:N",
                scale=alt.Scale(
                    domain=["POS", "NEU", "NEG"],
                    range=["#2ca02c", "#aec7e8", "#d62728"]
                )
            ),
            tooltip=["fecha:T", "sentiment_label:N", "count:Q"]
        )
        .properties(height=250, title=f"Evolución sentimiento – {partido_sel}")
    )

    st.altair_chart(chart_hist, use_container_width=True)

    # --------------------------------------------------------
    # TEMAS MÁS USADOS
    # --------------------------------------------------------
    st.subheader("🗂️ Temas más frecuentes")

    df_temas = pd.DataFrame(
        list(tema_counts.items()), columns=["tema", "count"]
    ).sort_values("count", ascending=False).head(15)

    chart_temas = (
        alt.Chart(df_temas)
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Frecuencia"),
            y=alt.Y("tema:N", sort="-x", title=""),
            color=alt.Color("count:Q", scale=alt.Scale(scheme="blues")),
            tooltip=["tema:N", "count:Q"]
        )
        .properties(height=350)
    )

    st.altair_chart(chart_temas, use_container_width=True)

    # --------------------------------------------------------
    # NARRATIVAS ACTIVAS
    # --------------------------------------------------------
    st.subheader("🌀 Narrativas activas en el discurso")

    if narr_counts:
        df_narr_p = pd.DataFrame(
            list(narr_counts.items()), columns=["narrativa", "count"]
        ).sort_values("count", ascending=False)

        colors_narr = [
            NARRATIVA_PERFIL.get(n, {}).get("color", "#999") for n in df_narr_p["narrativa"]
        ]

        chart_narr = (
            alt.Chart(df_narr_p)
            .mark_bar()
            .encode(
                x=alt.X("count:Q", title="Menciones"),
                y=alt.Y("narrativa:N", sort="-x", title=""),
                tooltip=["narrativa:N", "count:Q"]
            )
            .properties(height=250)
        )
        st.altair_chart(chart_narr, use_container_width=True)

        for n, cnt in sorted(narr_counts.items(), key=lambda x: -x[1]):
            perfil = NARRATIVA_PERFIL.get(n, {})
            desc = perfil.get("desc", "Sin descripción")
            st.markdown(f"- **{n}** ({cnt} menciones) — _{desc}_")
    else:
        st.info("No se detectaron narrativas específicas para este partido en los datos disponibles.")

    st.markdown("---")

    # --------------------------------------------------------
    # ROTACIÓN NARRATIVA HISTÓRICA
    # --------------------------------------------------------
    st.subheader("🔄 Rotación narrativa histórica")
    st.caption("Evolución semanal de narrativas detectadas en todo el sistema")

    df_rot = df_tend_all[df_tend_all["tipo"] == "narrativa"].copy()
    df_rot["semana"] = df_rot["fecha"].dt.to_period("W").apply(lambda r: r.start_time)

    df_rot_g = (
        df_rot.groupby(["semana", "clave"])["total"]
        .sum()
        .reset_index()
    )

    top_narr = df_rot_g.groupby("clave")["total"].sum().nlargest(8).index.tolist()
    df_rot_top = df_rot_g[df_rot_g["clave"].isin(top_narr)]

    chart_rot = (
        alt.Chart(df_rot_top)
        .mark_line(point=True)
        .encode(
            x=alt.X("semana:T", title="Semana"),
            y=alt.Y("total:Q", title="Menciones"),
            color="clave:N",
            tooltip=["semana:T", "clave:N", "total:Q"]
        )
        .properties(height=300)
    )

    st.altair_chart(chart_rot, use_container_width=True)

    st.markdown("---")

    # --------------------------------------------------------
    # MAPA DE CALOR: PARTIDO × NARRATIVA
    # --------------------------------------------------------
    st.subheader("🔥 Mapa de calor: partido × narrativa")

    registros_heat = []
    for _, row in df_narr.iterrows():
        if row["narrativas"] and row["narrativas"] != "ninguna":
            for n in str(row["narrativas"]).split(","):
                n = n.strip()
                if n:
                    registros_heat.append({"partido": row["partido"], "narrativa": n})

    if registros_heat:
        df_heat_narr = (
            pd.DataFrame(registros_heat)
            .groupby(["partido", "narrativa"])
            .size()
            .reset_index(name="count")
        )

        chart_heat_narr = (
            alt.Chart(df_heat_narr)
            .mark_rect()
            .encode(
                x=alt.X("narrativa:N", title="Narrativa"),
                y=alt.Y("partido:N", title="Partido"),
                color=alt.Color("count:Q", scale=alt.Scale(scheme="orangered")),
                tooltip=["partido:N", "narrativa:N", "count:Q"]
            )
            .properties(height=300)
        )
        st.altair_chart(chart_heat_narr, use_container_width=True)
    else:
        st.info("No hay suficientes datos de narrativas para el mapa de calor.")

    st.markdown("---")

    # --------------------------------------------------------
    # MAPA GEOGRÁFICO DE PRESENCIA
    # --------------------------------------------------------
    st.subheader("🗺️ Presencia territorial del partido")

    df_geo_p = df_p.dropna(subset=["lat", "lon"])

    if df_geo_p.empty:
        st.info("No hay datos geográficos para este partido en el período seleccionado.")
    else:
        df_map = df_geo_p[["lat", "lon"]].rename(columns={"lat": "latitude", "lon": "longitude"})
        st.map(df_map)

        # Distribución por territorio
        df_terr = (
            df_p[df_p["territorio"].notna() & (df_p["territorio"] != "")]
            .groupby("territorio")
            .size()
            .reset_index(name="noticias")
            .sort_values("noticias", ascending=False)
        )

        if not df_terr.empty:
            chart_terr = (
                alt.Chart(df_terr)
                .mark_bar()
                .encode(
                    x=alt.X("noticias:Q"),
                    y=alt.Y("territorio:N", sort="-x"),
                    color=alt.Color("noticias:Q", scale=alt.Scale(scheme="greens")),
                    tooltip=["territorio:N", "noticias:Q"]
                )
                .properties(height=300, title="Noticias por territorio")
            )
            st.altair_chart(chart_terr, use_container_width=True)

    st.markdown("---")

    # --------------------------------------------------------
    # COMPARATIVA ENTRE PARTIDOS
    # --------------------------------------------------------
    st.subheader("⚖️ Comparativa general entre partidos")

    resumen = []
    for p in partidos_narr:
        df_tmp = df_narr[df_narr["partido"] == p].copy()
        df_tmp["sent_score"] = df_tmp["sentiment_label"].map(map_sent)
        info_p = LIDERES.get(p, {"lider": "—", "posicion": "—", "ideologia": "—"})

        narr_p = {}
        for _, row in df_tmp.iterrows():
            if row["narrativas"] and row["narrativas"] != "ninguna":
                for n in str(row["narrativas"]).split(","):
                    n = n.strip()
                    if n:
                        narr_p[n] = narr_p.get(n, 0) + 1

        resumen.append({
            "Partido": p,
            "Líder": info_p["lider"],
            "Posición": info_p["posicion"],
            "Ideología": info_p["ideologia"],
            "Noticias": len(df_tmp),
            "Sent. medio": round(df_tmp["sent_score"].mean(), 3),
            "% NEG": round((df_tmp["sentiment_label"] == "NEG").mean() * 100, 1),
            "% POS": round((df_tmp["sentiment_label"] == "POS").mean() * 100, 1),
            "Narrativa top": max(narr_p, key=narr_p.get) if narr_p else "ninguna",
        })

    df_resumen = pd.DataFrame(resumen)
    st.dataframe(df_resumen, use_container_width=True)

    # --------------------------------------------------------
    # VISIÓN / POSICIONAMIENTO INFERIDO
    # --------------------------------------------------------
    st.subheader("🧠 Visión y posicionamiento inferido por partido")

    for p in partidos_narr:
        df_tmp = df_narr[df_narr["partido"] == p].copy()
        df_tmp["sent_score"] = df_tmp["sentiment_label"].map(map_sent)
        info_p = LIDERES.get(p, {"lider": "—", "posicion": "—", "ideologia": "—"})

        narr_p = {}
        tema_p = {}
        for _, row in df_tmp.iterrows():
            if row["narrativas"] and row["narrativas"] != "ninguna":
                for n in str(row["narrativas"]).split(","):
                    n = n.strip()
                    if n:
                        narr_p[n] = narr_p.get(n, 0) + 1
            if row["temas"]:
                for t in str(row["temas"]).split(","):
                    t = t.strip()
                    if t:
                        tema_p[t] = tema_p.get(t, 0) + 1

        sent_m = df_tmp["sent_score"].mean()
        narr_top3 = sorted(narr_p.items(), key=lambda x: -x[1])[:3]
        temas_top3 = sorted(tema_p.items(), key=lambda x: -x[1])[:3]

        narr_str = ", ".join([f"**{n}**" for n, _ in narr_top3]) if narr_top3 else "sin narrativas detectadas"
        temas_str = ", ".join([f"{t}" for t, _ in temas_top3]) if temas_top3 else "—"
        sent_str = "🟢 positivo" if sent_m > 0.1 else ("🔴 negativo" if sent_m < -0.1 else "🟡 neutro")

        perfil_narr = ""
        for n, _ in narr_top3:
            p_info = NARRATIVA_PERFIL.get(n, {})
            if p_info.get("desc"):
                perfil_narr += f"\n  - _{p_info['desc']}_"

        with st.expander(f"**{p}** — {info_p['lider']} ({info_p['ideologia']})"):
            st.markdown(f"""
**Posición institucional:** {info_p['posicion']}
**Sentimiento mediático:** {sent_str} ({sent_m:.2f})
**Temas principales:** {temas_str}
**Narrativas dominantes:** {narr_str}
{perfil_narr}

> _Análisis inferido automáticamente desde {len(df_tmp):,} noticias indexadas._
""")

    st.markdown("---")
    st.caption("SIEG – Inteligencia Narrativa · Análisis OSINT automatizado · M. Castillo")

# =========================================================
# TAB 5 — GUÍA DE USO
# © 2026 M. Castillo · mybloggingnotes@gmail.com
#
# INTEGRACIÓN:
# 1. En st.tabs() añadir "📖 Guía de uso" como último elemento
# 2. Añadir tab5 a la asignación:
#    tab1, tab2, tab3, tab4, tab5 = st.tabs([...])
# 3. Pegar este bloque al final de app_dashboard.py
# =========================================================

with tab5:

    st.markdown("""
<div style='padding: 0.4rem 0 1.2rem 0'>
    <div style='font-size:0.75rem; font-weight:600; letter-spacing:0.1em;
                text-transform:uppercase; opacity:0.45; margin-bottom:4px'>
        Documentación del sistema
    </div>
    <div style='font-size:1.5rem; font-weight:700'>Guía de uso · SIEG Centro OSINT</div>
    <div style='font-size:0.85rem; opacity:0.45; margin-top:4px'>
        Versión 3.0 · © 2026 M. Castillo ·
        <a href='mailto:mybloggingnotes@gmail.com'>mybloggingnotes@gmail.com</a>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── ¿Qué es SIEG? ────────────────────────────────────────
    with st.expander("🛰️ ¿Qué es SIEG – Centro OSINT Política Nacional?", expanded=True):
        st.markdown("""
**SIEG** (Sistema de Inteligencia y Evaluación Geopolítica) es una plataforma de
**vigilancia narrativa automatizada** centrada en la política nacional española.

Monitoriza en tiempo real la cobertura mediática de los principales partidos políticos
a través de fuentes RSS de medios nacionales, autonómicos y locales, aplicando
análisis de sentimiento, detección de narrativas y clasificación temática automática.

**El sistema NO es:**
- Una herramienta de propaganda ni de manipulación informativa.
- Un oráculo: los indicadores son estadísticos y aproximados, no deterministas.
- Un sustituto del análisis humano experto.

**El sistema SÍ es:**
- Una herramienta OSINT para detección temprana de tendencias narrativas,
  cambios en el discurso político mediático y evolución del sentimiento por partido.
""")

    # ── Arquitectura ─────────────────────────────────────────
    with st.expander("⚙️ Arquitectura del sistema"):
        st.markdown("""
El sistema corre íntegramente sobre un **Odroid C2** con DietPi Linux,
sin dependencias de servicios en la nube.

```
RSS Feeds (medios nacionales, autonómicos, locales)
      │
      ▼
fetch_rss.py            ← Descarga y normaliza noticias
      │
      ▼
process_nlp.py          ← Análisis de sentimiento (TextBlob / RoBERTa-ES)
      │
      ▼
normalize_partidos.py   ← Asigna partido (keywords + líderes + alias)
      │
      ▼
detect_narrativas.py    ← Clasifica narrativas activas
detect_tendencias.py    ← Calcula tendencias diarias
detect_territorios.py   ← Asigna territorio y coordenadas
      │
      ▼
noticias.db (SQLite)    ← Base de datos local · retención 30 días
      │
      ▼
app_dashboard.py        ← Este dashboard (Streamlit)
```

**Hardware:** Odroid C2 · 1GB RAM · DietPi Linux
**Retención activa:** 30 días (optimizado para el hardware)
**Deduplicación:** hash MD5 por source + title + published
""")

    # ── Descripción de paneles ────────────────────────────────
    with st.expander("📊 Descripción de los paneles"):
        st.markdown("""
| Panel | Contenido principal |
|-------|---------------------|
| **📊 Análisis General** | KPIs globales, alertas de negatividad adaptativas, volumen por partido, balance de sentimiento, cobertura por fuente, presencia territorial, coocurrencias y monitor de BD |
| **📈 Tendencias & Narrativas** | Evolución temporal de temas y narrativas, ranking diario, alertas automáticas de picos de actividad |
| **🗺️ Tendencias por Territorio** | Análisis geográfico por comunidad autónoma: qué temas y narrativas dominan en cada territorio |
| **🧭 Inteligencia Narrativa** | Análisis profundo por partido: ficha del líder, KPIs narrativos, rotación histórica, mapa de calor partido×narrativa, posicionamiento inferido |
| **📖 Guía de uso** | Esta documentación |
""")

    # ── Filtros del sidebar ───────────────────────────────────
    with st.expander("🎛️ Cómo usar los filtros"):
        st.markdown("""
Los filtros del panel lateral izquierdo afectan al **Tab 1 – Análisis General**.
Los tabs de análisis avanzado (2, 3, 4) tienen sus propios filtros internos.

**Partidos**
Selecciona uno o varios partidos para comparar cobertura y sentimiento.
Por defecto aparecen todos los detectados en el período activo.

**Tipo de fuente**
Filtra por categoría de medio: nacional, autonómico, local, digital, agencia.
Útil para aislar sesgos de cobertura por tipo de medio.

**Rango de fechas**
Limita el análisis a un período concreto dentro de los 30 días disponibles.
Con pocos días, las alertas comparan el último día frente a la media anterior.
Con más de 7 días, las alertas calculan tendencias semanales.

**Sentimientos**
Filtra por POS (positivo), NEG (negativo) o NEU (neutro).
Útil para aislar exclusivamente la cobertura negativa de un partido
o comparar solo cobertura positiva entre partidos.
""")

    # ── Interpretación de indicadores ────────────────────────
    with st.expander("📐 Interpretación de indicadores"):
        st.markdown("""
**Sentimiento medio (escala −1 a 1)**
Promedio del score de sentimiento de todas las noticias del período.
- Cercano a **+1** → cobertura predominantemente positiva
- Cercano a **0** → cobertura neutral o equilibrada
- Cercano a **−1** → cobertura predominantemente negativa

*El modelo léxico tiende a clasificar noticias políticas como NEU por defecto.
Los valores POS/NEG son más informativos que el score medio.*

**Alertas de negatividad**
Comparan el porcentaje de noticias negativas del último día frente
a la media de días anteriores. Umbrales:
- 🔴 Subida > 10 puntos porcentuales → alerta crítica
- 🟠 Subida 4–10 pp → alerta moderada
- 🔵 Bajada > 10 pp → mejora significativa
- 🟢 Variación < ±4 pp → situación estable

**Narrativas detectadas**
Marcos discursivos recurrentes identificados por keywords específicas.
No implican valoración política: son descriptores del discurso mediático.

**Coocurrencias**
Noticias donde aparece más de un partido simultáneamente.
Alta coocurrencia entre dos partidos indica conflicto directo, alianza
o debate mediático compartido entre ambos.

**Rotación narrativa**
Muestra qué narrativas ganan o pierden presencia semana a semana.
Una narrativa que sube bruscamente puede indicar un evento detonador
(escándalo, declaración, sentencia judicial, etc.).
""")

    # ── Mantenimiento ─────────────────────────────────────────
    with st.expander("🔧 Mantenimiento del sistema"):
        st.markdown("""
**Ejecutar el pipeline manualmente:**
```bash
cd ~/SIEG-Politica-Nacional
source venv/bin/activate
bash scripts/run_pipeline.sh
```

**Aplicar limpieza, deduplicación y retención de BD:**
```bash
cd ~/SIEG-Politica-Nacional
source venv/bin/activate
python3 scripts/patch_hash_retention.py
```
*Recomendado ejecutar semanalmente via cron.*

**Añadir al cron para ejecución automática semanal:**
```bash
crontab -e
# Añadir esta línea (cada domingo a las 03:00):
0 3 * * 0 cd ~/SIEG-Politica-Nacional && source venv/bin/activate && python3 scripts/patch_hash_retention.py >> logs/retention.log 2>&1
```

**Verificar estado de la BD:**
```bash
sqlite3 ~/SIEG-Politica-Nacional/data/processed/noticias.db "
SELECT
  COUNT(*) as total,
  COUNT(DISTINCT hash_id) as unicos,
  MIN(DATE(created_at)) as desde,
  MAX(DATE(created_at)) as hasta
FROM noticias_norm;"
```

**Espacio en disco:**
```bash
du -sh ~/SIEG-Politica-Nacional/data/processed/noticias.db
df -h /
```

**Reiniciar el dashboard:**
```bash
pkill -f streamlit
cd ~/SIEG-Politica-Nacional
source venv/bin/activate
nohup streamlit run dashboard/app_dashboard.py --server.port 8501 &
```

**Ver logs del pipeline:**
```bash
tail -50 ~/SIEG-Politica-Nacional/logs/pipeline.log
```
""")

    # ── Fuentes ───────────────────────────────────────────────
    with st.expander("📡 Fuentes monitorizadas"):
        st.markdown("""
El sistema monitoriza feeds RSS clasificados por tipo de medio:

- **Nacionales:** El País, El Mundo, ABC, La Razón, El Confidencial,
  elDiario.es, Público, La Vanguardia, El Periódico, 20minutos y otros.
- **Autonómicos:** medios de Cataluña, País Vasco, Galicia,
  Comunidad Valenciana, Andalucía y otras comunidades.
- **Locales y digitales:** medios regionales y nativos digitales seleccionados.
- **Agencias:** EFE, Europa Press.

La lista completa se gestiona en `config/` del proyecto.
Para añadir o eliminar fuentes, editar la configuración RSS
y reiniciar el pipeline.
""")

    # ── Limitaciones ──────────────────────────────────────────
    with st.expander("⚠️ Limitaciones conocidas"):
        st.markdown("""
- **Sentimiento:** TextBlob tiene limitaciones con el español político.
  Tiende a clasificar como NEU noticias que un humano percibiría como negativas.
  RoBERTa-ES ofrece mayor precisión pero mayor consumo de CPU en Odroid C2.

- **Detección de partidos:** puede producir falsos positivos cuando un partido
  es mencionado en contexto ajeno (noticias internacionales con términos coincidentes).

- **Datos territoriales:** solo disponibles para el subconjunto de noticias
  donde el territorio se detectó con suficiente confianza.

- **Retención:** los 30 días de retención limitan el análisis histórico largo.
  Para estudios comparativos de largo plazo, exportar datos antes de la rotación.

- **Hardware:** el Odroid C2 puede degradar el rendimiento del dashboard
  con más de 500k registros simultáneos en memoria.
""")

    # ── Pie de página ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
<div style='text-align:center; opacity:0.45; font-size:0.78rem; padding: 1rem 0'>
    <strong>SIEG – Sistema de Inteligencia y Evaluación Geopolítica</strong><br>
    Centro OSINT · Vigilancia Narrativa · Política Nacional · España<br>
    © 2026 M. Castillo ·
    <a href='mailto:mybloggingnotes@gmail.com' style='opacity:0.7'>mybloggingnotes@gmail.com</a>
    · Todos los derechos reservados · Uso personal e investigación
</div>
""", unsafe_allow_html=True)
