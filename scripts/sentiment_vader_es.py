#!/usr/bin/env python3
"""
sentiment_vader_es.py
SIEG – Centro OSINT · Política Nacional

VADER adaptado al español con léxico político ampliado.
Reemplaza TextBlob en process_nlp.py con mayor precisión
para texto político español.

Uso:
    from sentiment_vader_es import analizar_sentimiento
    label, polarity = analizar_sentimiento("El gobierno aprueba la reforma")

Autor : M. Castillo · mybloggingnotes@gmail.com
© 2026 M. Castillo
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ── Léxico político español ───────────────────────────────
# Valores: -4 (muy negativo) a +4 (muy positivo)
LEXICO_ES = {
    # Positivos generales
    "bien": 2.0, "bueno": 2.0, "buena": 2.0, "mejor": 2.5,
    "excelente": 3.0, "logro": 2.5, "éxito": 2.5, "avance": 2.0,
    "acuerdo": 1.5, "apoyo": 1.5, "victoria": 2.5, "ganador": 2.0,
    "positivo": 2.0, "favorable": 1.5, "beneficio": 2.0,
    "aprobado": 1.5, "aprobación": 1.5, "consenso": 2.0,
    "reforma": 1.0, "inversión": 1.5, "crecimiento": 2.0,
    "empleo": 1.5, "recuperación": 2.0, "estabilidad": 1.5,

    # Negativos generales
    "mal": -2.0, "malo": -2.0, "mala": -2.0, "peor": -2.5,
    "fracaso": -2.5, "derrota": -2.5, "perdedor": -2.0,
    "negativo": -2.0, "perjuicio": -2.0, "daño": -2.0,
    "rechazado": -1.5, "rechazo": -1.5, "desacuerdo": -1.5,
    "crisis": -2.5, "problema": -1.5, "conflicto": -2.0,
    "escándalo": -3.0, "polémica": -1.5, "controversia": -1.5,

    # Léxico político negativo
    "corrupción": -3.5, "corrupto": -3.5, "corruptela": -3.5,
    "mentira": -3.0, "mentiroso": -3.0, "engaño": -2.5,
    "fraude": -3.0, "fraudulento": -3.0, "malversación": -3.5,
    "soborno": -3.5, "prevaricación": -3.0, "nepotismo": -3.0,
    "dimisión": -2.0, "dimite": -2.0, "renuncia": -1.5,
    "escisión": -1.5, "ruptura": -2.0, "tensión": -1.5,
    "enfrentamiento": -2.0, "acusación": -2.0, "acusado": -2.0,
    "investigado": -2.0, "imputado": -2.5, "detenido": -2.5,
    "condena": -3.0, "condenado": -3.0, "pena": -2.0,
    "golpe": -3.0, "golpista": -3.5, "traición": -3.0,
    "manipulación": -2.5, "propaganda": -2.0,
    "ilegal": -3.0, "ilegítimo": -2.5, "inconstitucional": -2.5,

    # Léxico político positivo
    "democracia": 2.0, "democrático": 2.0, "libertad": 2.5,
    "justicia": 2.0, "transparencia": 2.5, "honestidad": 2.5,
    "diálogo": 2.0, "negociación": 1.5, "pacto": 1.5,
    "solidaridad": 2.0, "igualdad": 2.0, "derechos": 1.5,
    "prosperidad": 2.5, "bienestar": 2.5, "progreso": 2.0,
    "sanidad": 1.0, "educación": 1.0, "pensiones": 0.5,

    # Narrativas específicas
    "amnistía": -1.5, "independencia": -0.5, "secesión": -2.0,
    "referéndum": -0.5, "procés": -1.5, "lawfare": -2.0,
    "okupas": -2.0, "menas": -1.5, "invasión": -2.5,
    "inseguridad": -2.5, "delincuencia": -2.5, "violencia": -3.0,
    "terrorismo": -3.5, "terrorista": -3.5,

    # Intensificadores
    "muy": 0.5, "extremadamente": 1.0, "absolutamente": 0.5,
    "totalmente": 0.5, "completamente": 0.5, "gravemente": -0.5,
    "supuestamente": -0.3, "presuntamente": -0.3,
}

# Inicializar analizador
_analyzer = SentimentIntensityAnalyzer()

# Añadir léxico español
_analyzer.lexicon.update(LEXICO_ES)


def analizar_sentimiento(texto: str) -> tuple[str, float]:
    """
    Analiza el sentimiento de un texto en español.

    Returns:
        tuple (label, polarity)
        label: 'POS', 'NEG', 'NEU'
        polarity: float entre -1.0 y 1.0
    """
    if not texto or not isinstance(texto, str):
        return "NEU", 0.0

    scores = _analyzer.polarity_scores(texto.lower())
    compound = scores["compound"]

    if compound >= 0.05:
        label = "POS"
    elif compound <= -0.05:
        label = "NEG"
    else:
        label = "NEU"

    return label, round(compound, 4)


def analizar_batch(textos: list[str]) -> list[tuple[str, float]]:
    """Analiza una lista de textos."""
    return [analizar_sentimiento(t) for t in textos]


if __name__ == "__main__":
    # Test
    casos = [
        "El gobierno aprueba una reforma histórica para mejorar las pensiones",
        "Escándalo de corrupción sacude al partido en plena campaña electoral",
        "El Congreso debate la nueva ley de vivienda sin acuerdo entre los grupos",
        "Detenido el alcalde por malversación de fondos públicos",
        "El presidente celebra el crecimiento económico del último trimestre",
        "Tensión en Cataluña tras las declaraciones del presidente de la Generalitat",
        "Acuerdo histórico entre PP y PSOE para renovar el Consejo General del Poder Judicial",
        "VOX acusa al gobierno de amnistía encubierta e ilegal",
    ]

    print("SIEG – Test VADER ES")
    print("=" * 60)
    for texto in casos:
        label, pol = analizar_sentimiento(texto)
        icon = "🟢" if label == "POS" else ("🔴" if label == "NEG" else "🟡")
        print(f"{icon} [{label:3s}] {pol:+.3f} | {texto[:60]}")
