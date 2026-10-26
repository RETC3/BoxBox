"""Scarica i dati tramite FastF1 e li tiene in cache (su disco e in memoria)."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

import fastf1
import pandas as pd
import streamlit as st

CARTELLA_CACHE = Path(__file__).resolve().parent.parent / "cache"
CARTELLA_CACHE.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(CARTELLA_CACHE))
fastf1.set_log_level("WARNING")

PRIMO_ANNO = 2018  # da qui in poi FastF1 ha la telemetria completa

NOMI_SESSIONI = {
    "Practice 1": "Prove Libere 1", "Practice 2": "Prove Libere 2", "Practice 3": "Prove Libere 3",
    "Qualifying": "Qualifiche", "Sprint Qualifying": "Qualifiche Sprint", "Sprint Shootout": "Qualifiche Sprint",
    "Sprint": "Sprint", "Race": "Gara",
}

NOMI_GP = {
    "Australian Grand Prix": "GP d'Australia", "Chinese Grand Prix": "GP di Cina",
    "Japanese Grand Prix": "GP del Giappone", "Bahrain Grand Prix": "GP del Bahrain",
    "Saudi Arabian Grand Prix": "GP dell'Arabia Saudita", "Miami Grand Prix": "GP di Miami",
    "Emilia Romagna Grand Prix": "GP dell'Emilia-Romagna", "Monaco Grand Prix": "GP di Monaco",
    "Spanish Grand Prix": "GP di Spagna", "Barcelona-Catalunya Grand Prix": "GP di Barcellona-Catalogna",
    "Canadian Grand Prix": "GP del Canada", "Austrian Grand Prix": "GP d'Austria",
    "British Grand Prix": "GP di Gran Bretagna", "Belgian Grand Prix": "GP del Belgio",
    "Hungarian Grand Prix": "GP d'Ungheria", "Dutch Grand Prix": "GP d'Olanda",
    "Italian Grand Prix": "GP d'Italia", "Azerbaijan Grand Prix": "GP dell'Azerbaigian",
    "Singapore Grand Prix": "GP di Singapore", "United States Grand Prix": "GP degli Stati Uniti",
    "Mexico City Grand Prix": "GP di Città del Messico", "Mexican Grand Prix": "GP del Messico",
    "São Paulo Grand Prix": "GP di San Paolo", "Brazilian Grand Prix": "GP del Brasile",
    "Las Vegas Grand Prix": "GP di Las Vegas", "Qatar Grand Prix": "GP del Qatar",
    "Abu Dhabi Grand Prix": "GP di Abu Dhabi", "French Grand Prix": "GP di Francia",
    "German Grand Prix": "GP di Germania", "Russian Grand Prix": "GP di Russia",
    "Portuguese Grand Prix": "GP del Portogallo", "Turkish Grand Prix": "GP di Turchia",
    "Tuscan Grand Prix": "GP della Toscana", "Styrian Grand Prix": "GP di Stiria",
    "70th Anniversary Grand Prix": "GP del 70° Anniversario", "Eifel Grand Prix": "GP dell'Eifel",
    "Sakhir Grand Prix": "GP di Sakhir", "Madrid Grand Prix": "GP di Madrid",
}


def nome_gp(nome_en: str) -> str:
    return NOMI_GP.get(nome_en, nome_en)


def tipo_sessione(nome: str) -> str:
    if nome in ("Race", "Sprint"):
        return "gara"
    if nome in ("Qualifying", "Sprint Qualifying", "Sprint Shootout"):
        return "qualifica"
    return "prove"


# --------------------------------------------------------------------------- caricamento


@dataclass
class DatiSessione:
    """Tutto quello che serve alle pagine, come DataFrame pandas semplici."""
    risultati: pd.DataFrame
    giri: pd.DataFrame
    meteo: pd.DataFrame
    curve: pd.DataFrame | None
    rotazione: float
    sessione: object = None  # oggetto FastF1 originale
    _tel: dict = field(default_factory=dict, repr=False)

    def telemetria_giro_veloce(self, pilota: str) -> tuple[float, pd.DataFrame] | None:
        """(tempo in secondi, telemetria) del giro più veloce di un pilota."""
        if pilota not in self._tel:
            giro = self.sessione.laps.pick_drivers(pilota).pick_fastest()
            if giro is None or pd.isna(giro["LapTime"]):
                self._tel[pilota] = None
            else:
                self._tel[pilota] = (giro["LapTime"].total_seconds(), pd.DataFrame(giro.get_telemetry()))
        return self._tel[pilota]


@st.cache_data(ttl=3600, show_spinner=False)
def calendario(anno: int) -> pd.DataFrame:
    return pd.DataFrame(fastf1.get_event_schedule(anno, include_testing=False))


@st.cache_resource(max_entries=4, show_spinner=False)
def carica(anno: int, round_: int, nome_sessione: str) -> DatiSessione:
    s = fastf1.get_session(anno, round_, nome_sessione)
    s.load(laps=True, telemetry=True, weather=True, messages=True)
    giri = pd.DataFrame(s.laps)
    if giri.empty:
        raise RuntimeError("nessun giro disponibile per questa sessione")
    try:
        info = s.get_circuit_info()
        curve, rotazione = pd.DataFrame(info.corners), float(info.rotation)
    except Exception:
        curve, rotazione = None, 0.0
    meteo = pd.DataFrame(s.weather_data) if s.weather_data is not None else pd.DataFrame()
    return DatiSessione(pd.DataFrame(s.results), giri, meteo, curve, rotazione, s)


def _utc_naive(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_convert("UTC").tz_localize(None) if t.tzinfo else t


def sessioni_concluse(evento: pd.Series) -> list[str]:
    adesso = pd.Timestamp.now(tz="UTC").tz_localize(None)
    out = []
    for i in range(1, 6):
        nome, data = evento.get(f"Session{i}"), evento.get(f"Session{i}DateUtc")
        if isinstance(nome, str) and nome in NOMI_SESSIONI and pd.notna(data):
            if _utc_naive(data) + pd.Timedelta(hours=1) < adesso:
                out.append(nome)
    return out


# --------------------------------------------------------------------------- interfaccia


def selettore() -> dict | None:
    """Menu laterale: stagione → Gran Premio → sessione. Salva la scelta in st.session_state."""
    st.header("Cosa vuoi guardare?")
    anni = list(range(dt.date.today().year, PRIMO_ANNO - 1, -1))
    anno = st.selectbox("Stagione", anni, key="anno")
    try:
        cal = calendario(anno)
    except Exception:
        st.error("Non riesco a scaricare il calendario. Controlla la connessione e riprova.")
        st.session_state["scelta"] = None
        return None

    eventi = {}
    for _, ev in cal.iterrows():
        sess = sessioni_concluse(ev)
        if sess:
            eventi[int(ev["RoundNumber"])] = (ev, sess)
    if not eventi:
        st.info("Questa stagione non è ancora cominciata.")
        st.session_state["scelta"] = None
        return None

    rounds = list(eventi)
    rnd = st.selectbox("Gran Premio", rounds, index=len(rounds) - 1, key=f"gp_{anno}",
                       format_func=lambda r: f"{r}. {nome_gp(eventi[r][0]['EventName'])}")
    ev, sess = eventi[rnd]
    predefinita = sess.index("Race") if "Race" in sess else len(sess) - 1
    nome = st.radio("Sessione", sess, index=predefinita, key=f"sess_{anno}_{rnd}",
                    format_func=lambda s: NOMI_SESSIONI.get(s, s))

    scelta = {
        "anno": anno, "round": rnd, "sessione": nome,
        "sessione_it": NOMI_SESSIONI.get(nome, nome), "tipo": tipo_sessione(nome),
        "evento": nome_gp(ev["EventName"]), "luogo": f"{ev.get('Location', '')}, {ev.get('Country', '')}",
        "data": pd.Timestamp(ev["EventDate"]).strftime("%d/%m/%Y") if pd.notna(ev.get("EventDate")) else "",
    }
    st.session_state["scelta"] = scelta
    return scelta


def sessione_corrente() -> tuple[dict, DatiSessione]:
    scelta = st.session_state.get("scelta")
    if not scelta:
        st.info("👈 Scegli una stagione e un Gran Premio dal menu a sinistra.")
        st.stop()
    with st.spinner("Sto scaricando i dati della sessione… la prima volta può volerci un minuto, poi è istantaneo."):
        try:
            return scelta, carica(scelta["anno"], scelta["round"], scelta["sessione"])
        except Exception as e:
            st.error(
                "Non riesco a caricare i dati di questa sessione. Succede se è finita da poco "
                "(i dati arrivano circa 30 minuti dopo la bandiera a scacchi) o se manca la connessione. "
                "Riprova tra qualche minuto."
            )
            with st.expander("Dettaglio tecnico"):
                st.code(repr(e))
            st.stop()


def intestazione(scelta: dict, titolo: str | None = None):
    st.title(titolo or f"{scelta['evento']} · {scelta['sessione_it']}")
    st.caption(f"{scelta['evento']} {scelta['anno']} · {scelta['sessione_it']} · {scelta['luogo']} · {scelta['data']}")
