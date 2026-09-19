/* AptPlayer - interface Cyberpunk */

const $ = (id) => document.getElementById(id);
let audio = $("audio");   // trocavel: o crossfade alterna dois elementos

const state = {
  queue: [],
  index: -1,
  shuffle: false,
  repeat: false,
  playlistId: null,
  chat: [],
  ready: false,
};

const api = () => window.pywebview && window.pywebview.api;
const mediaUrl = (path) => `http://127.0.0.1:${window.MEDIA_PORT}${path}`;

function fmt(seconds) {
  if (!seconds || isNaN(seconds)) return "0:00";
  const s = Math.floor(seconds % 60);
  const m = Math.floor(seconds / 60) % 60;
  const h = Math.floor(seconds / 3600);
  const mm = h ? String(m).padStart(2, "0") : m;
  return h ? `${h}:${mm}:${String(s).padStart(2, "0")}`
           : `${mm}:${String(s).padStart(2, "0")}`;
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = text ?? "";
  return d.innerHTML;
}

let toastTimer;
function toast(message, isError = false) {
  const el = $("toast");
  el.textContent = message;
  el.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.className = "toast"), 3400);
}

/* ===== Modal (substitui prompt/confirm nativos) ===== */

function modal({ title, fields = [], confirmText = "OK", onConfirm }) {
  const root = $("modal-root");
  const bg = document.createElement("div");
  bg.className = "modal-bg";

  const inputs = fields.map((f, i) =>
    f.type === "select"
      ? `<select data-i="${i}">${f.options.map((o) =>
          `<option value="${esc(o.value)}">${esc(o.label)}</option>`).join("")}</select>`
      : `<input data-i="${i}" type="text" placeholder="${esc(f.placeholder || "")}"
           value="${esc(f.value || "")}">`
  ).join("");

  bg.innerHTML = `
    <div class="modal">
      <h3>${esc(title)}</h3>
      ${inputs}
      <div class="modal-actions">
        <button class="btn" data-act="cancel">Cancelar</button>
        <button class="btn primary" data-act="ok">${esc(confirmText)}</button>
      </div>
    </div>`;

  const close = () => bg.remove();
  const submit = () => {
    const values = [...bg.querySelectorAll("[data-i]")].map((el) => el.value.trim());
    close();
    onConfirm?.(values);
  };

  bg.addEventListener("click", (ev) => {
    if (ev.target === bg || ev.target.dataset.act === "cancel") close();
    if (ev.target.dataset.act === "ok") submit();
  });
  bg.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") submit();
    if (ev.key === "Escape") close();
  });

  root.appendChild(bg);
  bg.querySelector("input, select")?.focus();
}

function confirmBox(title, onYes) {
  modal({ title, fields: [], confirmText: "Confirmar", onConfirm: onYes });
}

/* ===== Navegação ===== */

function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  $("view-" + name)?.classList.add("active");
  // Sem isto a tela nova abre na posicao de rolagem da anterior.
  document.querySelector(".main")?.scrollTo({ top: 0, behavior: "instant" });
  document.querySelectorAll(".nav-item").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === name)
  );

  if (name === "home") loadHome();
  if (name === "library") loadLibrary();
  if (name === "favorites") loadFavorites();
  if (name === "history") loadHistory();
  if (name === "ai") refreshAiStatus();
  if (name === "chat") initChat();
  if (name === "settings") initSettings();
  if (name === "stats") loadStats();
  if (name === "rooms") { initRoomsOnce(); loadRooms(); }
}

document.querySelectorAll(".nav-item").forEach((btn) =>
  btn.addEventListener("click", () => showView(btn.dataset.view))
);

/* ===== Faixas ===== */

function trackRow(track, context = {}) {
  const el = document.createElement("div");
  el.className = "track";
  if (state.queue[state.index]?.video_id === track.video_id) el.classList.add("playing");

  const tags = [
    track.genre ? `<span class="tag">${esc(track.genre)}</span>` : "",
    track.mood ? `<span class="tag mood">${esc(track.mood)}</span>` : "",
  ].join("");

  el.innerHTML = `
    <div class="track-art">
      <img src="${esc(track.thumbnail)}" alt="" loading="lazy">
      <div class="eq"><i></i><i></i><i></i><i></i></div>
    </div>
    <div class="track-info">
      <div class="track-title">${esc(track.title)}</div>
      <div class="track-artist">${esc(track.artist)}</div>
      ${tags ? `<div class="track-tags">${tags}</div>` : ""}
    </div>
    <span class="track-time">${esc(track.duration_label || fmt(track.duration))}</span>
    <div class="track-actions">
      <button class="icon-btn${track.favorite ? " fav-on" : ""}" data-act="fav" title="Favoritar">
        <svg viewBox="0 0 24 24"><path d="M12 20s-7-4.5-7-9a4 4 0 0 1 7-2.6A4 4 0 0 1 19 11c0 4.5-7 9-7 9z"/></svg>
      </button>
      <button class="icon-btn" data-act="queue" title="Adicionar à fila">
        <svg viewBox="0 0 24 24"><path d="M4 6h11M4 12h11M4 18h7M18 12v7M14.5 15.5h7"/></svg>
      </button>
      <button class="icon-btn" data-act="download" data-dl="${esc(track.video_id)}" title="baixar para ouvir offline">
        <svg viewBox="0 0 24 24"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 19h16"/></svg>
      </button>
      <button class="icon-btn" data-act="radio" title="Rádio a partir desta música">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="2.5"/><path d="M7.5 16.5a6 6 0 0 1 0-9M16.5 7.5a6 6 0 0 1 0 9M4.5 19.5a10 10 0 0 1 0-15M19.5 4.5a10 10 0 0 1 0 15"/></svg>
      </button>
      <button class="icon-btn" data-act="playlist" title="Adicionar a playlist">
        <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
      </button>
      ${context.playlistId ? `
      <button class="icon-btn" data-act="remove" title="Remover">
        <svg viewBox="0 0 24 24"><path d="M5 12h14"/></svg>
      </button>` : ""}
    </div>`;

  el.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-act]");
    if (!btn) return playTrack(track, context.list || [track]);
    ev.stopPropagation();
    const act = btn.dataset.act;
    if (act === "fav") toggleFavorite(track, btn);
    if (act === "queue") addToQueue(track);
    if (act === "playlist") addToPlaylistPrompt(track);
    if (act === "radio") radioFromTrack(track);
    if (act === "download") downloadTrack(track, btn);
    if (act === "remove") removeFromPlaylist(context.playlistId, track.video_id);
  });

  return el;
}

function renderList(containerId, tracks, context = {}) {
  const box = $(containerId);
  box.innerHTML = "";
  if (!tracks || !tracks.length) {
    box.innerHTML = `<div class="empty">${esc(context.emptyText || "vazio")}</div>`;
    return;
  }
  const ctx = { ...context, list: tracks };
  tracks.forEach((t) => box.appendChild(trackRow(t, ctx)));
  refreshDownloadMarks(tracks, box);
}

function markPlaying() {
  const current = state.queue[state.index];
  document.querySelectorAll(".track").forEach((row) => {
    const title = row.querySelector(".track-title")?.textContent;
    const artist = row.querySelector(".track-artist")?.textContent;
    row.classList.toggle(
      "playing",
      !!current && title === current.title && artist === current.artist
    );
  });
}

/* ===== Player ===== */

