import streamlit as st

from boxbox import analisi, dati, grafici
from boxbox.testi import fmt_num, fmt_secondi, fmt_tempo

scelta, d = dati.sessione_corrente()
dati.intestazione(scelta, "⚔️ Sfida tra piloti")
st.write("Scegli due piloti: mettiamo a confronto il loro **giro più veloce**, metro per metro, "
         "e ti spieghiamo in parole semplici dove e perché uno è andato più forte dell'altro.")

nomi = analisi.nomi(d.risultati)
colori = analisi.colori(d.risultati)
ordine = analisi.ordine_piloti(d.risultati, d.giri, scelta["tipo"])
if len(ordine) < 2:
    st.warning("In questa sessione non ci sono abbastanza piloti con giri validi.")
    st.stop()

c1, c2 = st.columns(2)
a = c1.selectbox("Primo pilota", ordine, index=0, format_func=lambda x: nomi.get(x, x))
b = c2.selectbox("Secondo pilota", ordine, index=1, format_func=lambda x: nomi.get(x, x))
if a == b:
    st.warning("Scegli due piloti diversi.")
    st.stop()

with st.spinner("Confronto le telemetrie…"):
    ga, gb = d.telemetria_giro_veloce(a), d.telemetria_giro_veloce(b)
if ga is None or gb is None:
    manca = nomi.get(a if ga is None else b)
    st.warning(f"Non c'è un giro valido con telemetria per {manca} in questa sessione.")
    st.stop()

(tempo_a, tel_a), (tempo_b, tel_b) = ga, gb
na, nb = nomi.get(a, a), nomi.get(b, b)
ca, cb = colori.get(a, "#e10600"), colori.get(b, "#1e88e5")

df = analisi.allinea(tel_a, tel_b)
zn = analisi.zone(df, d.curve)

m1, m2, m3 = st.columns(3)
m1.metric(na, fmt_tempo(tempo_a))
m2.metric(nb, fmt_tempo(tempo_b))
diff = tempo_b - tempo_a
m3.metric("Differenza", fmt_secondi(abs(diff)),
          f"a favore di {(na if diff > 0 else nb).split()[-1]}" if abs(diff) >= 0.0005 else "pari", delta_color="off")

st.subheader("Il confronto in parole semplici")
st.markdown("\n".join(f"- {f}" for f in analisi.racconto_sfida(df, zn, a, b, na, nb, tempo_a, tempo_b)))

st.subheader("Dove è più veloce ciascuno")
mappa = grafici.mappa_vantaggi(df, zn, na, nb, ca, cb, d.curve, d.rotazione)
if mappa is not None:
    st.plotly_chart(mappa, width="stretch")
    st.caption("Ogni tratto della pista ha il colore del pilota più veloce lì. "
               "Passa il mouse sopra un tratto per vedere quanto tempo ha guadagnato.")

st.subheader("La telemetria completa")
st.plotly_chart(grafici.confronto_telemetria(df, na, nb, ca, cb, d.curve), width="stretch")
with st.expander("Come si legge questo grafico?", expanded=False):
    st.markdown(f"""
Tutti i grafici hanno in orizzontale **i metri percorsi** dalla linea del traguardo, e le linee tratteggiate
grigie segnano le curve (C1, C2…). Così puoi seguire il giro da sinistra a destra come se fossi in macchina.

- **Distacco**: la parte più importante. Se l'area colorata sta **sopra lo zero**, in quel punto è davanti
  {na.split()[-1]}; **sotto lo zero** è davanti {nb.split()[-1]}. Dove la linea sale o scende di colpo,
  lì si è decisa la sfida.
- **Velocità**: le "valli" sono le curve, le "colline" i rettilinei. Una valle meno profonda vuol dire che
  il pilota è passato più veloce in curva.
- **Acceleratore**: 100% è il piede a tavoletta. Chi torna prima sul 100% dopo una curva "esce meglio".
- **Freno**: quando la linea è su "sì" il pilota sta frenando. Chi frena più a destra (più tardi) prima di una
  curva sta osando di più.
- **Marcia**: la marcia inserita, dalla 1ª all'8ª.
""")

with st.expander("Tabella curva per curva"):
    tab = zn.assign(
        **{"Più veloce": zn["Guadagno_A"].map(lambda g: (na if g > 0 else nb).split()[-1]),
           "Vantaggio": zn["Guadagno_A"].abs().map(fmt_secondi),
           f"Vel. minima {na.split()[-1]}": zn["VMin_A"].map(lambda v: f"{fmt_num(v)} km/h"),
           f"Vel. minima {nb.split()[-1]}": zn["VMin_B"].map(lambda v: f"{fmt_num(v)} km/h")}
    )[["Zona", "Più veloce", "Vantaggio", f"Vel. minima {na.split()[-1]}", f"Vel. minima {nb.split()[-1]}"]]
    st.dataframe(tab, hide_index=True, width="stretch")
