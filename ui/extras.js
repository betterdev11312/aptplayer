/* Recursos complementares do player:
 * letras sincronizadas, fila arrastável e teclas de mídia.
 * Carregado depois de app.js — usa state, audio, $ e playTrack dele.
 */

/* ===== Letras ===== */

const lyrics = { open: false, data: null, index: -1, videoId: null };

async function loadLyrics(track) {
  if (!track) return;
  // faixa nova: descarta a traducao da anterior
  if (typeof lyricsTr !== "undefined") {
    lyricsTr.on = false;
    lyricsTr.original = null;
    $("lyrics-translate")?.classList.remove("on");
  }
  lyrics.videoId = track.video_id;
  lyrics.data = null;
  lyrics.index = -1;

  $("lyrics-title").textContent = `${track.artist} — ${track.title}`;
  $("lyrics-body").innerHTML = `<div class="loading">buscando letra...</div>`;

  const res = await api().get_lyrics(track.artist, track.title, track.duration || 0);

  // a faixa pode ter mudado enquanto a letra carregava
  if (lyrics.videoId !== track.video_id) return;

  if (!res.ok) {
    $("lyrics-body").innerHTML = `<div class="empty">${esc(res.error)}</div>`;
    return;
  }

  lyrics.data = res;
  const box = $("lyrics-body");

  if (res.synced && res.lines.length) {
    box.innerHTML = "";
    res.lines.forEach((item, i) => {
      const el = document.createElement("div");
      el.className = "lyric-line";
      el.dataset.i = i;
      el.textContent = item.line || "♪";
      el.addEventListener("click", () => { audio.currentTime = item.time; });
      box.appendChild(el);
    });
  } else {
    box.innerHTML = `<div class="lyrics-plain">${esc(res.plain)}</div>`;
  }
}

function syncLyrics() {
  if (!lyrics.open || !lyrics.data || !lyrics.data.synced) return;
  const t = audio.currentTime;
  const lines = lyrics.data.lines;

  let index = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].time <= t + 0.25) index = i; else break;
  }
  if (index === lyrics.index) return;
  lyrics.index = index;

  const box = $("lyrics-body");
  box.querySelectorAll(".lyric-line").forEach((el, i) => {
    el.classList.toggle("active", i === index);
    el.classList.toggle("past", i < index);
  });

  const active = box.querySelector(".lyric-line.active");
  if (active) {
    const offset = active.offsetTop - box.clientHeight / 2 + active.clientHeight / 2;
    box.scrollTo({ top: Math.max(0, offset), behavior: "smooth" });
  }
}

function toggleLyrics(force) {
  const track = state.queue[state.index];
  lyrics.open = force !== undefined ? force : !lyrics.open;
  $("lyrics-panel").classList.toggle("open", lyrics.open);
  $("btn-lyrics").classList.toggle("on", lyrics.open);

  if (!lyrics.open) return;
  if (!track) {
    $("lyrics-body").innerHTML = `<div class="empty">nada tocando</div>`;
    $("lyrics-title").textContent = "—";
  } else if (lyrics.videoId !== track.video_id) {
    loadLyrics(track);
  }
}

/* ===== Fila: arrastar para reordenar ===== */

let dragFrom = null;

function makeQueueDraggable(el, index) {
  el.draggable = true;

  el.addEventListener("dragstart", (ev) => {
    dragFrom = index;
    el.classList.add("dragging");
    ev.dataTransfer.effectAllowed = "move";
  });
  el.addEventListener("dragend", () => {
    el.classList.remove("dragging");
    document.querySelectorAll(".q-item").forEach((q) => q.classList.remove("drag-over"));
    dragFrom = null;
  });
  el.addEventListener("dragover", (ev) => {
    ev.preventDefault();
    if (dragFrom !== null && dragFrom !== index) el.classList.add("drag-over");
  });
  el.addEventListener("dragleave", () => el.classList.remove("drag-over"));
  el.addEventListener("drop", (ev) => {
    ev.preventDefault();
    el.classList.remove("drag-over");
    if (dragFrom === null || dragFrom === index) return;

    const current = state.queue[state.index];
    const [moved] = state.queue.splice(dragFrom, 1);
    state.queue.splice(index, 0, moved);
    // o índice atual acompanha a faixa que está tocando
    state.index = state.queue.indexOf(current);
    renderQueue();
  });
}

function removeFromQueue(index) {
  if (index === state.index) return toast("essa está tocando", true);
  state.queue.splice(index, 1);
  if (index < state.index) state.index -= 1;
  renderQueue();
}

/* ===== Teclas de mídia do teclado ===== */

function setupMediaKeys() {
  if (!("mediaSession" in navigator)) return;
  try {
    navigator.mediaSession.setActionHandler("play", () => audio.play());
    navigator.mediaSession.setActionHandler("pause", () => audio.pause());
    navigator.mediaSession.setActionHandler("nexttrack", () => playNext(false));
    navigator.mediaSession.setActionHandler("previoustrack", () => playPrev());
    navigator.mediaSession.setActionHandler("seekto", (d) => {
      if (d.seekTime != null) audio.currentTime = d.seekTime;
    });
  } catch {
    // webview sem suporte completo: as teclas de mídia ficam sem efeito
  }
}