async function playTrack(track, list = null) {
  if (list) {
    state.queue = list.slice();
    state.index = list.findIndex((t) => t.video_id === track.video_id);
  } else {
    state.index = state.queue.findIndex((t) => t.video_id === track.video_id);
  }
  if (state.index < 0) {
    state.queue = [track];
    state.index = 0;
  }

  $("np-title").textContent = track.title;
  $("np-artist").textContent = "// resolvendo stream...";
  $("np-art").src = track.thumbnail || "";
  $("np-art").classList.toggle("hidden", !track.thumbnail);
  $("source-badge").classList.add("hidden");
  renderQueue();
  markPlaying();

  const res = await api().resolve_stream(track.video_id);
  if (!res.ok) {
    $("np-artist").textContent = track.artist;
    toast(res.error || "Falha ao tocar esta faixa.", true);
    return;
  }

  audio.src = res.source === "cache" ? mediaUrl(res.url) : res.url;
  try {
    await audio.play();
  } catch {
    toast("Falha ao iniciar o áudio.", true);
    return;
  }

  $("np-artist").textContent = track.artist;
  if (res.source === "cache") $("source-badge").classList.remove("hidden");

  onTrackStarted(track);
}

/** Interface e registros quando uma faixa comeca.
 *  Usado tanto pelo playTrack quanto pelo crossfade. */
function onTrackStarted(track) {
  $("np-title").textContent = track.title;
  $("np-artist").textContent = track.artist;
  $("np-art").src = track.thumbnail || "";
  $("np-art").classList.toggle("hidden", !track.thumbnail);

  api().play_started(track);
  updateFavButton(track);
  updateMediaSession(track);
  updateTitlebar(track);
  if (typeof lyrics !== "undefined" && lyrics.open) loadLyrics(track);
  catOn.play(track, (track.play_count || 0) >= 2);
  renderQueue();
  markPlaying();

  const next = state.queue[state.index + 1];
  if (next) api().prefetch(next.video_id);

  extendRadio();
}

function playNext(auto = false) {
  if (!state.queue.length) return;
  if (state.repeat && auto) {
    audio.currentTime = 0;
    audio.play();
    return;
  }
  let next;
  if (state.shuffle) {
    next = Math.floor(Math.random() * state.queue.length);
  } else {
    next = state.index + 1;
    if (next >= state.queue.length) {
      if (auto) return;
      next = 0;
    }
  }
  state.index = next;
  playTrack(state.queue[next]);
}

function playPrev() {
  if (!state.queue.length) return;
  if (audio.currentTime > 3) return (audio.currentTime = 0);
  state.index = state.index > 0 ? state.index - 1 : state.queue.length - 1;
  playTrack(state.queue[state.index]);
}

$("btn-play").addEventListener("click", () => {
  if (!state.queue.length) return;
  audio.paused ? audio.play() : audio.pause();
});
$("btn-next").addEventListener("click", () => { catOn.skip(); playNext(false); });
$("btn-prev").addEventListener("click", playPrev);
$("btn-shuffle").addEventListener("click", (e) => {
  state.shuffle = !state.shuffle;
  e.currentTarget.classList.toggle("on", state.shuffle);
  toast(state.shuffle ? "Aleatório ligado" : "Aleatório desligado");
});
$("btn-repeat").addEventListener("click", (e) => {
  state.repeat = !state.repeat;
  e.currentTarget.classList.toggle("on", state.repeat);
  toast(state.repeat ? "Repetição ligada" : "Repetição desligada");
});

/** Liga os eventos do player a um elemento <audio>.
 *  Chamado de novo quando o crossfade troca de elemento. */
function bindAudioEvents(el) {
  el.addEventListener("play", () => {
    $("icon-play").classList.add("hidden");
    $("icon-pause").classList.remove("hidden");
  });
  el.addEventListener("pause", () => {
    $("icon-play").classList.remove("hidden");
    $("icon-pause").classList.add("hidden");
    catOn.pause();
  });
  el.addEventListener("ended", () => playNext(true));
  el.addEventListener("error", () => {
    if (el.src) toast("Erro ao reproduzir o áudio.", true);
  });
  el.addEventListener("timeupdate", () => {
    const pct = el.duration ? (el.currentTime / el.duration) * 100 : 0;
    $("progress-fill").style.width = pct + "%";
    $("time-current").textContent = fmt(el.currentTime);
    if (typeof syncLyrics === "function") syncLyrics();
    if (typeof fadeWatch === "function") fadeWatch();
  });
  el.addEventListener("loadedmetadata", () => {
    $("time-total").textContent = fmt(el.duration);
  });
}

bindAudioEvents(audio);

const ratio = (bar, ev) => {
  const r = bar.getBoundingClientRect();
  return Math.min(1, Math.max(0, (ev.clientX - r.left) / r.width));
};

$("progress-bar").addEventListener("click", (ev) => {
  if (audio.duration) audio.currentTime = ratio($("progress-bar"), ev) * audio.duration;
});
$("volume-bar").addEventListener("click", (ev) => {
  const v = ratio($("volume-bar"), ev);
  audio.volume = v;
  audio.muted = false;
  $("btn-mute").classList.remove("on");
  $("volume-fill").style.width = v * 100 + "%";
  if (typeof fadeSetBaseVolume === "function") fadeSetBaseVolume(v);
});
$("btn-mute").addEventListener("click", () => {
  audio.muted = !audio.muted;
  $("btn-mute").classList.toggle("on", audio.muted);
  $("volume-fill").style.width = (audio.muted ? 0 : audio.volume * 100) + "%";
});

/* ===== Fila ===== */

function renderQueue() {
  const box = $("queue-list");
  box.innerHTML = "";
  if (!state.queue.length) {
    box.innerHTML = `<div class="empty">fila vazia</div>`;
    return;
  }
  state.queue.forEach((track, i) => {
    const el = document.createElement("div");
    el.className = "q-item" + (i === state.index ? " current" : "");
    el.innerHTML =
      `<span class="q-grip" title="arraste para reordenar">\u28FF</span>` +
      `<span class="q-index">${String(i + 1).padStart(2, "0")}</span>` +
      `<img src="${esc(track.thumbnail)}" alt="" loading="lazy">` +
      `<div class="q-meta">` +
        `<div class="q-title">${esc(track.title)}</div>` +
        `<div class="q-artist">${esc(track.artist)}</div>` +
      `</div>` +
      `<button class="q-remove" title="remover da fila">` +
        `<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>` +
      `</button>`;

    el.addEventListener("click", (ev) => {
      if (ev.target.closest(".q-remove")) {
        ev.stopPropagation();
        return removeFromQueue(i);
      }
      state.index = i;
      playTrack(track);
    });
    makeQueueDraggable(el, i);
    box.appendChild(el);
  });
}

function addToQueue(track) {
  state.queue.push(track);
  api().add_track(track);
  renderQueue();
  toast(`+ ${track.title}`);
}

$("clear-queue").addEventListener("click", () => {
  const current = state.queue[state.index];
  state.queue = current ? [current] : [];
  state.index = current ? 0 : -1;
  renderQueue();
});

/* ===== Favoritos ===== */

async function toggleFavorite(track, btn) {
  await api().add_track(track);
  const res = await api().toggle_favorite(track.video_id);
  track.favorite = res.favorite ? 1 : 0;
  btn?.classList.toggle("fav-on", !!res.favorite);
  if (state.queue[state.index]?.video_id === track.video_id) updateFavButton(track);
  toast(res.favorite ? "♥ favoritada" : "removida das favoritas");
  catOn.favorite(!!res.favorite);
}

const updateFavButton = (track) =>
  $("np-fav").classList.toggle("fav-on", !!track.favorite);

