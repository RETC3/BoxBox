"""Formattazione all'italiana, nomi delle gomme e glossario."""
from __future__ import annotations

import math

MESCOLE = {
    "SOFT": ("Morbida", "#DA291C"),
    "MEDIUM": ("Media", "#FFD12E"),
    "HARD": ("Dura", "#E8E8E8"),
    "INTERMEDIATE": ("Intermedia", "#43B02A"),
    "WET": ("Da bagnato", "#0067AD"),
}


def nome_mescola(codice) -> str:
    c = str(codice).upper()
    if c in MESCOLE:
        return MESCOLE[c][0]
    return "Sconosciuta" if c in ("", "NAN", "NONE", "UNKNOWN", "TEST_UNKNOWN") else c.title()


def colore_mescola(codice) -> str:
    return MESCOLE.get(str(codice).upper(), ("", "#9E9E9E"))[1]


def _vuoto(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def fmt_tempo(sec) -> str:
    """92.345 -> '1:32,345'"""
    if _vuoto(sec):
        return "—"
    m = int(sec // 60)
    r = sec - 60 * m
    testo = f"{m}:{r:06.3f}" if m else f"{r:.3f}"
    return testo.replace(".", ",")


def fmt_secondi(sec, segno: bool = False) -> str:
    """0.1234 -> '0,123 s' (con segno: '+0,123 s')"""
    if _vuoto(sec):
        return "—"
    testo = f"{sec:+.3f}" if segno else f"{abs(sec):.3f}"
    return testo.replace(".", ",") + " s"


def fmt_num(x, decimali: int = 0) -> str:
    if _vuoto(x):
        return "—"
    return f"{x:.{decimali}f}".replace(".", ",")


def posizione(n) -> str:
    return "—" if _vuoto(n) else f"{int(n)}°"


GLOSSARIO = [
    ("Telemetria", "I dati che la macchina registra mentre gira: velocità, quanto il pilota preme "
     "l'acceleratore e il freno, la marcia inserita. È come la 'scatola nera' del giro."),
    ("Giro secco", "Il giro più veloce possibile, di solito in qualifica: poca benzina, gomme nuove, "
     "tutto al limite."),
    ("Distacco (o delta)", "Quanto tempo separa due piloti in un certo punto della pista. Nei nostri grafici, "
     "se la linea sale vuol dire che il primo pilota sta guadagnando."),
    ("Punto di frenata", "Il punto in cui il pilota inizia a frenare prima di una curva. Frenare qualche metro "
     "più tardi fa guadagnare tempo, ma se esageri vai lungo."),
    ("Velocità minima in curva", "La velocità nel punto più lento della curva. Chi la tiene più alta di solito "
     "ha una macchina con più aderenza o un pilota più coraggioso."),
    ("Mescola", "Il tipo di gomma. Morbida (rossa): veloce ma si consuma presto. Media (gialla): via di mezzo. "
     "Dura (bianca): più lenta ma dura a lungo. Intermedia (verde) e Da bagnato (blu) per la pioggia."),
    ("Stint", "Il tratto di gara fatto con lo stesso treno di gomme, tra una sosta ai box e l'altra."),
    ("Degrado", "Quanto rallenta una gomma giro dopo giro mentre si consuma. Se una gomma perde 0,1 s a giro, "
     "dopo 20 giri sei 2 secondi più lento."),
    ("Passo gara", "La velocità media di un pilota sui giri 'normali' di gara, senza soste e senza safety car. "
     "Dice chi era davvero veloce, al di là del risultato."),
    ("Undercut", "Fermarsi ai box prima dell'avversario: con le gomme nuove fai giri più veloci e quando lui "
     "si ferma a sua volta gli esci davanti."),
    ("Overcut", "Il contrario dell'undercut: restare fuori più a lungo, sperando che le gomme vecchie reggano "
     "e che l'avversario si trovi nel traffico."),
    ("Safety Car / VSC", "Quando c'è un incidente entra la Safety Car (o la Virtual Safety Car) e tutti devono "
     "rallentare. Fermarsi ai box in quel momento costa meno tempo."),
    ("Pit lane", "La corsia dei box. Partire dalla pit lane vuol dire partire per ultimi, di solito per una "
     "penalità o per modifiche alla macchina."),
    ("Pole position", "Il primo posto in griglia di partenza, conquistato con il giro più veloce in qualifica."),
    ("Q1, Q2, Q3", "Le tre fasi della qualifica. Dopo Q1 e Q2 i più lenti vengono eliminati; in Q3 i migliori "
     "dieci si giocano la pole."),
    ("DRS e aerodinamica attiva", "Fino al 2025 il DRS apriva un'ala posteriore per sorpassare in rettilineo. "
     "Con le regole 2026 le ali si regolano in modo attivo e c'è una modalità sorpasso con più energia elettrica."),
]
