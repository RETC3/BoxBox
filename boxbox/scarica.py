"""Scarica le sessioni con FastF1. Si usa SOLO dal proprio computer, tramite aggiorna_dati.py.

(I server della F1 rifiutano le richieste dai server cloud come Streamlit Community Cloud.)
"""
from __future__ import annotations

import gc

import fastf1
import pandas as pd

from .archivio import DatiSessione
from .nomi import NOMI_SESSIONI

_COLONNE_TEL = ["Distance", "Time", "Speed", "Throttle", "Brake", "nGear", "X", "Y"]


def _utc_naive(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_convert("UTC").tz_localize(None) if t.tzinfo else t


def sessioni_evento(evento: pd.Series) -> list[str]:
    """Tutte le sessioni del weekend, nell'ordine in cui si corrono."""
    return [evento.get(f"Session{i}") for i in range(1, 6) if evento.get(f"Session{i}") in NOMI_SESSIONI]


def sessioni_concluse(evento: pd.Series) -> list[str]:
    adesso = pd.Timestamp.now(tz="UTC").tz_localize(None)
    out = []
    for i in range(1, 6):
        nome, data = evento.get(f"Session{i}"), evento.get(f"Session{i}DateUtc")
        if nome in NOMI_SESSIONI and pd.notna(data) and _utc_naive(data) + pd.Timedelta(hours=1) < adesso:
            out.append(nome)
    return out


def _telemetrie_giri_veloci(s) -> dict:
    """Solo la telemetria dei giri più veloci: pochi MB invece delle centinaia della sessione intera."""
    out = {}
    for pilota in s.laps["Driver"].dropna().unique():
        try:
            giro = s.laps.pick_drivers(pilota).pick_fastest()
            if giro is None or pd.isna(giro["LapTime"]):
                continue
            tel = pd.DataFrame(giro.get_telemetry())
            out[pilota] = (giro["LapTime"].total_seconds(),
                           tel[[c for c in _COLONNE_TEL if c in tel]].reset_index(drop=True))
        except Exception:
            continue  # pilota senza telemetria valida: lo saltiamo
    return out


def scarica_sessione(anno: int, rnd: int, nome_sessione: str) -> DatiSessione:
    s = fastf1.get_session(anno, rnd, nome_sessione)
    s.load(laps=True, telemetry=True, weather=True, messages=True)
    try:
        giri = pd.DataFrame(s.laps)
    except fastf1.exceptions.DataNotLoadedError:
        raise RuntimeError("i server F1 non hanno restituito i dati (sessione appena finita "
                           "o rete che blocca livetiming.formula1.com)") from None
    if giri.empty:
        raise RuntimeError("nessun giro disponibile")
    try:
        info = s.get_circuit_info()
        curve, rotazione = pd.DataFrame(info.corners), float(info.rotation)
    except Exception:
        curve, rotazione = None, 0.0
    meteo = pd.DataFrame(s.weather_data) if s.weather_data is not None else pd.DataFrame()
    dati = DatiSessione(pd.DataFrame(s.results), giri, meteo, curve, rotazione, _telemetrie_giri_veloci(s))
    del s
    gc.collect()
    return dati