$("np-fav").addEventListener("click", () => {
  const track = state.queue[state.index];
  if (track) toggleFavorite(track, $("np-fav"));
});

/* ===== Busca ===== */

let searchTimer;
$("search-input").addEventListener("input", (ev) => {
  clearTimeout(searchTimer);
  const query = ev.target.value.trim();
  if (query.length < 2) return;
  searchTimer = setTimeout(() => runSearch(query), 500);
});
$("search-input").addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") {
    clearTimeout(searchTimer);
    const query = ev.target.value.trim();
    if (query) runSearch(query);
  }
});

async function runSearch(query) {
  $("search-results").innerHTML = `<div class="loading">buscando...</div>`;
  const res = await api().search(query, 20);
  if (!res.ok) {
    $("search-results").innerHTML = `<div class="empty">${esc(res.error)}</div>`;
    return;
  }
  if (!res.results.length) catOn.noResults();
  renderList("search-results", res.results, {
    emptyText: "nenhuma música encontrada",
  });
}

/* ===== Biblioteca ===== */

async function loadLibrary() {
  const res = await api().get_library($("library-order").value);
  renderList("library-list", res.tracks, {
    emptyText: "biblioteca vazia — toque algo para começar",
  });
  refreshCacheInfo();
}
$("library-order").addEventListener("change", loadLibrary);

async function loadFavorites() {
  const res = await api().get_favorites();
  renderList("favorites-list", res.tracks, { emptyText: "nenhuma favorita" });
}

async function loadHistory() {
  const res = await api().get_history(50);
  renderList("history-list", res.tracks, { emptyText: "nada tocado ainda" });
}

async function refreshCacheInfo() {
  const { stats } = await api().cache_stats();
  const dl = stats.downloading ? ` · ${stats.downloading} DL` : "";
  $("cache-info").textContent = `CACHE ${stats.files} · ${stats.size_mb}MB${dl}`;
}

/* ===== Playlists ===== */

async function loadPlaylists() {
  const res = await api().get_playlists();
  const box = $("playlist-list");
  box.innerHTML = "";
  if (!res.playlists.length) {
    box.innerHTML = `<div class="empty" style="padding:16px;font-size:11px">nenhuma</div>`;
    return;
  }
  res.playlists.forEach((pl) => {
    const el = document.createElement("div");
    el.className = "pl-item" + (pl.id === state.playlistId ? " active" : "");
    const art = pl.cover
      ? `<img class="pl-cover" src="${mediaUrl(`/cover/${pl.id}?v=${Date.now()}`)}" alt="">`
      : `<div class="pl-cover-ph">♫</div>`;
    el.innerHTML = `
      ${art}
      <div class="pl-meta">
        <div class="pl-name">${esc(pl.name)}</div>
        <div class="pl-count">${pl.track_count} faixas</div>
      </div>`;
    el.addEventListener("click", () => openPlaylist(pl.id));
    box.appendChild(el);
  });
}

async function openPlaylist(playlistId) {
  state.playlistId = playlistId;
  showView("playlist");

  const res = await api().get_playlist(playlistId);
  const pl = res.playlist || {};
  $("playlist-title").textContent = pl.name || "—";

  const total = res.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
  $("playlist-stats").textContent =
    `${res.tracks.length} faixas · ${fmt(total)} de duração`;

  $("pl-cover-box").innerHTML = pl.cover
    ? `<img src="${mediaUrl(`/cover/${playlistId}?v=${Date.now()}`)}" alt="">`
    : `<div class="ph">♫</div>`;

  renderList("playlist-tracks", res.tracks, {
    playlistId,
    emptyText: "playlist vazia",
  });
  loadPlaylists();
}

$("new-playlist").addEventListener("click", () => {
  modal({
    title: "Nova playlist",
    fields: [{ placeholder: "nome da playlist" }],
    confirmText: "Criar",
    onConfirm: async ([name]) => {
      if (!name) return;
      const res = await api().create_playlist(name);
      if (!res.ok) return toast(res.error, true);
      await loadPlaylists();
      catOn.playlistCreated();
      toast("playlist criada");
      openPlaylist(res.id);
    },
  });
});

$("rename-playlist").addEventListener("click", async () => {
  if (!state.playlistId) return;
  const { playlist } = await api().get_playlist(state.playlistId);
  modal({
    title: "Renomear playlist",
    fields: [{ value: playlist?.name || "" }],
    confirmText: "Salvar",
    onConfirm: async ([name]) => {
      if (!name) return;
      const res = await api().rename_playlist(state.playlistId, name);
      if (!res.ok) return toast(res.error, true);
      openPlaylist(state.playlistId);
      toast("renomeada");
    },
  });
});

async function changeCover() {
  if (!state.playlistId) return;
  const res = await api().pick_playlist_cover(state.playlistId);
  if (res.cancelled) return;
  if (!res.ok) return toast(res.error, true);
  openPlaylist(state.playlistId);
  catOn.playlistCover();
  toast("capa atualizada");
}

$("change-cover").addEventListener("click", changeCover);
$("pl-cover-box").addEventListener("click", changeCover);

$("play-playlist").addEventListener("click", async () => {
  if (!state.playlistId) return;
  const res = await api().get_playlist(state.playlistId);
  if (!res.tracks.length) return toast("playlist vazia", true);
  state.shuffle = false;
  $("btn-shuffle").classList.remove("on");
  playTrack(res.tracks[0], res.tracks);
});

$("shuffle-playlist").addEventListener("click", async () => {
  if (!state.playlistId) return;
  const res = await api().get_playlist(state.playlistId);
  if (!res.tracks.length) return toast("playlist vazia", true);
  const shuffled = res.tracks.slice().sort(() => Math.random() - 0.5);
  state.shuffle = true;
  $("btn-shuffle").classList.add("on");
  playTrack(shuffled[0], shuffled);
});

$("delete-playlist").addEventListener("click", () => {
  if (!state.playlistId) return;
  confirmBox("Excluir esta playlist?", async () => {
    await api().delete_playlist(state.playlistId);
    state.playlistId = null;
    loadPlaylists();
    showView("library");
    toast("playlist excluída");
  });
});

async function addToPlaylistPrompt(track) {
  const res = await api().get_playlists();
  if (!res.playlists.length) {
    return toast("crie uma playlist primeiro (botão + na lateral)", true);
  }
  modal({
    title: "Adicionar a playlist",
    fields: [{
      type: "select",
      options: res.playlists.map((p) => ({
        value: String(p.id),
        label: `${p.name} (${p.track_count})`,
      })),
    }],
    confirmText: "Adicionar",
    onConfirm: async ([playlistId]) => {
      await api().add_track(track);
      await api().add_to_playlist(Number(playlistId), track.video_id);
      loadPlaylists();
      const name = res.playlists.find((p) => String(p.id) === playlistId)?.name;
      toast(`+ "${name}"`);
    },
  });
}

async function removeFromPlaylist(playlistId, videoId) {
  await api().remove_from_playlist(playlistId, videoId);
  openPlaylist(playlistId);
  toast("removida");
}

/* ===== Chat IA ===== */

