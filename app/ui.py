"""Streamlit UI. Run: streamlit run app/ui.py"""
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os

import streamlit as st

# Streamlit Community Cloud: keys live in the app's Secrets, not in .env. Copy them into the
# environment so llm.py / voice.py read them the same way locally and in the cloud.
try:
    for _k in ("GEMINI_API_KEY", "SARVAM_API_KEY", "KUKU_API_KEY"):
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:  # no secrets file locally: .env is used instead
    pass

from app import guards, pipeline, retrieval, voice
from app.config import load_config, is_mock

st.set_page_config(page_title="AI Lawyer for India", page_icon="⚖️", layout="centered")

LANGS = {"Auto-detect": None, "English": "en-IN", "हिन्दी (Hindi)": "hi-IN"}
MODES = {"Advice": "advice", "Draft (notice / complaint)": "draft", "Practice (not built yet)": "practice"}

if "session" not in st.session_state:
    st.session_state.session = pipeline.new_session()
    st.session_state.log = []  # [(role, text, TurnResult|None)]
    st.session_state.audio = {}  # log index -> WAV bytes of the spoken reply
    st.session_state.heard = set()  # hashes of recordings already processed

st.title("⚖️ AI Lawyer for India")
st.caption("Everyday legal problems: consumer refunds, unpaid salary, rental deposits. Type or speak, in English or Hindi.")

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
    SPEAK = {"When I speak": "voice", "Always": "always", "Never": "never"}
    speak_label = st.selectbox("Read answers aloud", list(SPEAK), index=0,
                               help="Text-to-speech uses Sarvam credits. Long answers: only the first part is read.")
    speak_mode = SPEAK[speak_label]
    if st.button("New conversation"):
        st.session_state.session = pipeline.new_session()
        st.session_state.log = []
        st.session_state.audio = {}
        st.rerun()
    with st.expander("Case file so far"):
        st.json(st.session_state.session.case_file)


def show_details(r: pipeline.TurnResult) -> None:
    with st.expander("How I got this answer"):
        st.write(f"**Category:** {r.category}   **Action:** {r.action}   **Verifier:** {r.verifier['status']}")
        if r.trace.get("stt") or r.trace.get("tts"):
            v_in, v_out = r.trace.get("stt") or {}, r.trace.get("tts") or {}
            st.caption(f"Voice: heard via {v_in.get('provider', '-')}:{v_in.get('model', '-')} | "
                       f"spoken via {v_out.get('provider', '-')}:{v_out.get('model', '-')}")
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
                    for note in guards.source_notes(c):
                        (st.warning if "REVIEW" in note or note == guards.CAUTION else st.caption)(note)
        if r.retrieved:
            st.write("**Retrieved (rank order)**")
            st.table([{"id": x["id"], "score": round(x["score"], 3)} for x in r.retrieved])
        with st.popover("Raw trace"):
            st.json(json.loads(json.dumps(r.trace, default=str)))


for i, (role, text, r) in enumerate(st.session_state.log):
    with st.chat_message(role):
        if r is not None and r.action == "escalate":
            st.warning("This needs a real lawyer or free legal aid. See below.")
        elif r is not None and r.needs_lawyer:
            st.warning("Please consider speaking to a real lawyer or free legal aid office.")
        st.write(text)
        if i in st.session_state.audio:
            st.audio(st.session_state.audio[i], format="audio/wav")
        if r is not None:
            if r.draft_text:
                st.code(r.draft_text, language=None)  # code block has a copy button
                st.download_button("Download as .txt", r.draft_text,
                                   file_name=(r.trace.get("draft") or {}).get("file_name", "draft.txt"), key=f"dl{i}")
            show_details(r)

def run_turn(text: str, input_mode: str, lang_hint: str | None, stt_info: dict | None = None) -> None:
    shown = ("🎤 " + text) if input_mode == "voice" else text
    st.session_state.log.append(("user", shown, None))
    with st.spinner("Checking verified sources..."):
        res = pipeline.handle_turn(st.session_state.session, text, input_mode=input_mode, lang_hint=lang_hint)
    st.session_state.log.append(("assistant", res.reply_text, res))
    if stt_info:
        res.trace["stt"] = stt_info
    if speak_mode == "always" or (speak_mode == "voice" and input_mode == "voice"):
        try:
            with st.spinner("Preparing audio..."):
                out = voice.tts(res.reply_text, res.reply_lang)
            st.session_state.audio[len(st.session_state.log) - 1] = out["audio"]
            res.trace["tts"] = {k: v for k, v in out.items() if k != "audio"}
        except voice.VoiceError as ex:
            res.trace["tts_error"] = str(ex)
            st.session_state.log.append(("assistant", "🔇 I could not read this answer aloud right now. "
                                         "The full answer is above.", None))


_audio_input = getattr(st, "audio_input", None) or getattr(st, "experimental_audio_input", None)
rec = _audio_input("🎤 Or speak your problem (Hindi or English)") if _audio_input else None
if rec is not None:
    data = rec.getvalue()
    h = hashlib.sha1(data).hexdigest()
    if data and h not in st.session_state.heard:
        st.session_state.heard.add(h)
        try:
            with st.spinner("Listening..."):
                heard = voice.stt(data, LANGS[lang_label])
            run_turn(heard["text"], "voice", LANGS[lang_label] or heard.get("language"),
                     {k: heard.get(k) for k in ("provider", "model", "language", "pieces", "errors")})
        except voice.VoiceError as ex:
            st.session_state.log.append(("assistant", "🎤 I could not understand the recording. "
                                         "Please try again closer to the mic, or type your problem below. "
                                         f"({ex})", None))
        st.rerun()

prompt = st.chat_input("Describe your problem (English or हिन्दी)")
if prompt:
    run_turn(prompt, "text", LANGS[lang_label])
    st.rerun()

st.divider()
st.caption("Legal information, not legal advice.")
