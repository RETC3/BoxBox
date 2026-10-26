"""Lettura dell'archivio per il sito, con cache in memoria, e il menu di scelta della sessione."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from . import archivio
from .archivio import DatiSessione  # noqa: F401  (comodo da importare da qui)
from .nomi import NOMI_SESSIONI, nome_gp, tipo_sessione


def indice() -> dict[int, list[dict]]:
    # Niente cache: leggere l'elenco richiede pochi millisecondi, e così le sessioni
    # appena scaricate compaiono subito, senza dover riavviare il sito.
    return archivio.indice()


@st.cache_resource(max_entries=12, ttl=3600, show_spinner=False)
def carica(anno: int, rnd: int, nome_sessione: str) -> DatiSessione:
    return archivio.carica(anno, rnd, nome_sessione)


def selettore() -> dict | None:
    """Menu laterale: stagione → Gran Premio → sessione. Salva la scelta in st.session_state."""
    st.header("Cosa vuoi guardare?")
    idx = indice()
    if not idx:
        st.warning("L'archivio dei dati è vuoto. Dal tuo computer lancia `python aggiorna_dati.py` "
                   "e carica la cartella `dati` su GitHub.")
        st.session_state["scelta"] = None
        return None

    anno = st.selectbox("Stagione", sorted(idx, reverse=True), key="anno")
    eventi = {e["round"]: e for e in idx[anno]}
    rounds = list(eventi)
    rnd = st.selectbox("Gran Premio", rounds, index=len(rounds) - 1, key=f"gp_{anno}",
                       format_func=lambda r: f"{r}. {nome_gp(eventi[r]['nome'])}")
    ev = eventi[rnd]
    sess = ev["disponibili"]
    predefinita = sess.index("Race") if "Race" in sess else len(sess) - 1
    nome = st.radio("Sessione", sess, index=predefinita, key=f"sess_{anno}_{rnd}",
                    format_func=lambda s: NOMI_SESSIONI.get(s, s))

    scelta = {
        "anno": anno, "round": rnd, "sessione": nome,
        "sessione_it": NOMI_SESSIONI.get(nome, nome), "tipo": tipo_sessione(nome),
        "evento": nome_gp(ev["nome"]), "luogo": ev.get("luogo", ""),
        "data": pd.Timestamp(ev["data"]).strftime("%d/%m/%Y") if ev.get("data") else "",
    }
    st.session_state["scelta"] = scelta
    return scelta


def sessione_corrente() -> tuple[dict, DatiSessione]:
    scelta = st.session_state.get("scelta")
    if not scelta:
        st.info("👈 Scegli una stagione e un Gran Premio dal menu a sinistra.")
        st.stop()
    try:
        return scelta, carica(scelta["anno"], scelta["round"], scelta["sessione"])
    except Exception as e:
        st.error("Non riesco a leggere i dati di questa sessione dall'archivio. "
                 "Prova a riscaricarla con `python aggiorna_dati.py --forza`.")
        with st.expander("Dettaglio tecnico"):
            st.code(repr(e))
        st.stop()


def intestazione(scelta: dict, titolo: str | None = None):
    st.title(titolo or f"{scelta['evento']} · {scelta['sessione_it']}")
    st.caption(f"{scelta['evento']} {scelta['anno']} · {scelta['sessione_it']} · {scelta['luogo']} · {scelta['data']}")