function chatBubble(role, content, suggestions = []) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  const avatar = role === "ai" ? "AI" : "EU";

  const suggHtml = suggestions.length
    ? `<div class="msg-suggestions">` +
      suggestions.map((t, i) =>
        `<div class="sugg" data-i="${i}">` +
          `<img src="${esc(t.thumbnail)}" alt="">` +
          `<div class="sugg-meta">` +
            `<div class="sugg-title">${esc(t.title)}</div>` +
            `<div class="sugg-artist">${esc(t.artist)}</div>` +
          `</div>` +
          `<svg class="sugg-play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>` +
        `</div>`
      ).join("") +
      `</div>`
    : "";

  el.innerHTML =
    `<div class="msg-avatar">${avatar}</div>` +
    `<div class="msg-body"><span class="msg-text">${esc(content)}</span>${suggHtml}</div>`;

  el.querySelectorAll(".sugg").forEach((node) =>
    node.addEventListener("click", () => {
      const track = suggestions[Number(node.dataset.i)];
      if (track) playTrack(track, suggestions);
    })
  );

  return el;
}

function initChat() {
  refreshChatStatus();
  if (!$("chat-log").children.length && !state.chat.length) {
    $("chat-log").appendChild(chatBubble(
      "ai",
      "Sou o assistente do AptPlayer. Posso recomendar músicas, falar sobre artistas e montar o clima que você quiser. O que vamos ouvir?"
    ));
  }
}

async function refreshChatStatus() {
  const res = await api().ai_status();
  const el = $("chat-status");
  const ready = res.available && res.models.length;
  el.textContent = ready
    ? `// ollama online · ${res.active}`
    : res.available
      ? "// falta um modelo — no terminal: ollama pull llama3.2"
      : "// IA desligada — instale o Ollama (ollama.com) e rode: ollama pull llama3.2";
  $("chat-send").disabled = !ready;
  $("chat-text").disabled = !ready;
}

async function sendChat() {
  const input = $("chat-text");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  const log = $("chat-log");
  log.appendChild(chatBubble("user", text));
  state.chat.push({ role: "user", content: text });
  log.scrollTop = log.scrollHeight;

  const thinking = document.createElement("div");
  thinking.className = "msg ai";
  thinking.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-body"><div class="typing"><i></i><i></i><i></i></div></div>`;
  log.appendChild(thinking);
  log.scrollTop = log.scrollHeight;

  $("chat-send").disabled = true;
  const res = await api().ai_chat(state.chat);
  $("chat-send").disabled = false;
  thinking.remove();

  if (!res.ok) {
    log.appendChild(chatBubble("ai", `Erro: ${res.error}`));
    log.scrollTop = log.scrollHeight;
    return;
  }

  state.chat.push({ role: "assistant", content: res.reply });
  log.appendChild(chatBubble("ai", res.reply, res.suggestions || []));
  log.scrollTop = log.scrollHeight;
}

$("chat-send").addEventListener("click", sendChat);
$("chat-text").addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") sendChat();
});
$("clear-chat").addEventListener("click", () => {
  state.chat = [];
  $("chat-log").innerHTML = "";
  initChat();
});

/* ===== Ferramentas IA ===== */

async function refreshAiStatus() {
  const res = await api().ai_status();
  const el = $("ai-status");
  const buttons = ["ai-search-btn", "ai-playlist-btn", "ai-tag-btn"];
  const ready = res.available && res.models.length;

  el.textContent = ready
    ? `// ollama online · modelo: ${res.active}`
    : res.available
      ? "// falta um modelo — no terminal: ollama pull llama3.2"
      : "// IA desligada — instale o Ollama (ollama.com) e rode: ollama pull llama3.2";

  buttons.forEach((b) => ($(b).disabled = !ready));
}

$("ai-search-btn").addEventListener("click", async () => {
  const request = $("ai-search-input").value.trim();
  if (!request) return;
  const btn = $("ai-search-btn");
  btn.disabled = true;
  btn.textContent = "Pensando...";
  $("ai-results").innerHTML = `<div class="loading">a IA está escolhendo...</div>`;

  const res = await api().ai_search(request);
  btn.disabled = false;
  btn.textContent = "Buscar";

  if (!res.ok) {
    $("ai-results").innerHTML = `<div class="empty">${esc(res.error)}</div>`;
    return;
  }
  renderList("ai-results", res.results);
  toast(res.queries.join(" · "));
});

$("ai-playlist-btn").addEventListener("click", async () => {
  const description = $("ai-playlist-input").value.trim();
  if (!description) return;
  const btn = $("ai-playlist-btn");
  btn.disabled = true;
  btn.textContent = "Montando...";

  const res = await api().ai_playlist(description);
  btn.disabled = false;
  btn.textContent = "Gerar";

  if (!res.ok) return toast(res.error, true);
  await loadPlaylists();
  toast(`"${res.name}" · ${res.count} faixas`);
  openPlaylist(res.id);
});

$("ai-tag-btn").addEventListener("click", async () => {
  const btn = $("ai-tag-btn");
  btn.disabled = true;
  btn.textContent = "Classificando...";

  const res = await api().ai_tag_library(20);
  btn.disabled = false;
  btn.textContent = "Classificar";

  if (!res.ok) return toast(res.error, true);
  toast(res.updated ? `${res.updated} faixas classificadas` : "nada novo para classificar");
});

/* ===== Atalhos ===== */

document.addEventListener("keydown", (ev) => {
  if (ev.target.tagName === "INPUT" || ev.target.tagName === "SELECT") return;
  if (ev.code === "Space") {
    ev.preventDefault();
    $("btn-play").click();
  }
  if (ev.code === "ArrowRight" && ev.ctrlKey) playNext(false);
  if (ev.code === "ArrowLeft" && ev.ctrlKey) playPrev();
  if (ev.code === "KeyL") toggleLyrics();
  if (ev.code === "ArrowUp") {
    ev.preventDefault();
    audio.volume = Math.min(1, audio.volume + 0.05);
    audio.muted = false;
    $("volume-fill").style.width = audio.volume * 100 + "%";
  }
  if (ev.code === "ArrowDown") {
    ev.preventDefault();
    audio.volume = Math.max(0, audio.volume - 0.05);
    $("volume-fill").style.width = audio.volume * 100 + "%";
  }
});

/* ===== Início ===== */

function boot() {
  if (state.ready) return;
  state.ready = true;
  try {
    applyTheme(localStorage.getItem("aptplayer-theme") || "edgerunners");
  } catch { applyTheme("edgerunners"); }
  audio.volume = 0.8;
  $("volume-fill").style.width = "80%";
  renderQueue();
  loadPlaylists();
  refreshCacheInfo();
  loadHome();
  setupMediaKeys();
  initLanguage();
  fillLanguageSelects();
  initAudioFx();
  fadeInit();
  restoreHotkeys();
  catInit();
}

window.addEventListener("pywebviewready", boot);
setTimeout(() => { if (api()) boot(); }, 1400);

/* ===== Temas ===== */

