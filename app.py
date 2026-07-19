"""Assistant ONSSA — Streamlit chat application (implemented in Phase 4).

Run: streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="Assistant ONSSA", page_icon="🇲🇦")

st.title("🇲🇦 Assistant ONSSA")
st.info(
    "L'application de chat sera disponible en Phase 4 — voir PROJECT_PLAN.md.\n\n"
    "Commencez par construire la base de connaissances : `python ingest.py`."
)
