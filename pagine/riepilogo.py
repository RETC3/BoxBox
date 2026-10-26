import streamlit as st

from boxbox import analisi, dati, grafici

scelta, d = dati.sessione_corrente()
dati.intestazione(scelta)

meteo = analisi.racconto_meteo(d.meteo)
if meteo:
    st.caption(meteo)

tipo = scelta["tipo"]
nomi = analisi.nomi(d.risultati)
colori = analisi.colori(d.risultati)

st.subheader("In breve")
if tipo == "gara":
    frasi = analisi.racconto_gara(d.risultati, d.giri)
elif tipo == "qualifica":
    frasi = analisi.racconto_qualifica(d.risultati)
else:
    frasi = analisi.racconto_prove(d.giri, d.risultati)
st.markdown("\n".join(f"- {f}" for f in frasi))

st.subheader("Classifica")
if tipo == "gara":
    tabella = analisi.classifica_gara(d.risultati)
elif tipo == "qualifica":
    tabella = analisi.classifica_qualifica(d.risultati)
else:
    tabella = analisi.classifica_prove(d.giri, d.risultati)
st.dataframe(tabella, hide_index=True, width="stretch")

if tipo == "gara":
    st.subheader("Le posizioni giro dopo giro")
    ordine = analisi.ordine_piloti(d.risultati, d.giri, tipo)
    st.plotly_chart(grafici.grafico_posizioni(d.giri, ordine, nomi, colori), width="stretch")
    with st.expander("Come si legge questo grafico?"):
        st.markdown(
            "Ogni linea è un pilota, con il colore della sua squadra (il compagno di squadra è tratteggiato). "
            "In alto c'è chi è in testa. Quando una linea **sale** il pilota sta guadagnando posizioni, "
            "quando **scende** le sta perdendo. I saliscendi improvvisi di solito sono le soste ai box. "
            "Clicca sui nomi nella legenda per nascondere o mostrare un pilota."
        )

st.info("💡 Vuoi capire **dove** un pilota è stato più veloce di un altro? Vai su **Sfida tra piloti** nel menu.")
