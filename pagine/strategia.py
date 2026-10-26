import streamlit as st

from boxbox import analisi, dati, grafici

scelta, d = dati.sessione_corrente()
dati.intestazione(scelta, "🛞 Gomme e strategia")

if scelta["tipo"] != "gara":
    st.info("Questa pagina racconta le strategie di gara: scegli una **Gara** o una **Sprint** dal menu a sinistra.")
    st.stop()

nomi = analisi.nomi(d.risultati)
colori = analisi.colori(d.risultati)
ordine = analisi.ordine_piloti(d.risultati, d.giri, "gara")

st.subheader("Chi ha usato quali gomme, e quando")
st.plotly_chart(grafici.grafico_strategie(analisi.strategie(d.giri), ordine, nomi), width="stretch")
st.caption("Ogni barra è una gara, dal primo all'ultimo giro. Ogni colore è un tipo di gomma, e ogni cambio di "
           "colore è una sosta ai box. L'asterisco (*) indica una gomma già usata in precedenza.")

puliti = analisi.giri_puliti(d.giri)
pa = analisi.passo(puliti)

st.subheader("Chi era davvero il più veloce?")
st.markdown("\n".join(f"- {f}" for f in analisi.racconto_passo(pa, nomi, ordine)) or "Dati insufficienti.")

scelti = st.multiselect("Piloti da confrontare", ordine, default=[p for p in ordine if p in set(pa["Driver"])][:6],
                        format_func=lambda x: nomi.get(x, x))
if scelti:
    st.plotly_chart(grafici.grafico_passo(puliti, scelti, nomi, colori), width="stretch")
with st.expander("Come si legge questo grafico?"):
    st.markdown(
        "Ogni puntino è un giro di gara 'normale': abbiamo tolto il primo giro, i giri con sosta ai box e quelli "
        "con Safety Car, perché non dicono nulla sulla velocità vera. **Più i puntini sono in basso, più il pilota "
        "era veloce.** La scatola contiene la metà dei giri più tipici: più è stretta, più il pilota è stato "
        "costante."
    )

st.subheader("Quanto si consumavano le gomme")
frasi = analisi.racconto_degrado(analisi.degrado(puliti), nomi)
if frasi:
    st.markdown("\n".join(f"- {f}" for f in frasi))
    st.caption("Stima semplice: guardiamo quanto si allunga il tempo sul giro man mano che la gomma invecchia. "
               "Visto che intanto la benzina cala e la macchina si alleggerisce, il consumo reale delle gomme è un "
               "po' più alto di così.")
else:
    st.write("Non ci sono abbastanza giri puliti per stimare il consumo delle gomme.")
