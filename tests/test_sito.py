"""Prova tutte le pagine con una sessione simulata, passando dall'archivio.   Avvio:  python -m pytest tests"""
import sys
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from boxbox import analisi, archivio  # noqa: E402
from tests import finto  # noqa: E402

SESSIONI = ["Practice 1", "Qualifying", "Race"]


@pytest.fixture(autouse=True)
def archivio_finto(tmp_path, monkeypatch):
    monkeypatch.setattr(archivio, "CARTELLA", tmp_path)
    for s in SESSIONI:
        archivio.salva(finto.carica(2026, 1, s), 2026, 1, s, finto.EVENTO)
    st.cache_data.clear()
    st.cache_resource.clear()
    monkeypatch.chdir(RADICE)


def _senza_errori(at):
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def test_indice():
    idx = archivio.indice()
    assert list(idx) == [2026]
    assert idx[2026][0]["disponibili"] == SESSIONI  # nell'ordine del weekend


def test_andata_e_ritorno():
    """Quello che salviamo deve tornare indietro uguale (nei valori che il sito usa)."""
    orig, letto = finto.carica(2026, 1, "Race"), archivio.carica(2026, 1, "Race")
    pd.testing.assert_series_equal(orig.giri["LapTime"], letto.giri["LapTime"], check_names=False)
    assert set(letto.telemetrie) == set(orig.telemetrie)
    ta, tel = letto.telemetria_giro_veloce("AAA")
    assert abs(ta - orig.telemetria_giro_veloce("AAA")[0]) < 1e-9
    assert len(tel) == len(orig.telemetria_giro_veloce("AAA")[1])
    assert letto.curve is not None and letto.rotazione == 30.0


@pytest.mark.parametrize("pagina", ["pagine/riepilogo.py", "pagine/sfida.py", "pagine/strategia.py",
                                    "pagine/glossario.py"])
def test_pagine_gara(pagina):
    at = AppTest.from_file(str(RADICE / "app.py"), default_timeout=60)
    at.run()
    at.switch_page(pagina)
    at.run()
    _senza_errori(at)


@pytest.mark.parametrize("sessione", ["Qualifying", "Practice 1"])
def test_altre_sessioni(sessione):
    at = AppTest.from_file(str(RADICE / "app.py"), default_timeout=60)
    at.run()
    at.radio[0].set_value(sessione).run()
    for pagina in ["pagine/riepilogo.py", "pagine/sfida.py", "pagine/strategia.py"]:
        at.switch_page(pagina)
        at.run()
        _senza_errori(at)


def test_archivio_vuoto(tmp_path, monkeypatch):
    monkeypatch.setattr(archivio, "CARTELLA", tmp_path / "vuota")
    st.cache_data.clear()
    at = AppTest.from_file(str(RADICE / "app.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert any("archivio" in w.value for w in at.sidebar.warning)


def test_racconto_sfida_sensato():
    s = archivio.carica(2026, 1, "Race")
    ta, tel_a = s.telemetria_giro_veloce("AAA")
    tb, tel_b = s.telemetria_giro_veloce("BBB")
    df = analisi.allinea(tel_a, tel_b)
    zn = analisi.zone(df, s.curve)
    assert abs(df["Delta"].iloc[-1] - (tb - ta)) < 0.05
    assert abs(zn["Guadagno_A"].sum() - df["Delta"].iloc[-1]) < 0.02
    testo = " ".join(analisi.racconto_sfida(df, zn, "AAA", "BBB", "Mario Rossi", "Luca Bianchi", ta, tb))
    assert "Mario Rossi" in testo and "frena" in testo
