"""Scarica le sessioni di F1 e le salva nella cartella `dati/`, che il sito legge.

Va lanciato DAL TUO COMPUTER (i server della F1 bloccano i server cloud come Streamlit).
Dopo, carica la cartella `dati` su GitHub (commit + push) e il sito online si aggiorna.

Esempi:
    python aggiorna_dati.py                    tutte le sessioni concluse della stagione in corso
    python aggiorna_dati.py --anno 2025        un'altra stagione
    python aggiorna_dati.py --gp 19 20         solo alcuni Gran Premi (numero del round)
    python aggiorna_dati.py --solo-gare        solo Gara e Sprint (molto più veloce)
    python aggiorna_dati.py --forza            riscarica anche le sessioni già presenti

Le sessioni già scaricate vengono saltate: puoi interrompere con Ctrl+C e riprendere quando vuoi.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent
sys.path.insert(0, str(RADICE))

import fastf1  # noqa: E402
import pandas as pd  # noqa: E402

from boxbox import archivio, scarica  # noqa: E402
from boxbox.nomi import NOMI_SESSIONI, nome_gp  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Aggiorna l'archivio dei dati F1 del sito.")
    p.add_argument("--anno", type=int, nargs="+", default=[dt.date.today().year], help="stagione/i")
    p.add_argument("--gp", type=int, nargs="+", help="solo questi round (es. --gp 19 20)")
    p.add_argument("--solo-gare", action="store_true", help="solo Gara e Sprint")
    p.add_argument("--forza", action="store_true", help="riscarica le sessioni già presenti")
    p.add_argument("--tieni-cache", action="store_true",
                   help="non cancellare i dati grezzi di FastF1 dopo ogni sessione (occupano parecchi GB)")
    a = p.parse_args()

    cache = RADICE / "cache"
    cache.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(cache))
    fastf1.set_log_level("ERROR")

    nuove = saltate = errori = 0
    for anno in a.anno:
        print(f"\n=== Stagione {anno} ===")
        try:
            cal = fastf1.get_event_schedule(anno, include_testing=False)
        except Exception as e:
            print(f"Non riesco a scaricare il calendario {anno}: {e}")
            errori += 1
            continue
        for _, ev in cal.iterrows():
            rnd = int(ev["RoundNumber"])
            if a.gp and rnd not in a.gp:
                continue
            concluse = scarica.sessioni_concluse(ev)
            if not concluse:
                continue
            evento = {
                "nome": ev["EventName"],
                "luogo": f"{ev.get('Location', '')}, {ev.get('Country', '')}",
                "data": pd.Timestamp(ev["EventDate"]).date().isoformat() if pd.notna(ev.get("EventDate")) else "",
                "sessioni": scarica.sessioni_evento(ev),
            }
            for nome in concluse:
                if a.solo_gare and nome not in ("Race", "Sprint"):
                    continue
                if archivio.esiste(anno, rnd, nome) and not a.forza:
                    saltate += 1
                    continue
                print(f"- {rnd:>2}. {nome_gp(ev['EventName'])} · {NOMI_SESSIONI[nome]} ... ", end="", flush=True)
                t0 = time.time()
                try:
                    d = scarica.scarica_sessione(anno, rnd, nome)
                    archivio.salva(d, anno, rnd, nome, evento)
                    print(f"ok ({time.time() - t0:.0f} s)")
                    nuove += 1
                except KeyboardInterrupt:
                    print("interrotto.")
                    return 1
                except Exception as e:
                    print(f"saltata: {e}")
                    errori += 1
                finally:
                    if not a.tieni_cache:
                        try:
                            fastf1.Cache.clear_cache(str(cache), deep=True)
                        except Exception:
                            pass

    print(f"\nFatto: {nuove} sessioni nuove, {saltate} già presenti, {errori} con problemi.")
    if nuove:
        print("Ora carica le modifiche su GitHub (GitHub Desktop: Commit to main, poi Push origin) "
              "e il sito online si aggiornerà da solo.")
    if errori and not nuove:
        print("Se falliscono tutte, controlla la connessione: questo script deve girare dal tuo computer, "
              "non da un server cloud.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrotto. Le sessioni già salvate restano nell'archivio.")
        sys.exit(1)