const THEMES = [
  { id: "edgerunners", name: "Edgerunners", desc: "Amarelo ácido e ciano. Scanlines e glitch.",
    colors: ["#fcee0a", "#00f0ff", "#ff2a6d", "#05060a"] },
  { id: "synthwave", name: "Synthwave", desc: "Roxo e rosa neon, grid retrô dos anos 80.",
    colors: ["#ff6ac1", "#00e5ff", "#c77dff", "#0d0221"] },
  { id: "matrix", name: "Matrix", desc: "Verde fósforo em terminal. Tudo monoespaçado.",
    colors: ["#00ff41", "#00c853", "#76ff03", "#000700"] },
  { id: "vaporwave", name: "Vaporwave", desc: "Pastel suave, cantos redondos, sem scanline.",
    colors: ["#ff99e6", "#7af0ff", "#ffd6a5", "#1a1033"] },
  { id: "blood", name: "Blood", desc: "Vermelho sobre preto. Agressivo e sujo.",
    colors: ["#ff1e27", "#ff6b35", "#c1121f", "#0a0203"] },
  { id: "clean", name: "Clean", desc: "Sóbrio, sem efeitos. Para quem quer foco.",
    colors: ["#e8e8ec", "#8ab4f8", "#f28b82", "#131316"] },
  { id: "arasaka", name: "Arasaka", desc: "Corporativo e frio. Vermelho sobre preto absoluto.",
    colors: ["#e8e8ec", "#ff3b3b", "#ff6b6b", "#0a0a0c"] },
  { id: "acid", name: "Acid", desc: "Verde-limão tóxico. Radioativo e ácido.",
    colors: ["#c6ff2e", "#39ffa0", "#ff9f1c", "#07100a"] },
  { id: "midnight", name: "Midnight", desc: "Azul profundo e calmo. Sem barulho visual.",
    colors: ["#8ab4ff", "#6c7ce8", "#b48ce8", "#080c18"] },
  { id: "amber", name: "Amber", desc: "Monitor âmbar dos anos 80. Scanlines pesadas.",
    colors: ["#ffb000", "#ff8c1a", "#ffd166", "#120c04"] },
  { id: "arcade", name: "Arcade", desc: "Fliperama em fonte pixelada. Puro 8-bit.",
    colors: ["#ffe14d", "#4deeff", "#ff4d88", "#12071c"] },
  { id: "snow", name: "Snow", desc: "O único claro. Para ambientes iluminados.",
    colors: ["#0066cc", "#0a8fa8", "#d6336c", "#e8ebf2"] },
];

function applyTheme(id) {
  const theme = THEMES.find((t) => t.id === id) || THEMES[0];
  document.documentElement.dataset.theme = theme.id;
  const noFlicker = ["clean", "vaporwave", "midnight", "snow"];
  document.body.classList.toggle("fx-flicker", !noFlicker.includes(theme.id));
  try { localStorage.setItem("aptplayer-theme", theme.id); } catch {}
  document.querySelectorAll(".theme-card").forEach((card) =>
    card.classList.toggle("active", card.dataset.theme === theme.id)
  );
}

function renderThemes() {
  const grid = $("theme-grid");
  if (!grid || grid.children.length) return;
  THEMES.forEach((theme) => {
    const card = document.createElement("div");
    card.className = "theme-card";
    card.dataset.theme = theme.id;
    // 4a cor = fundo do tema; 1a = destaque. Texto claro ou escuro conforme o fundo.
    const bg = theme.colors[3];
    const light = parseInt(bg.slice(1, 3), 16) + parseInt(bg.slice(3, 5), 16)
                + parseInt(bg.slice(5, 7), 16) > 380;
    card.style.background = bg;
    card.style.color = light ? "#14181f" : "#e8ecf8";

    card.innerHTML =
      `<div class="theme-name" style="color:${theme.colors[0]}">${esc(theme.name)}</div>` +
      `<div class="theme-swatches">` +
        theme.colors.map((c) => `<i style="background:${c}"></i>`).join("") +
      `</div>` +
      `<div class="theme-desc">${esc(theme.desc)}</div>`;
    card.addEventListener("click", () => {
      applyTheme(theme.id);
      toast(`tema: ${theme.name}`);
    });
    grid.appendChild(card);
  });
  const saved = (() => {
    try { return localStorage.getItem("aptplayer-theme"); } catch { return null; }
  })();
  applyTheme(saved || "edgerunners");
}

/* ===== Rádio ===== */

const radio = { on: false, seed: null, loading: false, useAi: true };

function setRadioUi(on) {
  radio.on = on;
  $("btn-radio").classList.toggle("on", on);
  $("radio-badge").classList.toggle("hidden", !on);
}

async function startRadio() {
  const seed = state.queue[state.index];
  if (!seed) return toast("toque uma música primeiro", true);

  if (radio.on) {
    setRadioUi(false);
    radio.seed = null;
    catOn.radio(false);
    return toast("rádio desligado");
  }

  setRadioUi(true);
  radio.seed = seed;
  catOn.radio(true);
  toast("montando o rádio...");

  const res = await api().radio_start(seed, 12, radio.useAi);
  if (!res.ok) {
    setRadioUi(false);
    return toast(res.error, true);
  }

  // A semente continua tocando; o resto do rádio vira a fila.
  state.queue = [seed, ...res.tracks];
  state.index = 0;
  renderQueue();
  toast(`rádio: ${res.tracks.length} faixas na fila`);
}

async function extendRadio() {
  if (!radio.on || radio.loading) return;
  const remaining = state.queue.length - state.index - 1;
  if (remaining > 3) return;

  radio.loading = true;
  const seed = state.queue[state.index] || radio.seed;
  const res = await api().radio_more(seed, 10, radio.useAi);
  radio.loading = false;

  if (res.ok && res.tracks.length) {
    state.queue.push(...res.tracks);
    renderQueue();
  }
}

async function radioFromTrack(track) {
  setRadioUi(false);          // garante estado limpo antes de religar
  await playTrack(track, [track]);
  await startRadio();
}

$("btn-radio").addEventListener("click", startRadio);

/* ===== Ajustes ===== */

function initSettings() {
  renderThemes();
  loadAbout();
  loadAccount();
  initAudioSettings();
  loadDiscord();
  const toggle = $("cat-toggle");
  if (toggle) {
    try { toggle.checked = localStorage.getItem("aptplayer-cat") !== "off"; }
    catch { toggle.checked = true; }
  }
  api().cache_stats().then(({ stats }) => {
    const el = $("settings-cache");
    if (el) {
      el.textContent =
        `${stats.files} músicas baixadas · ${stats.size_mb} MB` +
        (stats.downloading ? ` · ${stats.downloading} baixando agora` : "");
    }
  });
}

$("cat-toggle")?.addEventListener("change", (ev) => {
  catToggle(ev.target.checked);
  toast(ev.target.checked ? "Byte voltou" : "Byte foi dormir");
});

$("radio-ai")?.addEventListener("change", (ev) => {
  radio.useAi = ev.target.checked;
  toast(radio.useAi ? "IA ligada no rádio" : "rádio só com o mix do YouTube");
});

$("open-cache-folder")?.addEventListener("click", async () => {
  const res = await api().open_data_folder();
  if (!res.ok) toast(res.error || "não consegui abrir a pasta", true);
});

/* ===== Download manual ===== */

const DL_ICON = `<svg viewBox="0 0 24 24"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 19h16"/></svg>`;
const DL_OK   = `<svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>`;

async function downloadTrack(track, btn) {
  await api().add_track(track);
  const res = await api().force_cache(track.video_id);
  if (!res.ok) return toast("não consegui baixar", true);

  if (res.state === "ready") {
    markDownloadBtn(btn, "ready");
    return toast("já está offline");
  }
  markDownloadBtn(btn, "downloading");
  catOn.download();
  toast(`baixando "${track.title}"...`);
  watchDownload(track.video_id, btn);
}

function markDownloadBtn(btn, state) {
  if (!btn) return;
  btn.classList.remove("dl-ready", "dl-busy", "dl-failed");
  if (state === "ready") {
    btn.classList.add("dl-ready");
    btn.innerHTML = DL_OK;
    btn.title = "já disponível offline";
  } else if (state === "downloading") {
    btn.classList.add("dl-busy");
    btn.title = "baixando...";
  } else if (state === "failed") {
    btn.classList.add("dl-failed");
    btn.title = "falhou — clique para tentar de novo";
  } else {
    btn.innerHTML = DL_ICON;
    btn.title = "baixar para ouvir offline";
  }
}

