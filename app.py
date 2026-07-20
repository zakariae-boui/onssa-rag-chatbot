"""Assistant ONSSA — Streamlit chat application.

Run: streamlit run app.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import streamlit as st

from onssa_rag import config
from onssa_rag import conversations as convs
from onssa_rag import llm, rag, voice
from onssa_rag.retriever import Retriever

st.set_page_config(page_title="Assistant ONSSA", page_icon="🇲🇦", layout="centered")

LOGO = config.PROJECT_ROOT / "assets" / "onssa-logo.png"

SUGGESTIONS = [
    "Quelles sont les missions de l'ONSSA ?",
    "Comment payer les prestations en ligne ?",
    "Comment contacter l'ONSSA ?",
]


@st.cache_resource(show_spinner="Chargement de la base de connaissances…")
def load_retriever() -> Retriever:
    return Retriever()


@st.cache_resource(show_spinner="Chargement du modèle de transcription (1ʳᵉ fois : ~150 Mo)…")
def load_stt():
    return voice.load_stt()


@st.cache_resource(show_spinner="Chargement de la voix française (1ʳᵉ fois : ~60 Mo)…")
def load_tts():
    return voice.load_tts()


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


def settings() -> dict:
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "model": config.OLLAMA_MODEL,
            "temperature": 0.2,
            "top_k": config.TOP_K,
            "max_context": config.MAX_CONTEXT_CHARS,
        }
    return st.session_state.settings


def active_conv() -> dict:
    if "conv" not in st.session_state:
        st.session_state.conv = convs.create()
    return st.session_state.conv


def log_feedback(conv: dict, index: int, value: int) -> None:
    question = conv["messages"][index - 1]["content"] if index > 0 else ""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "conversation": conv["id"],
        "question": question,
        "rating": "up" if value == 1 else "down",
        "model": settings()["model"],
    }
    with open(config.DATA_DIR / "feedback.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def render_sources(sources: list[str]) -> None:
    with st.expander("📄 Sources (site ONSSA)"):
        for url in sources:
            st.markdown(f"- [{url}]({url})")


def render_assistant_extras(conv: dict, index: int, msg: dict) -> None:
    if msg.get("sources"):
        render_sources(msg["sources"])

    col_fb, col_listen = st.columns([1, 3])
    with col_fb:
        rating = st.feedback("thumbs", key=f"fb_{conv['id']}_{index}")
        if rating is not None and rating != msg.get("feedback"):
            msg["feedback"] = rating
            convs.save(conv)
            log_feedback(conv, index, rating)

    wav_key = f"wav_{conv['id']}_{index}"
    with col_listen:
        if st.button("🔊 Écouter", key=f"tts_{conv['id']}_{index}"):
            try:
                with st.spinner("Synthèse vocale…"):
                    st.session_state[wav_key] = voice.synthesize(
                        load_tts(), voice.clean_for_speech(msg["content"])
                    )
                st.session_state.autoplay = wav_key
            except Exception as exc:
                st.caption(
                    "Synthèse vocale indisponible — vérifiez `pip install piper-tts` "
                    f"et la connexion pour le 1ᵉʳ téléchargement. ({type(exc).__name__})"
                )
    if wav_key in st.session_state:
        st.audio(
            st.session_state[wav_key],
            format="audio/wav",
            autoplay=st.session_state.pop("autoplay", None) == wav_key,
        )


# --- Startup ---
startup_checks()
try:
    retriever = load_retriever()
except RuntimeError as exc:
    st.error(f"**Index incompatible.** {exc}")
    st.stop()

conv = active_conv()
s = settings()
manifest = retriever.manifest

# --- Sidebar ---
with st.sidebar:
    if LOGO.exists():
        st.image(str(LOGO), width="stretch")
    st.title("Assistant ONSSA")

    query = st.text_input(
        "Rechercher", placeholder="🔍 Rechercher une conversation…",
        label_visibility="collapsed",
    )

    if st.button("➕ Nouvelle conversation", width="stretch", type="primary"):
        st.session_state.conv = convs.create()
        st.rerun()

    for saved in convs.search(convs.load_all(), query):
        col_open, col_del = st.columns([5, 1])
        prefix = "🟢 " if saved["id"] == conv["id"] else "💬 "
        if col_open.button(
            prefix + saved["title"], key=f"open_{saved['id']}", width="stretch"
        ):
            st.session_state.conv = saved
            st.rerun()
        if col_del.button("🗑️", key=f"del_{saved['id']}"):
            convs.delete(saved["id"])
            if saved["id"] == conv["id"]:
                st.session_state.conv = convs.create()
            st.rerun()

    st.divider()

    if st.button("🔄 Réinitialiser la conversation", width="stretch"):
        convs.delete(conv["id"])
        st.session_state.conv = convs.create()
        st.rerun()

    # Always visible (assignment requirement: model name + indexed docs)
    st.caption(f"🧠 `{s['model']}` · 📄 {manifest['n_pages']} pages · {manifest['n_chunks']} extraits")

    with st.expander("⚙️ Paramètres"):
        models = llm.available_models() or [s["model"]]
        current = models.index(s["model"]) if s["model"] in models else 0
        s["model"] = st.selectbox("Modèle LLM", models, index=current)
        s["temperature"] = st.slider("Température", 0.0, 1.0, s["temperature"], 0.05)
        s["top_k"] = st.slider("Extraits récupérés (top-k)", 3, 8, s["top_k"])
        s["max_context"] = st.slider(
            "Taille du contexte (caractères)", 2000, 10000, s["max_context"], 1000,
            help="Plus bas = réponses plus rapides ; plus haut = réponses plus complètes.",
        )

    with st.expander("ℹ️ À propos"):
        st.markdown(
            "Assistant basé exclusivement sur le contenu du site officiel "
            "[onssa.gov.ma](https://www.onssa.gov.ma/)."
        )
        st.markdown(f"**Embeddings :** `{manifest['embedding_model'].split('/')[-1]}`")
        col1, col2 = st.columns(2)
        col1.metric("Pages indexées", manifest["n_pages"])
        col2.metric("Extraits", manifest["n_chunks"])

# --- Conversation display ---
if not conv["messages"]:
    st.markdown(
        "##### 👋 Bienvenue !\n"
        "Posez vos questions sur l'ONSSA : missions, organisation, métiers, "
        "réglementation, e-services, contacts et démarches."
    )
    cols = st.columns(len(SUGGESTIONS))
    for col, suggestion in zip(cols, SUGGESTIONS):
        if col.button(suggestion, key=f"sugg_{suggestion[:20]}", width="stretch"):
            st.session_state.pending_question = suggestion
            st.rerun()

for index, msg in enumerate(conv["messages"]):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_assistant_extras(conv, index, msg)

# --- Question handling — compose bar: text input (left) + mic recorder (right) ---
# The recorder is placed directly (no popover) so one click on the mic starts
# recording; a second click stops it and transcription runs automatically.
col_input, col_mic = st.columns([8, 2], vertical_alignment="bottom")
with col_mic:
    audio = st.audio_input(
        "Question vocale", key="voice_input", label_visibility="collapsed",
    )
    if audio is not None:
        digest = hashlib.sha1(audio.getvalue()).hexdigest()
        if st.session_state.get("voice_done") != digest:
            transcript = ""
            try:
                with st.spinner("Transcription…"):
                    transcript = voice.transcribe(load_stt(), audio.getvalue())
            except Exception as exc:
                st.caption(f"Transcription indisponible ({type(exc).__name__})")
            st.session_state.voice_done = digest
            if transcript:
                st.session_state.pending_question = transcript
                st.rerun()
with col_input:
    question = st.chat_input("Posez votre question sur l'ONSSA…")

if not question:
    question = st.session_state.pop("pending_question", None)

if question:
    conv["messages"].append({"role": "user", "content": question})
    if len(conv["messages"]) == 1:
        conv["title"] = convs.title_from(question)
    with st.chat_message("user"):
        st.markdown(question)

    history = [
        {"role": m["role"], "content": m["content"]} for m in conv["messages"][:-1]
    ]
    with st.chat_message("assistant"):
        refusal = rag.safety_refusal(question)
        if refusal:
            st.markdown(refusal)
            text, sources = refusal, []
        else:
            with st.status("🔎 Analyse de la question…", expanded=False) as status:
                standalone, result = rag.retrieve_for(
                    question,
                    history,
                    retriever,
                    top_k=s["top_k"],
                    max_context_chars=s["max_context"],
                    model=s["model"],
                )
                if standalone != question:
                    st.caption(f"Question reformulée : *{standalone}*")
                if result.relevant and result.passages:
                    for p in result.passages:
                        st.caption(f"📄 [{p.title}]({p.url})")
                    status.update(
                        label=f"✅ {len(result.passages)} extraits trouvés — rédaction en cours…",
                        state="complete",
                    )
                else:
                    status.update(label="ℹ️ Aucun contenu pertinent trouvé", state="complete")

            if result.relevant and result.passages:
                text = st.write_stream(
                    rag.generate_stream(
                        question,
                        history,
                        result.passages,
                        model=s["model"],
                        temperature=s["temperature"],
                    )
                )
                sources = list(dict.fromkeys(p.url for p in result.passages))
            else:
                text = rag.FALLBACK_ANSWER
                st.markdown(text)
                sources = []

    conv["messages"].append({"role": "assistant", "content": text, "sources": sources})
    convs.save(conv)
    st.rerun()
