"""Prova tutte le pagine con una sessione simulata.   Avvio:  python -m pytest tests"""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from boxbox import analisi, dati  # noqa: E402
from tests import finto  # noqa: E402


@pytest.fixture(autouse=True)
def dati_finti(monkeypatch):
    monkeypatch.setattr(dati, "calendario", finto.calendario)
    monkeypatch.setattr(dati, "carica", finto.carica)
    monkeypatch.chdir(RADICE)


def _senza_errori(at):
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


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


def test_racconto_sfida_sensato():
    s = finto.carica(2026, 1, "Race")
    ta, tel_a = s.telemetria_giro_veloce("AAA")
    tb, tel_b = s.telemetria_giro_veloce("BBB")
    df = analisi.allinea(tel_a, tel_b)
    zn = analisi.zone(df, s.curve)
    # il distacco a fine giro deve coincidere con la differenza dei tempi
    assert abs(df["Delta"].iloc[-1] - (tb - ta)) < 0.05
    # la somma dei guadagni per zona deve tornare con il distacco totale
    assert abs(zn["Guadagno_A"].sum() - df["Delta"].iloc[-1]) < 0.02
    frasi = analisi.racconto_sfida(df, zn, "AAA", "BBB", "Mario Rossi", "Luca Bianchi", ta, tb)
    testo = " ".join(frasi)
    assert "Mario Rossi" in testo and "frena" in testo
