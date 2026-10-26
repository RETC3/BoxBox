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

### Windows – PowerShell (il prompt inizia con `PS C:\...`)

```powershell
cd boxbox
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

- Se l'attivazione dà un errore sull'"esecuzione di script disabilitata", lancia una volta sola
  `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, conferma con `S` e riprova.
- Se `python` non viene riconosciuto, usa `py` al posto di `python` (es. `py -m venv .venv`).

### Windows – Prompt dei comandi (cmd, il prompt è `C:\...>`)

```cmd
cd boxbox
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

### Mac e Linux

```bash
cd boxbox
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Se l'ambiente è attivo, all'inizio della riga del terminale compare `(.venv)`.
Le volte successive basta entrare nella cartella, riattivare l'ambiente e lanciare `streamlit run app.py`.

Si apre il browser su `http://localhost:8501`. Il sito mostra le sessioni presenti nell'archivio
(cartella `dati/`): se è vuoto, riempilo come spiegato qui sotto.

## Aggiornare i dati (dopo ogni Gran Premio)

I server della F1 **bloccano le richieste dai server cloud**, compreso Streamlit Community Cloud.
Per questo il sito online non scarica nulla: legge un archivio già pronto nella cartella `dati/`,
che riempi **dal tuo computer** e carichi su GitHub.

Con l'ambiente attivo (`(.venv)` all'inizio della riga):

```
python aggiorna_dati.py
```

Scarica tutte le sessioni concluse della stagione in corso che non sono ancora nell'archivio
(ogni sessione richiede circa 30-90 secondi). Poi in GitHub Desktop fai **Commit to main** e **Push origin**:
il sito online si aggiorna da solo in pochi minuti.

| Comando | Cosa fa |
|---|---|
| `python aggiorna_dati.py --solo-gare` | Solo Gara e Sprint: molto più veloce |
| `python aggiorna_dati.py --anno 2025` | Un'altra stagione (anche più d'una: `--anno 2024 2025`) |
| `python aggiorna_dati.py --gp 19 20` | Solo alcuni Gran Premi (numero del round) |
| `python aggiorna_dati.py --forza` | Riscarica anche le sessioni già presenti |

Puoi interrompere con Ctrl+C quando vuoi: le sessioni già salvate restano, e al giro dopo lo script
riparte da dove si era fermato. Ogni sessione occupa pochi MB nell'archivio.

## Struttura

```
app.py              punto di ingresso: menu laterale e navigazione
aggiorna_dati.py    scarica le sessioni nell'archivio (da lanciare dal tuo computer)
dati/               l'archivio letto dal sito (va caricato su GitHub)
boxbox/
  archivio.py       lettura e scrittura della cartella dati/ (file Parquet)
  scarica.py        scaricamento con FastF1 (usato solo da aggiorna_dati.py)
  dati.py           menu di scelta della sessione e cache per il sito
  nomi.py           nomi italiani di Gran Premi e sessioni
  analisi.py        tutti i calcoli e i testi generati in italiano (non dipende da Streamlit)
  grafici.py        grafici Plotly
  testi.py          formattazione all'italiana (1:23,456), gomme, glossario
pagine/             una pagina per file
tests/              sessione simulata + test di tutte le pagine (python -m pytest tests)
```

`analisi.py` è separato apposta: quando vorrai passare a un sito "vero" (API FastAPI + frontend su misura),
quella logica si riusa così com'è.

## Prossimi passi possibili

1. **Automatizzare l'aggiornamento** dell'archivio (oggi è un comando da lanciare a mano dopo ogni GP).
2. **Confronto su un giro a scelta** (non solo il più veloce) e confronto tra stagioni sulla stessa pista.
3. **Pagina pilota** e **pagina stagione** (classifiche mondiali, andamento punti) con i dati Jolpica.
4. Altri sport, dove esistono dati aperti di qualità.

## Note legali

Progetto amatoriale e non ufficiale, non affiliato con Formula 1, FOM o FIA. I dati provengono dalla
libreria open source [FastF1](https://docs.fastf1.dev). Evita di usare i marchi ufficiali nel nome e nella grafica del sito.