/** Acompanha um download até terminar, sem travar a interface. */
function watchDownload(videoId, btn, tries = 0) {
  if (tries > 60) return;                 // ~3 min de teto
  setTimeout(async () => {
    const res = await api().cache_status([videoId]);
    const state = res.states?.[videoId];
    if (state === "ready") {
      markDownloadBtn(btn, "ready");
      refreshCacheInfo();
      return;
    }
    if (state === "failed") {
      markDownloadBtn(btn, "failed");
      return;
    }
    watchDownload(videoId, btn, tries + 1);
  }, 3000);
}

/** Marca nas listas visíveis o que já está em cache. */
async function refreshDownloadMarks(tracks, root = document) {
  if (!tracks?.length) return;
  const res = await api().cache_status(tracks.map((t) => t.video_id));
  Object.entries(res.states || {}).forEach(([videoId, state]) => {
    root.querySelectorAll(`[data-dl="${videoId}"]`).forEach((btn) => {
      if (state !== "none") markDownloadBtn(btn, state);
      if (state === "downloading") watchDownload(videoId, btn);
    });
  });
}

/* ===== Tela inicial ===== */

function greeting() {
  const h = new Date().getHours();
  if (h < 6) return "Boa madru<span>gada</span>";
  if (h < 12) return "Bom <span>dia</span>";
  if (h < 18) return "Boa <span>tarde</span>";
  return "Boa <span>noite</span>";
}

function tile(track, list) {
  const el = document.createElement("div");
  el.className = "tile";
  el.innerHTML =
    `<div class="tile-art">` +
      `<img src="${esc(track.thumbnail)}" alt="" loading="lazy">` +
      `<div class="tile-play"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></div>` +
      `<button class="tile-dl" data-dl="${esc(track.video_id)}" title="baixar para ouvir offline">${DL_ICON}</button>` +
    `</div>` +
    `<div class="tile-title">${esc(track.title)}</div>` +
    `<div class="tile-artist">${esc(track.artist)}</div>`;

  el.addEventListener("click", (ev) => {
    const dl = ev.target.closest("[data-dl]");
    if (dl) {
      ev.stopPropagation();
      downloadTrack(track, dl);
      return;
    }
    playTrack(track, list);
  });
  return el;
}

function renderRow(section) {
  const row = document.createElement("div");
  row.className = "row";

  const head = document.createElement("div");
  head.className = "row-head";
  head.innerHTML =
    `<div>` +
      `<div class="row-title">${esc(section.title)}</div>` +
      `<div class="row-sub">${esc(section.subtitle || "")}</div>` +
    `</div>` +
    `<button class="row-more">tocar tudo</button>`;
  head.querySelector(".row-more").addEventListener("click", () => {
    if (section.tracks.length) playTrack(section.tracks[0], section.tracks);
  });

  const scroll = document.createElement("div");
  scroll.className = "row-scroll";
  section.tracks.forEach((t) => scroll.appendChild(tile(t, section.tracks)));

  // Roda do mouse rola o carrossel na horizontal, sem levar a pagina junto.
  scroll.addEventListener("wheel", (ev) => {
    if (Math.abs(ev.deltaY) <= Math.abs(ev.deltaX)) return;
    const atStart = scroll.scrollLeft <= 0 && ev.deltaY < 0;
    const atEnd = scroll.scrollLeft >= scroll.scrollWidth - scroll.clientWidth - 1
                  && ev.deltaY > 0;
    if (atStart || atEnd) return;   // deixa a pagina rolar nas pontas
    ev.preventDefault();
    scroll.scrollLeft += ev.deltaY;
  }, { passive: false });

  row.append(head, scroll);
  return row;
}

let homeLoaded = false;

async function loadHome(force = false) {
  if (homeLoaded && !force) return;
  homeLoaded = true;

  $("home-greeting").innerHTML = greeting();
  const box = $("home-sections");
  box.innerHTML = `<div class="loading">montando sua home...</div>`;

  loadChips();

  const res = await api().discover_home(18);
  if (!res.ok) {
    box.innerHTML = `<div class="empty">${esc(res.error)}</div>`;
    return;
  }

  box.innerHTML = "";
  res.sections.forEach((section) => box.appendChild(renderRow(section)));

  const all = res.sections.flatMap((s) => s.tracks);
  refreshDownloadMarks(all, box);
}

async function loadChips() {
  const box = $("home-chips");
  if (box.children.length) return;
  const res = await api().discover_categories();
  if (!res.ok) return;

  const add = (item, cls) => {
    const chip = document.createElement("button");
    chip.className = `chip ${cls}`;
    chip.textContent = item.label;
    chip.addEventListener("click", () => openCategory(item.id, item.label));
    box.appendChild(chip);
  };
  res.genres.forEach((g) => add(g, "genre"));
  res.moods.forEach((m) => add(m, "mood"));
  res.decades.forEach((d) => add(d, "decade"));
}

$("home-refresh").addEventListener("click", () => {
  toast("buscando novas sugestões...");
  loadHome(true);
});

/* ===== Categoria ===== */

let categoryTracks = [];

async function openCategory(categoryId, label) {
  showView("category");
  $("category-title").textContent = label;
  $("category-tracks").innerHTML = `<div class="loading">carregando ${esc(label)}...</div>`;

  const res = await api().discover_category(categoryId, 24);
  if (!res.ok) {
    $("category-tracks").innerHTML = `<div class="empty">${esc(res.error)}</div>`;
    return;
  }
  categoryTracks = res.tracks;
  renderList("category-tracks", res.tracks);
  refreshDownloadMarks(res.tracks, $("category-tracks"));
}

$("category-play").addEventListener("click", () => {
  if (categoryTracks.length) playTrack(categoryTracks[0], categoryTracks);
});
$("category-radio").addEventListener("click", async () => {
  if (!categoryTracks.length) return;
  await radioFromTrack(categoryTracks[0]);
});
$("category-back").addEventListener("click", () => showView("home"));

/* ===== Baixar playlist inteira ===== */

$("download-playlist").addEventListener("click", async () => {
  if (!state.playlistId) return;
  const btn = $("download-playlist");
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = "Enfileirando...";

  const res = await api().cache_playlist(state.playlistId);
  btn.disabled = false;
  btn.textContent = original;

  if (!res.ok) return toast(res.error, true);
  if (!res.queued) return toast(`todas as ${res.already} faixas já estão offline`);

  catOn.downloadPlaylist();
  toast(`baixando ${res.queued} faixas em background`);
  refreshCacheInfo();
  // Atualiza os marcadores conforme os downloads terminam.
  const poll = setInterval(async () => {
    const stats = await api().cache_stats();
    refreshCacheInfo();
    if (!stats.stats.downloading) {
      clearInterval(poll);
      openPlaylist(state.playlistId);
      toast("download da playlist concluído");
    }
  }, 5000);
});


/* ===== Sobre / diagnóstico ===== */

let diagCache = null;

