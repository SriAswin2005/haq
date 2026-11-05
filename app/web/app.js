/* Haq web UI. Vanilla JS, no build step.
   - Chats live in localStorage (this browser only). The server is sent the chat's state on every
     turn, so a restarted server continues the conversation.
   - Answers stream real pipeline stages over Server-Sent Events (/api/turn/stream), with a
     plain /api/turn fallback.
   - Interface text comes from i18n.js (English, Hindi, Telugu); answers come in the user's language. */
(() => {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const KEY = "haq.chats.v1";
  const SKEY = "haq.settings.v1";
  const FKEY = "haq.firstRunSeen.v1";
  const I18N = window.HAQ_I18N || { en: {} };
  const HIDE_FACTS = new Set(["minor_stated", "category", "months_since_event", "language", "conflicts"]);

  let chats = load(KEY, []);
  let settings = Object.assign({ lang: "", mode: "advice", speak: "voice" }, load(SKEY, {}));
  let current = null;
  let busy = false;
  let stage = "start";
  let installEvt = null;
  const audioUrls = {};
  const seenFacts = {};
  const openFeedback = new Set();

  function load(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } }
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(chats)); localStorage.setItem(SKEY, JSON.stringify(settings)); }
    catch { showNotice("errEngine", true); }
  }
  const uid = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // ---------------------------------------------------------------- i18n
  function uiLang() {
    const pick = (code) => (code || "").slice(0, 2).toLowerCase();
    if (I18N[pick(settings.lang)]) return pick(settings.lang);
    if (I18N[pick(navigator.language)]) return pick(navigator.language);
    return "en";
  }
  function t(key, vars) {
    const L = I18N[uiLang()] || {}, E = I18N.en || {};
    let v = key.split(".").reduce((o, k) => (o || {})[k], L);
    if (v == null) v = key.split(".").reduce((o, k) => (o || {})[k], E);
    if (v == null) v = key;
    if (vars) Object.keys(vars).forEach((k) => { v = String(v).replace("{" + k + "}", vars[k]); });
    return v;
  }
  function applyI18n(root = document) {
    root.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    root.querySelectorAll("[data-i18n-ph]").forEach((el) => { el.placeholder = t(el.dataset.i18nPh); });
    document.documentElement.lang = uiLang();
  }

  function inr(v) {
    const n = Number(String(v).replace(/,/g, ""));
    return isFinite(n) ? "₹" + n.toLocaleString("en-IN") : String(v);
  }
  function ago(ts) {
    const d = (Date.now() - ts) / 1000;
    const loc = uiLang() === "en" ? "en-IN" : uiLang() + "-IN";
    try {
      const rtf = new Intl.RelativeTimeFormat(loc, { numeric: "auto" });
      if (d < 60) return rtf.format(0, "second");
      if (d < 3600) return rtf.format(-Math.floor(d / 60), "minute");
      if (d < 86400) return rtf.format(-Math.floor(d / 3600), "hour");
    } catch { /* older browsers */ }
    return new Date(ts).toLocaleDateString(loc, { day: "numeric", month: "short" });
  }

  // ---------------------------------------------------------------- chats
  function newChat() {
    if (current && current.messages.length === 0) { render(); $("#txt").focus(); return; }
    current = { id: uid(), title: "", created: Date.now(), updated: Date.now(), messages: [], state: null,
      session_id: null, missing: [] };
    chats.unshift(current);
    persist(); render(); closeDrawers(); $("#txt").focus();
  }
  function openChat(id) {
    current = chats.find((c) => c.id === id) || current;
    seenFacts[current.id] = new Set(Object.keys((current.state || {}).case_file || {}));
    render(); closeDrawers();
  }
  function deleteChat() {
    if (!current || !current.messages.length || busy) return;
    if (!confirm(t("confirmDeleteChat"))) return;
    chats = chats.filter((c) => c !== current);
    current = null; persist();
    if (chats.length) openChat(chats[0].id); else newChat();
  }

  function renderChatList() {
    const shown = chats.filter((c) => c.messages.length || c === current);
    $("#chatList").innerHTML = shown.map((c) => `<button type="button" class="chat-item" data-id="${c.id}" aria-current="${c === current}">
      <span class="t">${esc(c.title || t("newCaseTitle"))}</span><span class="d">${ago(c.updated)}</span></button>`).join("");
  }

  // ---------------------------------------------------------------- rendering answers
  function formatText(text) {
    const paras = String(text).replace(/\r/g, "").split(/\n{2,}/);
    return paras.map((p) => {
      const lines = p.split("\n").filter((l) => !/^\s*(Source|स्रोत)\s*:/.test(l));
      if (!lines.length) return "";
      const fmt = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\[●([^\]]*)\]/g, '<span class="ph">[●$1]</span>');
      const bullet = (l) => /^\s*[-*•]\s+/.test(l);
      if (lines.some(bullet)) {
        let html = "", items = [];
        const flush = () => { if (items.length) { html += `<ul>${items.join("")}</ul>`; items = []; } };
        lines.forEach((l) => { if (bullet(l)) items.push(`<li>${fmt(l.replace(/^\s*[-*•]\s+/, ""))}</li>`); else { flush(); html += `<p>${fmt(l)}</p>`; } });
        flush();
        return html;
      }
      const muted = /legal information, not legal advice|कानूनी जानकारी है, कानूनी सलाह नहीं/i.test(p) && p.length < 160;
      return `<p${muted ? ' class="muted"' : ""}>${lines.map(fmt).join("<br>")}</p>`;
    }).join("");
  }

  function sourceChips(r, sources) {
    if (!r.citations || !r.citations.length) return "";
    return `<div class="sources">` + r.citations.map((cid) => {
      const s = (sources || {})[cid];
      if (!s) return "";
      const caution = s.source_type === "secondary" || /REVIEW/.test(s.status_note || "");
      const where = s.doc_type === "helpline" ? t("helpline") : `${s.unit || ""} ${s.unit_number || ""}`.trim();
      const checked = s.verified === "human" ? t("sourceHuman") : t("sourceOfficial");
      return `<a class="stamp${caution ? " caution" : ""}" href="${esc(s.source_url)}" target="_blank" rel="noopener"
        title="${esc(s.source_url)} (${esc(s.fetched_on)})"><b>${esc(s.doc_title)}</b><span>${esc(where)}</span>
        <small>${caution ? t("sourceCaution") : checked}</small></a>`;
    }).join("") + `</div>`;
  }

  function howPanel(m) {
    const r = m.result, tr = r.trace || {}, llm = tr.llm || {};
    const models = [...new Set((llm.models || []).map((x) => x.replace(/^(\w+):gemini:/, "$1: ")))];
    const fb = llm.fallbacks || [];
    const rows = (r.retrieved || []).map((x) => `<tr><td>${esc(x.id)}${x.via ? ` <small>(${esc(x.via)})</small>` : ""}${x.old_law ? " <small>(old law)</small>" : ""}</td><td class="num">${x.score == null ? "" : Number(x.score).toFixed(3)}</td></tr>`).join("");
    const issues = (r.verifier && r.verifier.issues && r.verifier.issues.length) ? `<dt>${t("howCheck")}</dt><dd>${esc(r.verifier.issues.join("; "))}</dd>` : "";
    const removed = tr.pruned ? `<dt>${t("howRemoved")}</dt><dd>${esc((tr.pruned.reasons || []).join("; "))}</dd>` : "";
    const trl = tr.translation ? `<dt>${t("howTranslation")}</dt><dd>${esc(tr.translation.to)}: ${esc(tr.translation.status)}</dd>` : "";
    const voice = (m.stt || m.ttsVia) ? `<dt>${t("howVoice")}</dt><dd>${m.stt ? `in: ${esc(m.stt.provider)}:${esc(m.stt.model)}` : ""}${m.ttsVia ? `${m.stt ? "; " : ""}out: ${esc(m.ttsVia)}` : ""}</dd>` : "";
    return `<details class="how"><summary>${t("how")}</summary>
      <dl class="how-grid">
        <dt>${t("howTopic")}</dt><dd>${esc(t("cat." + r.category))}</dd>
        <dt>${t("howResponse")}</dt><dd>${esc(r.action)}</dd>
        <dt>${t("howCheck")}</dt><dd>${esc(r.verifier ? r.verifier.status : "")}</dd>${issues}${removed}
        <dt>${t("howModels")}</dt><dd>${esc(models.join(", ") || t("none"))}</dd>
        <dt>${t("howSwitches")}</dt><dd>${fb.length ? esc(fb.map((f) => `${f.model.replace("gemini:", "")} (${f.reason})`).join("; ")) : t("none")}</dd>
        <dt>${t("howTime")}</dt><dd>${m.seconds ? m.seconds + " s" : ""}</dd>${trl}${voice}
      </dl>
      ${rows ? `<table><thead><tr><th>${t("lawSearched")}</th><th>${t("match")}</th></tr></thead><tbody>${rows}</tbody></table>` : ""}
    </details>`;
  }

  function feedbackRow(m) {
    if (m.feedback === "sent") return `<span class="meta-line">${t("feedbackThanks")}</span>`;
    if (openFeedback.has(m.id)) {
      return `<div class="fb-form" data-fbform="${m.id}">
        <textarea rows="2" placeholder="${esc(t("feedbackWhy"))}" data-fbtext="${m.id}"></textarea>
        <label class="fb-share"><input type="checkbox" data-fbshare="${m.id}"> ${t("shareText")}</label>
        <button type="button" class="chip-btn" data-fbsend="${m.id}">${t("sendFeedback")}</button></div>`;
    }
    return `<span class="fb-q">${t("helpful")}</span>
      <button type="button" class="chip-btn" data-fb="up" data-mid="${m.id}" aria-label="${esc(t("yes"))}">${t("yes")}</button>
      <button type="button" class="chip-btn" data-fb="down" data-mid="${m.id}" aria-label="${esc(t("no"))}">${t("no")}</button>`;
  }

  function renderBot(m) {
    if (m.error) {
      return `<div class="msg bot err"><div class="avatar" aria-hidden="true">हक़</div><div class="bot-body"><div class="answer"><p>${esc(m.error)}</p></div>
        ${m.retryText ? `<div class="bot-actions"><button type="button" class="chip-btn" data-retry="${m.id}">${t("retry")}</button></div>` : ""}</div></div>`;
    }
    const r = m.result;
    let banner = "";
    if (r.action === "escalate") banner = `<div class="banner hard">${t("bannerHard")}</div>`;
    else if (r.needs_lawyer) banner = `<div class="banner soft">${t("bannerSoft")}</div>`;

    let body;
    if (r.draft_text) {
      const intro = String(r.reply_text).split(/\n{2,}/)[0];
      const file = ((r.trace || {}).draft || {}).file_name || "draft.txt";
      body = formatText(intro) + `<div class="sheet"><div class="sheet-head"><span>${t("fillBlanks")}</span>
        <span class="btns"><button type="button" class="chip-btn" data-copy="${m.id}">${t("copy")}</button>
        <button type="button" class="chip-btn" data-dl="${m.id}" data-file="${esc(file)}">${t("download")}</button></span></div>
        <pre>${esc(r.draft_text).replace(/\[●([^\]]*)\]/g, '<span class="ph">[●$1]</span>')}</pre></div>`;
    } else {
      body = formatText(r.reply_text);
    }
    const audio = audioUrls[m.id]
      ? `<audio controls src="${audioUrls[m.id]}" ${m.autoplay ? "autoplay" : ""}></audio>`
      : `<button type="button" class="chip-btn" data-listen="${m.id}">${m.speaking ? t("preparingAudio") : t("listen")}</button>`;
    m.autoplay = false;
    return `<div class="msg bot"><div class="avatar" aria-hidden="true">हक़</div><div class="bot-body">
      ${banner}<div class="answer" lang="${esc((r.reply_lang || "en").slice(0, 2))}">${body}</div>${sourceChips(r, m.sources)}
      <div class="bot-actions">${audio}<button type="button" class="chip-btn" data-copyans="${m.id}">${t("copyAnswer")}</button>
        ${m.ttsError ? `<span class="meta-line">${esc(m.ttsError)}</span>` : ""}</div>
      <div class="bot-actions fb">${feedbackRow(m)}</div>
      ${howPanel(m)}</div></div>`;
  }

  function renderLog() {
    const log = $("#log");
    if (!current || !current.messages.length) {
      log.innerHTML = "";
      const tpl = $("#tplEmpty").content.cloneNode(true);
      applyI18n(tpl);
      log.appendChild(tpl);
      return;
    }
    log.innerHTML = current.messages.map((m) => m.role === "user"
      ? `<div class="msg user"><div class="bubble">${m.voice ? `<span class="mic-mark">${t("spoken")}</span>` : ""}${esc(m.text)}</div></div>`
      : renderBot(m)).join("") +
      (busy ? `<div class="msg bot pending"><div class="avatar" aria-hidden="true">हक़</div><div class="step" id="step">${esc(t("steps." + stage))}…</div></div>` : "");
    log.scrollTop = log.scrollHeight;
  }

  function renderCaseFile() {
    const body = $("#fileBody");
    const cf = ((current || {}).state || {}).case_file || {};
    const keys = Object.keys(cf).filter((k) => !HIDE_FACTS.has(k) && cf[k] !== null && cf[k] !== "" &&
      !(Array.isArray(cf[k]) && !cf[k].length));
    $("#factCount").textContent = keys.length;
    const lastBot = [...((current || {}).messages || [])].reverse().find((m) => m.result);
    const cat = lastBot ? lastBot.result.category : null;
    if (!keys.length && !cat) { body.innerHTML = `<p class="fb-empty">${t("fileEmpty")}</p>`; return; }
    const seen = seenFacts[current.id] || (seenFacts[current.id] = new Set());
    const label = (k) => t("facts." + k) === "facts." + k ? k.replace(/_/g, " ") : t("facts." + k);
    const facts = keys.map((k) => {
      let v = cf[k];
      if (k === "amount_inr" || k === "monthly_wage_inr") v = inr(v);
      else if (Array.isArray(v)) v = v.join(", ");
      else if (typeof v === "object") v = JSON.stringify(v);
      if (k === "event_date" && cf.months_since_event != null) v = `${v} (${t("monthsAgo", { n: Math.round(cf.months_since_event) })})`;
      const isNew = !seen.has(k); seen.add(k);
      return `<div class="fact${isNew ? " new" : ""}"><dt>${esc(label(k))}</dt><dd>${esc(v)}</dd></div>`;
    }).join("");
    const conflicts = (cf.conflicts || []).map((c) => `<li><b>${esc(label(c.field))}</b>: ${esc(t("youSaid", { a: c.earlier, b: c.now }))}</li>`).join("");
    const missing = (current.missing || []).slice(0, 5);
    const srcs = {};
    current.messages.forEach((m) => m.result && (m.result.citations || []).forEach((cid) => { if (m.sources && m.sources[cid]) srcs[cid] = m.sources[cid]; }));
    const srcList = Object.values(srcs).map((s) => `<li><a href="${esc(s.source_url)}" target="_blank" rel="noopener">${esc(s.doc_title)}${s.doc_type === "helpline" ? "" : `, ${esc(s.unit)} ${esc(s.unit_number)}`}</a></li>`).join("");
    body.innerHTML = `${cat ? `<span class="fb-cat">${esc(t("cat." + cat))}</span>` : ""}
      ${conflicts ? `<div class="fb-conflict"><div class="fb-h">${t("pleaseCheck")}</div><ul class="fb-list">${conflicts}</ul></div>` : ""}
      ${facts ? `<dl class="facts">${facts}</dl>` : ""}
      ${missing.length ? `<div class="fb-h">${t("stillNeeded")}</div><ul class="fb-list">${missing.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
      ${srcList ? `<div class="fb-h">${t("lawsUsed")}</div><ul class="fb-list">${srcList}</ul>` : ""}`;
  }

  function render() {
    applyI18n();
    $("#chatTitle").textContent = current && current.title ? current.title : t("newCaseTitle");
    renderChatList(); renderLog(); renderCaseFile();
    $("#btnSend").disabled = busy;
    $("#btnDelChat").hidden = !(current && current.messages.length);
    document.querySelectorAll('input[name="mode"]').forEach((i) => { i.checked = i.value === settings.mode; });
    $("#selSpeak").value = settings.speak;
    if ($("#selLang").options.length) $("#selLang").value = settings.lang;
    const mn = $("#modeNotice");
    if (mn.dataset.sticky) { mn.textContent = t(mn.dataset.key || ""); return; }
    if (settings.mode === "draft") { mn.hidden = false; mn.className = "notice"; mn.textContent = t("draftNotice"); }
    else mn.hidden = true;
  }

  // key: an i18n key (re-translated when the language changes) or literal text from the server
  function showNotice(key, warn) {
    const mn = $("#modeNotice"); mn.hidden = false; mn.dataset.key = key;
    mn.textContent = t(key); mn.className = "notice" + (warn ? " warn" : "");
    mn.dataset.sticky = "1";
    clearTimeout(showNotice.tm);
    if (!warn) return;
    showNotice.tm = setTimeout(() => { delete mn.dataset.sticky; render(); }, 9000);
  }

  // ---------------------------------------------------------------- talking to the server
  function setStage(s) { stage = s; const el = $("#step"); if (el) el.textContent = t("steps." + s) + "…"; }

  async function postTurn(payload) {
    // Streams real stages; falls back to the plain endpoint if streaming is unavailable.
    let res;
    try {
      res = await fetch("/api/turn/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    } catch (e) { throw new Error(e.message || "network error"); }
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error(d.detail || `HTTP ${res.status}`);
    }
    if (!res.body || !res.body.getReader) {
      const r2 = await fetch("/api/turn", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const d2 = await r2.json().catch(() => ({}));
      if (!r2.ok) throw new Error(d2.detail || `HTTP ${r2.status}`);
      return d2;
    }
    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "", result = null, error = null;
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const block = buf.slice(0, i); buf = buf.slice(i + 2);
        const ev = (block.match(/^event: (.*)$/m) || [])[1];
        const data = (block.match(/^data: (.*)$/m) || [])[1];
        if (!ev || !data) continue;
        const obj = JSON.parse(data);
        if (ev === "stage") setStage(obj.stage);
        else if (ev === "result") result = obj;
        else if (ev === "error") error = obj.error;
      }
    }
    if (error) throw new Error(error);
    if (!result) throw new Error("the connection closed early");
    return result;
  }

  async function send(text, inputMode = "text", stt = null) {
    text = (text || "").trim();
    if (!text || busy) return;
    if (!current) newChat();
    const chat = current;
    chat.messages.push({ id: uid(), role: "user", text, voice: inputMode === "voice" });
    if (!chat.title) chat.title = text.length > 60 ? text.slice(0, 57) + "…" : text;
    chat.updated = Date.now();
    busy = true; stage = "start"; persist(); render();
    try {
      const data = await postTurn({ text, session_id: chat.session_id, lang: settings.lang || null, mode: settings.mode,
        input_mode: inputMode, state: chat.state });
      chat.session_id = data.session_id; chat.state = data.state; chat.missing = data.missing_facts || [];
      const msg = { id: uid(), role: "assistant", result: data.result, sources: data.sources, seconds: data.seconds, stt };
      chat.messages.push(msg);
      if (settings.speak === "always" || (settings.speak === "voice" && inputMode === "voice")) { msg.speaking = true; speak(msg, true); }
    } catch (e) {
      chat.messages.push({ id: uid(), role: "assistant", error: t("errEngine", { e: e.message }), retryText: text });
    } finally {
      busy = false; chat.updated = Date.now(); persist();
      if (chat === current) render();
    }
  }

  async function speak(msg, auto) {
    msg.speaking = true; msg.ttsError = ""; if (!auto) render();
    try {
      const r = msg.result;
      const res = await fetch("/api/tts", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: r.draft_text ? String(r.reply_text).split(/\n{2,}/)[0] : r.reply_text, lang: r.reply_lang }) });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.error || d.detail || "Audio is not available right now."); }
      msg.ttsVia = res.headers.get("X-Voice-Provider") || "";
      audioUrls[msg.id] = URL.createObjectURL(await res.blob());
      msg.autoplay = true;
    } catch (e) {
      msg.ttsError = e.message;
    } finally {
      msg.speaking = false; persist(); render();
    }
  }

  async function sendFeedback(m, rating, reason, share) {
    const r = m.result || {};
    const q = current.messages[current.messages.indexOf(m) - 1];
    try {
      await fetch("/api/feedback", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: m.id, rating, reason: reason || null, category: r.category, action: r.action,
          verifier_status: (r.verifier || {}).status, citations: r.citations || [], reply_lang: r.reply_lang,
          share_text: !!share, question: share && q ? q.text : null, answer: share ? r.reply_text : null }) });
    } catch { /* feedback is best effort */ }
    m.feedback = "sent"; openFeedback.delete(m.id); persist(); render();
  }

  // ---------------------------------------------------------------- microphone
  let recorder = null, recChunks = [], recStart = 0, recTimer = null;
  async function toggleMic() {
    if (recorder) { recorder.stop(); return; }
    if (busy) return;
    if (!navigator.mediaDevices || !window.MediaRecorder) { showNotice("micUnsupported", true); return; }
    let stream;
    try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
    catch { showNotice("micBlocked", true); return; }
    const type = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find((x) => MediaRecorder.isTypeSupported(x)) || "";
    recorder = new MediaRecorder(stream, type ? { mimeType: type } : undefined);
    recChunks = [];
    recorder.ondataavailable = (e) => e.data.size && recChunks.push(e.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach((x) => x.stop());
      clearInterval(recTimer); $("#recState").hidden = true; $("#txt").hidden = false;
      const mic = $("#btnMic"); mic.classList.remove("rec");
      const blob = new Blob(recChunks, { type: recorder.mimeType || "audio/webm" });
      recorder = null;
      if (blob.size < 2000) { showNotice("tooShort", true); return; }
      mic.classList.add("busy"); mic.disabled = true;
      try {
        const fd = new FormData();
        fd.append("audio", blob, "recording." + ((blob.type.split("/")[1] || "webm").split(";")[0]));
        fd.append("lang", settings.lang || "");
        const res = await fetch("/api/stt", { method: "POST", body: fd });
        const d = await res.json().catch(() => ({}));
        if (!res.ok || !d.text) throw new Error(d.error || d.detail || t("sttFail"));
        await send(d.text, "voice", { provider: d.provider, model: d.model, language: d.language });
      } catch (e) {
        showNotice(e.message, true);
      } finally { mic.classList.remove("busy"); mic.disabled = false; }
    };
    recorder.start();
    recStart = Date.now();
    $("#btnMic").classList.add("rec"); $("#txt").hidden = true; $("#recState").hidden = false;
    const tick = () => {
      const s = Math.floor((Date.now() - recStart) / 1000);
      $("#recState").textContent = t("recording", { t: `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}` });
      if (s >= 120 && recorder) recorder.stop();
    };
    tick(); recTimer = setInterval(tick, 250);
  }

  // ---------------------------------------------------------------- export / drawers
  function download(name, text, type = "text/plain") {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: type + ";charset=utf-8" }));
    a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  function chatAsText(c) {
    const lines = [c.title || t("newCaseTitle"), new Date(c.updated).toLocaleString("en-IN"), ""];
    c.messages.forEach((m) => {
      if (m.role === "user") lines.push("You: " + m.text, "");
      else if (m.error) lines.push("Haq: " + m.error, "");
      else lines.push("Haq: " + m.result.reply_text, "");
    });
    lines.push(t("legalNote"));
    return lines.join("\n");
  }
  function closeDrawers() {
    $("#shelf").classList.remove("open"); $("#casefile").classList.remove("open"); $("#scrim").hidden = true;
    $("#btnShelf").setAttribute("aria-expanded", "false"); $("#btnFile").setAttribute("aria-expanded", "false");
  }
  function toggleDrawer(el, btn) {
    const open = !el.classList.contains("open"); closeDrawers();
    if (open) { el.classList.add("open"); $("#scrim").hidden = false; btn.setAttribute("aria-expanded", "true"); }
  }

  // ---------------------------------------------------------------- events
  const findMsg = (id) => current && current.messages.find((m) => m.id === id);

  document.addEventListener("click", (e) => {
    const b = e.target.closest("button, a");
    if (!b) return;
    if (b.classList.contains("chat-item")) return openChat(b.dataset.id);
    if (b.classList.contains("example")) return send(b.dataset.text);
    if (b.dataset.listen) { const m = findMsg(b.dataset.listen); if (m && !m.speaking) speak(m, false); return; }
    if (b.dataset.copy || b.dataset.copyans) {
      const m = findMsg(b.dataset.copy || b.dataset.copyans);
      if (!m) return;
      navigator.clipboard.writeText(b.dataset.copy ? m.result.draft_text : m.result.reply_text)
        .then(() => { const o = b.textContent; b.textContent = t("copied"); setTimeout(() => (b.textContent = o), 1400); });
      return;
    }
    if (b.dataset.dl) { const m = findMsg(b.dataset.dl); if (m) download(b.dataset.file || "draft.txt", m.result.draft_text); return; }
    if (b.dataset.fb) {
      const m = findMsg(b.dataset.mid); if (!m) return;
      if (b.dataset.fb === "up") sendFeedback(m, "up");
      else { openFeedback.add(m.id); render(); const ta = document.querySelector(`[data-fbtext="${m.id}"]`); if (ta) ta.focus(); }
      return;
    }
    if (b.dataset.fbsend) {
      const m = findMsg(b.dataset.fbsend); if (!m) return;
      sendFeedback(m, "down", (document.querySelector(`[data-fbtext="${m.id}"]`) || {}).value,
        (document.querySelector(`[data-fbshare="${m.id}"]`) || {}).checked);
      return;
    }
    if (b.dataset.retry) {
      const i = current.messages.findIndex((m) => m.id === b.dataset.retry);
      const m = current.messages[i];
      if (m) { current.messages.splice(i - 1, 2); send(m.retryText); }
    }
  });

  const autosize = () => { const ta = $("#txt"); ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 180) + "px"; };
  $("#composer").addEventListener("submit", (e) => { e.preventDefault(); const v = $("#txt").value; $("#txt").value = ""; autosize(); send(v); });
  $("#txt").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); $("#composer").requestSubmit(); } });
  $("#txt").addEventListener("input", autosize);
  $("#btnMic").addEventListener("click", toggleMic);
  $("#btnNew").addEventListener("click", newChat);
  $("#btnDelChat").addEventListener("click", deleteChat);
  $("#selSpeak").addEventListener("change", (e) => { settings.speak = e.target.value; persist(); });
  $("#selLang").addEventListener("change", (e) => { settings.lang = e.target.value; persist(); render(); });
  document.querySelectorAll('input[name="mode"]').forEach((i) => i.addEventListener("change", (e) => {
    settings.mode = e.target.value; delete $("#modeNotice").dataset.sticky; persist(); render(); }));
  $("#btnExport").addEventListener("click", () => download("haq-chats.json", JSON.stringify(chats, null, 2), "application/json"));
  $("#btnTxt").addEventListener("click", () => current && current.messages.length && download("haq-chat.txt", chatAsText(current)));
  $("#btnClear").addEventListener("click", () => {
    if (!confirm(t("confirmDeleteAll"))) return;
    chats = []; current = null; persist(); newChat();
  });
  $("#btnShelf").addEventListener("click", () => toggleDrawer($("#shelf"), $("#btnShelf")));
  $("#btnFile").addEventListener("click", () => toggleDrawer($("#casefile"), $("#btnFile")));
  $("#scrim").addEventListener("click", closeDrawers);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawers(); });

  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); installEvt = e; $("#btnInstall").hidden = false; });
  $("#btnInstall").addEventListener("click", async () => {
    if (!installEvt) return;
    installEvt.prompt(); await installEvt.userChoice.catch(() => null);
    installEvt = null; $("#btnInstall").hidden = true;
  });
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => null));
  }

  // ---------------------------------------------------------------- start
  (async () => {
    applyI18n();
    try {
      const meta = await (await fetch("/api/meta")).json();
      $("#selLang").innerHTML = meta.languages.map((l) => `<option value="${esc(l.code)}">${esc(l.label)}</option>`).join("");
      $("#selLang").value = settings.lang;
      if (meta.sample_data) showNotice("sampleData", true);
      else if (meta.mock) { showNotice("demoMode"); }
    } catch { showNotice("engineDown", true); }
    chats.forEach((c) => c.messages.forEach((m) => { m.speaking = false; m.autoplay = false; }));
    chats = chats.filter((c) => c.messages.length);
    current = chats.length ? chats[0] : null;
    if (!current) newChat(); else { seenFacts[current.id] = new Set(Object.keys((current.state || {}).case_file || {})); render(); }
    const fr = $("#firstRun");
    if (!localStorage.getItem(FKEY) && fr && fr.showModal) {
      applyI18n(fr); fr.showModal();
      fr.addEventListener("close", () => { try { localStorage.setItem(FKEY, "1"); } catch { /* ignore */ } $("#txt").focus(); });
    }
  })();
})();
