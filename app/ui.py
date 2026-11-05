"""Streamlit UI. Run: streamlit run app/ui.py"""
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app import pipeline, retrieval
from app.config import load_config, is_mock

st.set_page_config(page_title="AI Lawyer for India", page_icon="⚖️", layout="centered")

LANGS = {"Auto-detect": None, "English": "en-IN", "हिन्दी (Hindi)": "hi-IN"}
MODES = {"Advice": "advice", "Draft (deposit notice)": "draft", "Practice (not built yet)": "practice"}

if "session" not in st.session_state:
    st.session_state.session = pipeline.new_session()
    st.session_state.log = []  # [(role, text, TurnResult|None)]

st.title("⚖️ AI Lawyer for India")
st.caption("Everyday legal problems: consumer refunds, unpaid salary, rental deposits. Text in English or Hindi.")

idx = retrieval.get_index()
if idx["has_sample"]:
    st.error("SAMPLE DATA LOADED: the chunks are fake and are NOT real law. "
             "Set corpus.path to data/corpus in config.yaml for real answers.")
if idx["problems"]:
    st.warning(f"{len(idx['problems'])} corpus line(s) were skipped as invalid. See logs.")
if is_mock():
    st.info("MOCK MODE: canned model output, no API keys used. Not real model behaviour.")

with st.sidebar:
    st.header("Settings")
    lang_label = st.selectbox("Language", list(LANGS), index=0)
    mode_label = st.selectbox("Mode", list(MODES), index=0)
    st.session_state.session.mode = MODES[mode_label]
    st.caption("Voice input and output: not available in this build.")
    if st.button("New conversation"):
        st.session_state.session = pipeline.new_session()
        st.session_state.log = []
        st.rerun()
    with st.expander("Case file so far"):
        st.json(st.session_state.session.case_file)


def show_details(r: pipeline.TurnResult) -> None:
    with st.expander("How I got this answer"):
        st.write(f"**Category:** {r.category}   **Action:** {r.action}   **Verifier:** {r.verifier['status']}")
        if r.verifier.get("issues"):
            st.write("Verifier notes:", r.verifier["issues"])
        by_id = {c["id"]: c for c in idx["chunks"]}
        if r.citations:
            st.write("**Citations shown**")
            for cid in r.citations:
                c = by_id.get(cid)
                if c:
                    st.markdown(f"- `{cid}` {c['doc_title']}, {c['unit']} {c['unit_number']} | fetched {c['fetched_on']} "
                                f"| verified: **{c['verified']}** | [{c['status']}] | [source]({c['source_url']})")
        if r.retrieved:
            st.write("**Retrieved (rank order)**")
            st.table([{"id": x["id"], "score": round(x["score"], 3)} for x in r.retrieved])
        with st.popover("Raw trace"):
            st.json(json.loads(json.dumps(r.trace, default=str)))


for role, text, r in st.session_state.log:
    with st.chat_message(role):
        if r is not None and r.action == "escalate":
            st.warning("This needs a real lawyer or free legal aid. See below.")
        elif r is not None and r.needs_lawyer:
            st.warning("Please consider speaking to a real lawyer or free legal aid office.")
        st.write(text)
        if r is not None:
            if r.draft_text:
                st.code(r.draft_text, language=None)  # code block has a copy button
                st.download_button("Download as .txt", r.draft_text, file_name="deposit_notice.txt")
            show_details(r)

prompt = st.chat_input("Describe your problem (English or हिन्दी)")
if prompt:
    st.session_state.log.append(("user", prompt, None))
    with st.spinner("Checking verified sources..."):
        res = pipeline.handle_turn(st.session_state.session, prompt, lang_hint=LANGS[lang_label])
    st.session_state.log.append(("assistant", res.reply_text, res))
    st.rerun()

st.divider()
st.caption("Legal information, not legal advice.")
