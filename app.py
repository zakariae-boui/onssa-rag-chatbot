"""Assistant ONSSA — Streamlit chat application.

Run: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from onssa_rag import config, llm
from onssa_rag.rag import answer
from onssa_rag.retriever import Retriever

st.set_page_config(page_title="Assistant ONSSA", page_icon="🇲🇦", layout="centered")


@st.cache_resource(show_spinner="Chargement de la base de connaissances…")
def load_retriever() -> Retriever:
    return Retriever()


def startup_checks() -> None:
    """Friendly French errors instead of tracebacks when setup is incomplete."""
    if not (config.INDEX_DIR / "manifest.json").exists():
        st.error(
            "**Base de connaissances introuvable.** Construisez-la d'abord :\n\n"
            "```\npython ingest.py\n```\npuis rechargez cette page."
        )
        st.stop()
    if "ollama_ok" not in st.session_state:
        ok, msg = llm.health()
        if not ok:
            st.error(f"**Ollama n'est pas prêt.** {msg}")
            st.stop()
        st.session_state.ollama_ok = True


def render_sources(sources: list[str]) -> None:
    with st.expander("📄 Sources (site ONSSA)"):
        for url in sources:
            st.markdown(f"- [{url}]({url})")


startup_checks()
try:
    retriever = load_retriever()
except RuntimeError as exc:
    st.error(f"**Index incompatible.** {exc}")
    st.stop()

# --- Sidebar: model info, corpus stats, reset (assignment requirements) ---
with st.sidebar:
    st.title("🇲🇦 Assistant ONSSA")
    st.caption(
        "Chatbot d'assistance basé exclusivement sur le contenu du site officiel "
        "[onssa.gov.ma](https://www.onssa.gov.ma/)."
    )
    manifest = retriever.manifest
    st.markdown(f"**Modèle LLM :** `{config.OLLAMA_MODEL}`")
    st.markdown(f"**Embeddings :** `{manifest['embedding_model'].split('/')[-1]}`")
    col1, col2 = st.columns(2)
    col1.metric("Pages indexées", manifest["n_pages"])
    col2.metric("Chunks", manifest["n_chunks"])
    if st.button("🔄 Réinitialiser la conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption(
        "Les réponses sont générées automatiquement à partir du contenu publié par "
        "l'ONSSA ; elles ne constituent ni un avis officiel, ni un conseil juridique, "
        "médical ou vétérinaire."
    )

# --- Conversation ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown(
        "##### 👋 Bienvenue !\n"
        "Posez vos questions sur l'ONSSA : missions, organisation, métiers, "
        "réglementation, e-services, contacts et démarches."
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            render_sources(msg["sources"])

if question := st.chat_input("Posez votre question sur l'ONSSA…"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]
        with st.spinner("Recherche dans le contenu du site de l'ONSSA…"):
            result = answer(question, history, retriever)
        if result.grounded:
            text = st.write_stream(result.stream)
        else:
            st.markdown(result.text)
            text = result.text
        if result.sources:
            render_sources(result.sources)

    st.session_state.messages.append(
        {"role": "assistant", "content": text, "sources": result.sources}
    )
