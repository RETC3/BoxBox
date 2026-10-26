"""Una sessione F1 completamente simulata, per provare il sito senza connessione.

I numeri sono inventati: servono solo a verificare che calcoli e pagine funzionino.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from boxbox.archivio import DatiSessione

PILOTI = [  # sigla, nome, squadra, colore, griglia, arrivo
    ("AAA", "Mario Rossi", "Squadra Rossa", "DC0000", 2, "1"),
    ("BBB", "Luca Bianchi", "Squadra Blu", "1E41FF", 1, "2"),
    ("CCC", "Paolo Verdi", "Squadra Rossa", "DC0000", 9, "3"),
    ("DDD", "Anna Neri", "Squadra Verde", "00A19C", 3, "4"),
    ("EEE", "Sara Gialli", "Squadra Blu", "1E41FF", 5, "5"),
    ("FFF", "Gino Viola", "Squadra Verde", "00A19C", 4, "R"),
]
CURVE_DIST = [550, 1150, 1900, 2650, 3350, 4150]
CURVE_VMIN = [95, 180, 240, 120, 210, 150]
LUNGHEZZA = 5000.0


EVENTO = {"nome": "Italian Grand Prix", "luogo": "Monza, Italy", "data": "2026-09-06",
          "sessioni": ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"]}


def telemetria(bravura_curva: float, frenata: float, vmax: float) -> pd.DataFrame:
    d = np.arange(0, LUNGHEZZA, 4.0)
    v = np.full_like(d, vmax)
    for dc, vm in zip(CURVE_DIST, CURVE_VMIN):
        vm = vm + bravura_curva
        prima = vm + 0.55 * np.clip(dc - d + frenata, 0, None)   # frenata
        dopo = vm + 0.18 * np.clip(d - dc, 0, None)              # accelerazione
        v = np.minimum(v, np.where(d < dc, prima, dopo))
    dt = np.diff(d, prepend=0) / (v / 3.6)
    t = np.cumsum(dt)
    dv = np.gradient(v)
    ang = d / LUNGHEZZA * 2 * np.pi
    return pd.DataFrame({
        "Distance": d, "Time": pd.to_timedelta(t, unit="s"), "Speed": v,
        "Throttle": np.where(dv < -0.05, 0, np.where(dv > 0.01, 100, 100)),
        "Brake": dv < -0.05, "nGear": np.clip((v / 42).astype(int) + 1, 1, 8),
        "X": 4000 * np.cos(ang) + 600 * np.cos(3 * ang), "Y": 2500 * np.sin(ang),
    })


TEL = {
    "AAA": telemetria(4, 8, 330), "BBB": telemetria(0, 0, 334), "CCC": telemetria(2, 3, 329),
    "DDD": telemetria(-2, 5, 331), "EEE": telemetria(-1, -4, 332), "FFF": telemetria(-3, 0, 328),
}


def telemetrie() -> dict:
    return {p: (float(t["Time"].iloc[-1].total_seconds()), t) for p, t in TEL.items()}


def risultati() -> pd.DataFrame:
    righe = []
    for i, (sig, nome, sq, col, gr, arr) in enumerate(PILOTI):
        righe.append({
            "Abbreviation": sig, "FullName": nome, "TeamName": sq, "TeamColor": col,
            "Position": float(i + 1), "ClassifiedPosition": arr, "GridPosition": float(gr),
            "Points": [25, 18, 15, 12, 10, 0][i],
            "Q1": pd.Timedelta(seconds=81 + i * 0.1), "Q2": pd.Timedelta(seconds=80.5 + i * 0.1) if i < 5 else pd.NaT,
            "Q3": pd.Timedelta(seconds=80 + i * 0.07) if i < 4 else pd.NaT,
        })
    return pd.DataFrame(righe)


def giri(n_giri: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    righe = []
    for i, (sig, *_rest) in enumerate(PILOTI):
        sosta = 12 + i * 2
        ultimo = 18 if sig == "FFF" else n_giri
        for g in range(1, ultimo + 1):
            stint = 1 if g <= sosta else 2
            vita = g if stint == 1 else g - sosta
            mescola = "MEDIUM" if stint == 1 else "HARD"
            sec = 82 + i * 0.15 + vita * (0.07 if stint == 1 else 0.04) - g * 0.05 + rng.normal(0, 0.15)
            sc = 20 <= g <= 21
            righe.append({
                "Driver": sig, "LapNumber": float(g), "LapTime": pd.Timedelta(seconds=sec + (20 if sc else 0)),
                "Stint": float(stint), "Compound": mescola, "TyreLife": float(vita),
                "PitInTime": pd.Timedelta(seconds=1) if g == sosta else pd.NaT,
                "PitOutTime": pd.Timedelta(seconds=1) if g == sosta + 1 else pd.NaT,
                "TrackStatus": "4" if sc else "1",
                "Position": float(min(len(PILOTI), max(1, i + 1 + (2 if sosta < g < sosta + 4 else 0)))),
            })
    return pd.DataFrame(righe)


def curve() -> pd.DataFrame:
    tel = TEL["AAA"]
    xs = np.interp(CURVE_DIST, tel["Distance"], tel["X"])
    ys = np.interp(CURVE_DIST, tel["Distance"], tel["Y"])
    return pd.DataFrame({"Number": range(1, len(CURVE_DIST) + 1), "Letter": "", "Distance": CURVE_DIST,
                         "X": xs, "Y": ys})


def carica(anno, round_, nome) -> DatiSessione:
    meteo = pd.DataFrame({"AirTemp": [24.0, 25.0], "TrackTemp": [40.0, 42.0], "Rainfall": [False, False]})
    return DatiSessione(risultati(), giri(), meteo, curve(), 30.0, telemetrie())
