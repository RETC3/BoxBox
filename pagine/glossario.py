import streamlit as st

from boxbox.testi import GLOSSARIO

st.title("📖 Glossario")
st.write("Le parole della Formula 1 spiegate senza giri di parole.")

cerca = st.text_input("Cerca una parola", placeholder="es. undercut")
for termine, spiegazione in GLOSSARIO:
    if cerca and cerca.lower() not in (termine + spiegazione).lower():
        continue
    with st.container(border=True):
        st.markdown(f"**{termine}**  \n{spiegazione}")