function updateMediaSession(track) {
  if (!("mediaSession" in navigator)) return;
  try {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: track.title,
      artist: track.artist,
      album: "AptPlayer",
      artwork: track.thumbnail
        ? [{ src: track.thumbnail, sizes: "320x180", type: "image/jpeg" }]
        : [],
    });
  } catch {}
}

/* ===== Ligações ===== */

document.addEventListener("DOMContentLoaded", () => {
  $("btn-lyrics")?.addEventListener("click", () => toggleLyrics());
  $("lyrics-close")?.addEventListener("click", () => toggleLyrics(false));
  audio.addEventListener("timeupdate", syncLyrics);
});

/* ===== Tradução de letras ===== */

const lyricsTr = { on: false, lang: "pt", original: null, langs: [] };

async function loadTranslateLanguages() {
  if (lyricsTr.langs.length) return lyricsTr.langs;
  const res = await api().translate_languages();
  lyricsTr.langs = res.ok ? res.languages : [];
  return lyricsTr.langs;
}

function savedLyricsLang() {
  try { return localStorage.getItem("aptplayer-lyrics-lang") || "pt"; }
  catch { return "pt"; }
}

async function fillLanguageSelects() {
  const langs = await loadTranslateLanguages();
  const saved = savedLyricsLang();
  lyricsTr.lang = saved;

  const options = langs
    .map((l) => `<option value="${esc(l.code)}">${esc(l.name)}</option>`)
    .join("");

  ["lyrics-lang", "lyrics-lang-default"].forEach((id) => {
    const select = $(id);
    if (!select || select.children.length) return;
    select.innerHTML = options;
    select.value = saved;
    select.addEventListener("change", (ev) => {
      lyricsTr.lang = ev.target.value;
      try { localStorage.setItem("aptplayer-lyrics-lang", ev.target.value); } catch {}
      // mantém os dois seletores em sincronia
      ["lyrics-lang", "lyrics-lang-default"].forEach((other) => {
        if (other !== id && $(other)) $(other).value = ev.target.value;
      });
      if (lyricsTr.on) translateCurrentLyrics();
    });
  });

  // idiomas da interface
  const ui = $("ui-lang");
  if (ui && !ui.children.length) {
    ui.innerHTML = uiLanguages()
      .map((l) => `<option value="${l.code}">${esc(l.name)}</option>`)
      .join("");
    try { ui.value = localStorage.getItem("aptplayer-lang") || "pt"; } catch {}
    ui.addEventListener("change", (ev) => {
      applyLanguage(ev.target.value);
      toast(`idioma: ${I18N[ev.target.value]._name}`);
    });
  }
}

function renderLyricLines(lines, translated) {
  const box = $("lyrics-body");
  box.innerHTML = "";
  lines.forEach((item, i) => {
    const el = document.createElement("div");
    el.className = "lyric-line" + (translated ? " translated" : "");
    el.dataset.i = i;
    el.textContent = item.line || "\u266A";
    el.addEventListener("click", () => { audio.currentTime = item.time; });
    box.appendChild(el);
  });
}

async function translateCurrentLyrics() {
  const track = state.queue[state.index];
  if (!track) return toast("nada tocando", true);

  const btn = $("lyrics-translate");
  btn.classList.add("on");
  const note = document.createElement("div");
  note.className = "lyrics-note";
  note.textContent = "traduzindo...";
  $("lyrics-body").prepend(note);

  const res = await api().translate_lyrics(
    track.artist, track.title, track.duration || 0, lyricsTr.lang);

  note.remove();

  if (!res.ok) {
    btn.classList.remove("on");
    lyricsTr.on = false;
    return toast(res.error, true);
  }

  // guarda o original para poder voltar
  if (!lyricsTr.original) lyricsTr.original = lyrics.data;

  lyricsTr.on = true;
  const langName = lyricsTr.langs.find((l) => l.code === lyricsTr.lang)?.name || lyricsTr.lang;

  if (res.synced) {
    lyrics.data = { synced: true, lines: res.lines, plain: "" };
    lyrics.index = -1;
    renderLyricLines(res.lines, true);
  } else {
    lyrics.data = { synced: false, lines: [], plain: res.plain };
    $("lyrics-body").innerHTML = `<div class="lyrics-plain">${esc(res.plain)}</div>`;
  }

  const tag = document.createElement("div");
  tag.className = "lyrics-note";
  tag.textContent = `traduzido para ${langName}`;
  $("lyrics-body").prepend(tag);
  toast(`letra traduzida para ${langName}`);
}

function restoreOriginalLyrics() {
  if (!lyricsTr.original) return;
  lyrics.data = lyricsTr.original;
  lyrics.index = -1;
  lyricsTr.on = false;
  lyricsTr.original = null;
  $("lyrics-translate").classList.remove("on");

  if (lyrics.data.synced && lyrics.data.lines.length) {
    renderLyricLines(lyrics.data.lines, false);
  } else {
    $("lyrics-body").innerHTML = `<div class="lyrics-plain">${esc(lyrics.data.plain)}</div>`;
  }
  toast("letra original");
}

document.addEventListener("DOMContentLoaded", () => {
  $("lyrics-translate")?.addEventListener("click", () => {
    if (lyricsTr.on) restoreOriginalLyrics();
    else translateCurrentLyrics();
  });
});