async function loadAbout() {
  const res = await api().diagnostics();
  if (!res.ok) return;
  diagCache = res;

  $("about-version").textContent = `AptPlayer ${res.version}`;
  api().check_update().then((u) => {
    const el = $("about-version");
    if (u.ok && u.update) {
      el.innerHTML = `AptPlayer ${res.version}<br><span style="color:var(--yellow)">v${u.latest} disponível</span>`;
    } else if (u.reason === "not_configured") {
      el.innerHTML = `AptPlayer ${res.version}<br>` +
        `<span style="font-size:11px;color:var(--text-faint)">verificação não configurada</span>`;
    }
  });
  $("about-diag").innerHTML =
    `Internet: ${res.online ? "conectado" : "offline"}<br>` +
    `IA: ${res.ollama ? (res.model || "sem modelo") : "Ollama desligado"}<br>` +
    `${res.tracks} faixas · ${res.playlists} playlists · ${res.cache.files} em cache`;
}

$("check-update")?.addEventListener("click", async () => {
  const btn = $("check-update");
  btn.disabled = true;
  btn.textContent = "Verificando...";

  const res = await api().check_update();
  btn.disabled = false;
  btn.textContent = "Procurar atualização";

  if (!res.ok) {
    const why = {
      not_configured: "verificação de atualização ainda não configurada — publique o site primeiro",
      offline: "sem conexão com o servidor de atualizações",
      not_published: "o site está no ar, mas o version.json ainda não foi publicado",
      bad_response: "o servidor respondeu algo inesperado",
    }[res.reason] || "não consegui verificar";
    return toast(why, true);
  }
  if (!res.update) return toast(`você já está na versão mais recente (${res.current})`);

  showUpdateDialog(res);
});

/** Diálogo de atualização: baixa e instala sozinho quando possível. */
async function showUpdateDialog(info) {
  const auto = await api().can_auto_update();
  const root = $("modal-root");
  const bg = document.createElement("div");
  bg.className = "modal-bg";

  const notes = info.notes
    ? `<div class="update-notes">${esc(info.notes)}</div>` : "";

  bg.innerHTML =
    `<div class="modal" style="width:440px">` +
      `<h3>Versão ${esc(info.latest)} disponível</h3>` +
      `<div class="update-sub">Você tem a ${esc(info.current)}</div>` +
      notes +
      `<div class="update-bar hidden" id="upd-bar">` +
        `<div class="update-fill" id="upd-fill"></div>` +
      `</div>` +
      `<div class="update-step" id="upd-step"></div>` +
      `<div class="modal-actions">` +
        `<button class="btn" data-act="later">Depois</button>` +
        `<button class="btn primary" data-act="go">` +
          (auto.supported ? "Atualizar agora" : "Baixar") +
        `</button>` +
      `</div>` +
    `</div>`;

  bg.addEventListener("click", (ev) => {
    const act = ev.target.dataset.act;
    if (ev.target === bg || act === "later") {
      bg.remove();
      return;
    }
    if (act !== "go") return;

    if (!auto.supported) {
      // rodando pelo código ou pasta sem permissão: abre o download
      if (info.url) window.open(info.url, "_blank");
      bg.remove();
      return;
    }
    runAutoUpdate(bg, info);
  });

  root.appendChild(bg);
}

async function runAutoUpdate(bg, info) {
  const btn = bg.querySelector('[data-act="go"]');
  const later = bg.querySelector('[data-act="later"]');
  const bar = bg.querySelector("#upd-bar");
  const fill = bg.querySelector("#upd-fill");
  const step = bg.querySelector("#upd-step");

  btn.disabled = true;
  later.disabled = true;
  btn.textContent = "Atualizando...";
  bar.classList.remove("hidden");

  // o .exe puro substitui o que está rodando; o instalador é o plano B
  const url = info.exe || info.url;
  await api().start_auto_update(url, info.latest);

  const poll = setInterval(async () => {
    const p = await api().auto_update_progress();
    fill.style.width = (p.percent || 0) + "%";
    if (p.step) step.textContent = p.step;

    if (!p.done) return;
    clearInterval(poll);

    if (p.ok) {
      step.textContent = "reiniciando o AptPlayer...";
      btn.textContent = "Pronto";
      return;   // o app fecha sozinho em seguida
    }

    btn.disabled = false;
    later.disabled = false;
    btn.textContent = "Tentar de novo";
    step.textContent = p.error || "falhou";
    step.classList.add("update-error");
  }, 400);
}

$("copy-diag")?.addEventListener("click", async () => {
  if (!diagCache) return;
  const text = [
    `AptPlayer ${diagCache.version}`,
    `Python ${diagCache.python} · ${diagCache.frozen ? "exe" : "código"}`,
    `Internet: ${diagCache.online}`,
    `Ollama: ${diagCache.ollama} (${diagCache.model || "sem modelo"})`,
    `Faixas: ${diagCache.tracks} · Playlists: ${diagCache.playlists}`,
    `Cache: ${diagCache.cache.files} arquivos, ${diagCache.cache.size_mb} MB`,
    `Dados: ${diagCache.data_dir}`,
  ].join(String.fromCharCode(10));
  try {
    await navigator.clipboard.writeText(text);
    toast("detalhes copiados");
  } catch {
    toast("não consegui copiar", true);
  }
});


/* ===== Importar do Spotify ===== */

$("spotify-btn")?.addEventListener("click", async () => {
  const url = $("spotify-url").value.trim();
  if (!url) return toast("cole o link da playlist", true);

  const btn = $("spotify-btn");
  btn.disabled = true;
  btn.textContent = "Lendo...";

  const preview = await api().spotify_preview(url);
  btn.disabled = false;
  btn.textContent = "Importar";

  if (!preview.ok) return toast(preview.error, true);

  const amostra = preview.sample
    .map((s) => `${s.artist} — ${s.title}`)
    .join(" · ");

  modal({
    title: `${preview.name} (${preview.count} faixas)`,
    fields: [{ value: preview.name, placeholder: "nome da playlist aqui" }],
    confirmText: "Importar",
    onConfirm: ([name]) => startSpotifyImport(url, name, preview.count),
  });
  toast(amostra, false);
});

async function startSpotifyImport(url, name, total) {
  const btn = $("spotify-btn");
  btn.disabled = true;
  btn.textContent = "Importando...";
  toast(`importando ${total} faixas — isso leva alguns minutos`);

  await api().spotify_import(url, name, 0);

  const poll = setInterval(async () => {
    const p = await api().spotify_progress();
    if (p.step) btn.textContent = `${p.found}/${p.total || total}`;

    if (!p.done) return;
    clearInterval(poll);
    btn.disabled = false;
    btn.textContent = "Importar";

    if (!p.ok) return toast(p.error || "falhou", true);

    await loadPlaylists();
    toast(`"${p.name}": ${p.found} de ${p.total} faixas importadas`);
    catOn.playlistCreated();
    if (p.playlist_id) openPlaylist(p.playlist_id);
  }, 700);
}


/* ===== Conta e sincronização ===== */

