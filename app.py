"""Box Box – la Formula 1 spiegata semplice.

Avvio:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Box Box · la F1 spiegata semplice", page_icon="🏁", layout="wide")

from boxbox import dati  # noqa: E402

pagine = st.navigation([
    st.Page("pagine/riepilogo.py", title="Com'è andata", icon="🏁", default=True),
    st.Page("pagine/sfida.py", title="Sfida tra piloti", icon="⚔️"),
    st.Page("pagine/strategia.py", title="Gomme e strategia", icon="🛞"),
    st.Page("pagine/glossario.py", title="Glossario", icon="📖"),
])

with st.sidebar:
    dati.selettore()
    st.divider()
    st.caption("Sito amatoriale e non ufficiale, non affiliato con Formula 1, FOM o FIA. "
               "Dati ottenuti tramite la libreria open source FastF1.")

pagine.run()
