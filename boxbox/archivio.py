"""L'archivio dei dati già elaborati, nella cartella `dati/` del progetto.

Il sito legge SOLO da qui: non si collega mai ai server della F1, che bloccano i server cloud.
L'archivio si riempie dal proprio computer con `python aggiorna_dati.py`.

Struttura:
    dati/2026/19/evento.json             nome del GP, luogo, data, ordine delle sessioni
    dati/2026/19/Race/giri.parquet        un file per tabella
    dati/2026/19/Race/sessione.json       scritto per ultimo: se c'è, la sessione è completa
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

CARTELLA = Path(__file__).resolve().parent.parent / "dati"


@dataclass
class DatiSessione:
    """Tutto quello che serve alle pagine, come DataFrame pandas semplici."""
    risultati: pd.DataFrame
    giri: pd.DataFrame
    meteo: pd.DataFrame
    curve: pd.DataFrame | None
    rotazione: float
    # pilota -> (tempo in secondi, telemetria del giro più veloce)
    telemetrie: dict = field(default_factory=dict, repr=False)

    def telemetria_giro_veloce(self, pilota: str) -> tuple[float, pd.DataFrame] | None:
        return self.telemetrie.get(pilota)


# Solo le colonne che il sito usa, con un tipo preciso: file piccoli e sempre leggibili.
SCHEMI = {
    "risultati": {"Abbreviation": "str", "FullName": "str", "TeamName": "str", "TeamColor": "str",
                  "Position": "float", "ClassifiedPosition": "str", "GridPosition": "float",
                  "Points": "float", "Q1": "td", "Q2": "td", "Q3": "td"},
    "giri": {"Driver": "str", "LapNumber": "float", "LapTime": "td", "Stint": "float", "Compound": "str",
             "TyreLife": "float", "PitInTime": "td", "PitOutTime": "td", "TrackStatus": "str",
             "Position": "float"},
    "meteo": {"AirTemp": "float", "TrackTemp": "float", "Rainfall": "bool"},
    "curve": {"Number": "float", "Letter": "str", "Distance": "float", "X": "float", "Y": "float"},
    "telemetria": {"Driver": "str", "Distance": "float", "Time": "td", "Speed": "float", "Throttle": "float",
                   "Brake": "bool", "nGear": "float", "X": "float", "Y": "float"},
}


def _converti(s: pd.Series, tipo: str) -> pd.Series:
    if tipo == "str":
        return s.where(s.notna(), "").astype(str)
    if tipo == "float":
        return pd.to_numeric(s, errors="coerce").astype(float)
    if tipo == "td":
        return pd.to_timedelta(s, errors="coerce")
    try:
        return s.astype("boolean").fillna(False).astype(bool)
    except (TypeError, ValueError):
        return s.fillna(0).astype(bool)


def pulisci(df: pd.DataFrame | None, tabella: str) -> pd.DataFrame:
    df = pd.DataFrame() if df is None else df.reset_index(drop=True)
    return pd.DataFrame({
        col: _converti(df[col] if col in df else pd.Series(np.nan, index=df.index, dtype=object), tipo)
        for col, tipo in SCHEMI[tabella].items()
    })


def cartella_evento(anno: int, rnd: int) -> Path:
    return CARTELLA / str(anno) / f"{int(rnd):02d}"


def cartella_sessione(anno: int, rnd: int, sessione: str) -> Path:
    return cartella_evento(anno, rnd) / sessione.replace(" ", "_")


def esiste(anno: int, rnd: int, sessione: str) -> bool:
    return (cartella_sessione(anno, rnd, sessione) / "sessione.json").exists()


def salva(d: DatiSessione, anno: int, rnd: int, sessione: str, evento: dict) -> None:
    ce = cartella_evento(anno, rnd)
    cs = cartella_sessione(anno, rnd, sessione)
    cs.mkdir(parents=True, exist_ok=True)
    (ce / "evento.json").write_text(json.dumps(evento, ensure_ascii=False, indent=1), encoding="utf-8")

    fine = cs / "sessione.json"
    fine.unlink(missing_ok=True)  # finché non riscriviamo questo file la sessione risulta incompleta

    pulisci(d.risultati, "risultati").to_parquet(cs / "risultati.parquet", index=False)
    pulisci(d.giri, "giri").to_parquet(cs / "giri.parquet", index=False)
    if d.meteo is not None and not d.meteo.empty:
        pulisci(d.meteo, "meteo").to_parquet(cs / "meteo.parquet", index=False)
    if d.curve is not None and not d.curve.empty:
        pulisci(d.curve, "curve").to_parquet(cs / "curve.parquet", index=False)
    tel = [t.assign(Driver=p) for p, (_, t) in d.telemetrie.items()]
    if tel:
        pulisci(pd.concat(tel, ignore_index=True), "telemetria").to_parquet(cs / "telemetria.parquet", index=False)

    info = {"sessione": sessione, "rotazione": float(d.rotazione or 0.0),
            "tempi": {p: float(t) for p, (t, _) in d.telemetrie.items()}}
    fine.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")


def _leggi(cartella: Path, nome: str) -> pd.DataFrame | None:
    f = cartella / f"{nome}.parquet"
    return pd.read_parquet(f) if f.exists() else None


def carica(anno: int, rnd: int, sessione: str) -> DatiSessione:
    cs = cartella_sessione(anno, rnd, sessione)
    info = json.loads((cs / "sessione.json").read_text(encoding="utf-8"))
    tel = _leggi(cs, "telemetria")
    telemetrie = {}
    if tel is not None:
        for p, t in tel.groupby("Driver", sort=False):
            if p in info["tempi"]:
                telemetrie[p] = (info["tempi"][p], t.drop(columns="Driver").reset_index(drop=True))
    meteo = _leggi(cs, "meteo")
    return DatiSessione(_leggi(cs, "risultati"), _leggi(cs, "giri"),
                        meteo if meteo is not None else pd.DataFrame(),
                        _leggi(cs, "curve"), info["rotazione"], telemetrie)


def indice() -> dict[int, list[dict]]:
    """{anno: [evento, ...]} con, per ogni evento, le sessioni presenti nell'archivio."""
    out: dict[int, list[dict]] = {}
    for f in sorted(CARTELLA.glob("*/*/evento.json")):
        ev = json.loads(f.read_text(encoding="utf-8"))
        anno, rnd = int(f.parent.parent.name), int(f.parent.name)
        disponibili = [s for s in ev.get("sessioni", []) if esiste(anno, rnd, s)]
        if disponibili:
            out.setdefault(anno, []).append({**ev, "round": rnd, "disponibili": disponibili})
    for eventi in out.values():
        eventi.sort(key=lambda e: e["round"])
    return out