async function loadAccount() {
  const res = await api().account_status();
  const title = $("account-title");
  const desc = $("account-desc");
  const forms = $("account-forms");

  if (!res.configured) {
    title.textContent = "Conta (não configurada)";
    desc.innerHTML = "Este build não tem servidor de conta configurado. " +
      "Use o backup em arquivo, ao lado — funciona igual para trocar de PC.";
    forms.innerHTML = "";
    return;
  }

  if (res.user) {
    title.textContent = "Conectado";
    desc.textContent = "Suas playlists podem ser salvas na nuvem e recuperadas em outro PC.";
    forms.innerHTML =
      `<div class="account-user">${esc(res.user.email)}</div>` +
      `<div class="account-row">` +
        `<button class="btn primary" id="sync-up">Enviar</button>` +
        `<button class="btn" id="sync-down">Baixar</button>` +
      `</div>` +
      `<button class="btn ghost" id="sign-out">Sair</button>` +
      `<div class="sync-hint">Enviar substitui o backup da nuvem. ` +
      `Baixar mescla com o que já existe aqui.</div>`;

    $("sync-up").addEventListener("click", async () => {
      const btn = $("sync-up");
      btn.disabled = true; btn.textContent = "Enviando...";
      const r = await api().account_upload();
      btn.disabled = false; btn.textContent = "Enviar";
      toast(r.ok ? `${r.tracks} faixas e ${r.playlists} playlists salvas`
                 : r.error, !r.ok);
    });

    $("sync-down").addEventListener("click", async () => {
      const btn = $("sync-down");
      btn.disabled = true; btn.textContent = "Baixando...";
      const r = await api().account_download(false);
      btn.disabled = false; btn.textContent = "Baixar";
      if (!r.ok) return toast(r.error, true);
      toast(`${r.tracks} faixas e ${r.playlists} playlists recuperadas`);
      loadPlaylists(); loadHome(true);
    });

    $("sign-out").addEventListener("click", async () => {
      await api().account_logout();
      loadAccount();
      toast("desconectado");
    });
    return;
  }

  title.textContent = "Entrar";
  desc.textContent = "Faça login para salvar suas playlists na nuvem e recuperá-las em outro PC.";
  forms.innerHTML =
    `<input id="acc-email" type="text" placeholder="email" autocomplete="off">` +
    `<input id="acc-pass" type="password" placeholder="senha">` +
    `<div class="account-row">` +
      `<button class="btn primary" id="acc-login">Entrar</button>` +
      `<button class="btn" id="acc-signup">Criar conta</button>` +
    `</div>`;

  const creds = () => [$("acc-email").value.trim(), $("acc-pass").value];

  $("acc-login").addEventListener("click", async () => {
    const [email, pass] = creds();
    if (!email || !pass) return toast("preencha email e senha", true);
    const btn = $("acc-login");
    btn.disabled = true; btn.textContent = "Entrando...";
    const r = await api().account_login(email, pass);
    btn.disabled = false; btn.textContent = "Entrar";
    if (!r.ok) return toast(r.error, true);
    toast(`bem-vindo, ${r.email}`);
    loadAccount();
  });

  $("acc-signup").addEventListener("click", async () => {
    const [email, pass] = creds();
    if (!email || !pass) return toast("preencha email e senha", true);
    const btn = $("acc-signup");
    btn.disabled = true; btn.textContent = "Criando...";
    const r = await api().account_signup(email, pass);
    btn.disabled = false; btn.textContent = "Criar conta";
    if (!r.ok) return toast(r.error, true);
    if (r.needs_confirmation) return toast(r.message, false);
    toast("conta criada");
    loadAccount();
  });
}

$("export-backup")?.addEventListener("click", async () => {
  const r = await api().export_backup();
  if (r.cancelled) return;
  toast(r.ok ? `${r.tracks} faixas e ${r.playlists} playlists salvas em arquivo`
             : r.error, !r.ok);
});

$("import-backup")?.addEventListener("click", async () => {
  const r = await api().import_backup(false);
  if (r.cancelled) return;
  if (!r.ok) return toast(r.error, true);
  toast(`${r.tracks} faixas e ${r.playlists} playlists importadas`);
  loadPlaylists(); loadHome(true);
});


/* mostra e esconde a caixa de importação do Spotify */
$("open-spotify")?.addEventListener("click", () => {
  const box = $("spotify-box");
  box.classList.toggle("hidden");
  if (!box.classList.contains("hidden")) $("spotify-url").focus();
});
$("close-spotify")?.addEventListener("click", () => {
  $("spotify-box").classList.add("hidden");
});
$("spotify-url")?.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") $("spotify-btn").click();
});


/* o chat so e inicializado quando a aba e aberta pela primeira vez */
let roomsReady = false;
function initRoomsOnce() {
  if (roomsReady) return;
  roomsReady = true;
  initRooms();
}

/* avisa a sala quando a reproducao muda, no modo ouvir junto */
audio.addEventListener("play", () => {
  if (typeof pushPlayback === "function") pushPlayback();
});
audio.addEventListener("pause", () => {
  if (typeof pushPlayback === "function") pushPlayback();
});


/* ===== Discord Rich Presence ===== */

const discord = { on: false, lastId: null };

async function loadDiscord() {
  const res = await api().discord_status();
  const desc = $("discord-desc");
  const toggle = $("discord-toggle");
  if (!desc || !toggle) return;

  if (!res.configured) {
    desc.innerHTML =
      "Falta o Application ID do Discord. O passo a passo está no arquivo " +
      "<strong>DISCORD.md</strong>, na pasta do projeto — leva uns 5 minutos.";
    toggle.disabled = true;
    toggle.checked = false;
    return;
  }

  toggle.disabled = false;
  desc.textContent = res.discord_running
    ? "Mostra a música que você está ouvindo no seu perfil do Discord."
    : "Abra o Discord para o status aparecer.";

  let want = false;
  try { want = localStorage.getItem("aptplayer-discord") === "on"; } catch {}
  toggle.checked = want;
  discord.on = want;
  if (want) api().discord_enable();
}

$("discord-toggle")?.addEventListener("change", async (ev) => {
  if (ev.target.checked) {
    const res = await api().discord_enable();
    if (!res.ok) {
      ev.target.checked = false;
      return toast(res.error, true);
    }
    discord.on = true;
    try { localStorage.setItem("aptplayer-discord", "on"); } catch {}
    toast("Discord conectado");
    pushDiscord();
  } else {
    await api().discord_disable();
    discord.on = false;
    discord.lastId = null;
    try { localStorage.setItem("aptplayer-discord", "off"); } catch {}
    toast("Rich Presence desligado");
  }
});

/** Envia ao Discord o que está tocando agora. */
function pushDiscord() {
  if (!discord.on) return;
  const track = state.queue[state.index];
  if (!track) {
    api().discord_update(null, false, 0, 0);
    discord.lastId = null;
    return;
  }
  api().discord_update(
    { video_id: track.video_id, title: track.title, artist: track.artist },
    !audio.paused,
    audio.currentTime || 0,
    audio.duration || track.duration || 0,
  );
  discord.lastId = track.video_id;
}

audio.addEventListener("play", pushDiscord);
audio.addEventListener("pause", pushDiscord);

/* o Discord limita atualizações; uma a cada 15s é suficiente e seguro */
setInterval(() => {
  if (discord.on && !audio.paused) pushDiscord();
}, 15000);


/* ===== Barra de titulo propria ===== */

$("tb-min")?.addEventListener("click", () => api().window_minimize());
$("tb-close")?.addEventListener("click", () => api().window_close());

$("tb-max")?.addEventListener("click", async () => {
  const res = await api().window_toggle_max();
  const btn = $("tb-max");
  // icone muda para indicar que da para restaurar
  btn.innerHTML = res.maximized
    ? `<svg viewBox="0 0 12 12"><rect x="2" y="4" width="6" height="6"/><path d="M4 4V2h6v6H8"/></svg>`
    : `<svg viewBox="0 0 12 12"><rect x="2.5" y="2.5" width="7" height="7"/></svg>`;
});

/* duplo clique na barra maximiza, como no Windows */
document.querySelector(".tb-drag")?.addEventListener("dblclick", () => {
  $("tb-max")?.click();
});

/** Mostra a faixa atual na barra de titulo. */
function updateTitlebar(track) {
  const el = $("tb-now");
  if (!el) return;
  el.textContent = track ? `${track.artist} - ${track.title}` : "";
}
