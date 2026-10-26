# 🏁 Box Box – la Formula 1 spiegata semplice

Un sito in italiano che mostra statistiche e telemetria della F1 **spiegate a parole**, pensato per chi
guarda le gare la domenica e non per gli ingegneri. *(Box Box è un nome provvisorio.)*

## Cosa c'è dentro

| Pagina | Cosa fa |
|---|---|
| **Com'è andata** | Riassunto automatico della sessione (vincitore, rimonte, ritiri, giro veloce, strategia più usata), classifica, meteo e grafico delle posizioni giro per giro. Funziona per gara, qualifiche e prove libere. |
| **Sfida tra piloti** | Confronta il giro più veloce di due piloti metro per metro: spiega *dove* uno guadagna e *perché* (frena più tardi, passa più veloce in curva, è più veloce in rettilineo), mappa del circuito colorata, telemetria completa con istruzioni di lettura. |
| **Gomme e strategia** | Strategie di tutti i piloti, passo gara "pulito" (senza soste e Safety Car), chi aveva il passo per arrivare più avanti, consumo delle gomme. |
| **Glossario** | Le parole della F1 spiegate semplici, con ricerca. |

## Avvio

Serve Python 3.10 o più recente.

```bash
cd boxbox
python -m venv .venv
source .venv/bin/activate        # su Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Si apre il browser su `http://localhost:8501`. La prima volta che apri una sessione i dati vengono
scaricati (30-60 secondi); poi restano nella cartella `cache/` e il caricamento è istantaneo.

## Struttura

```
app.py              punto di ingresso: menu laterale e navigazione
boxbox/
  dati.py           scaricamento tramite FastF1, cache, nomi italiani di GP e sessioni
  analisi.py        tutti i calcoli e i testi generati in italiano (non dipende da Streamlit)
  grafici.py        grafici Plotly
  testi.py          formattazione all'italiana (1:23,456), gomme, glossario
pagine/             una pagina per file
tests/              sessione simulata + test di tutte le pagine (python -m pytest tests)
```

`analisi.py` è separato apposta: quando vorrai passare a un sito "vero" (API FastAPI + frontend su misura),
quella logica si riusa così com'è.

## Prossimi passi in programma:

1. **Pubblicarlo**: Pubblicazione su Streamlit Community Cloud.
2. **Precalcolare** i dati dopo ogni GP con un job automatico, così nessun visitatore aspetta il download.
3. **Confronto su un giro a scelta** (non solo il più veloce) e confronto tra stagioni sulla stessa pista.
4. **Pagina pilota** e **pagina stagione** (classifiche mondiali, andamento punti) con i dati Jolpica.
5. Altri sport, dove esistono dati aperti di qualità.

## Note legali

Progetto amatoriale e non ufficiale, non affiliato con Formula 1, FOM o FIA. I dati provengono dalla
libreria open source [FastF1](https://docs.fastf1.dev). Evita di usare i marchi ufficiali nel nome e nella grafica del sito.
