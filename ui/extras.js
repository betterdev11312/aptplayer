/* Recursos complementares do player:
 * letras sincronizadas, fila arrastável e teclas de mídia.
 * Carregado depois de app.js — usa state, audio, $ e playTrack dele.
 */

/* ===== Letras ===== */

const lyrics = { open: false, data: null, index: -1, videoId: null };

async function loadLyrics(track) {
  if (!track) return;
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
