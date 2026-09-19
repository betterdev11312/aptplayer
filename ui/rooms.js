/* Salas de chat entre amigos.
 *
 * Atualiza por polling: mensagens a cada 3s, presença a cada 15s. Para um
 * punhado de amigos isso é suficiente e evita manter WebSocket aberto.
 */

const room = {
  id: null,
  name: "",
  code: "",
  lastId: 0,
  pollMsg: 0,
  pollMembers: 0,
  pollSync: 0,
  listenTogether: false,
  applyingRemote: false,   // evita eco: mudança vinda da sala não volta pra sala
};

/* ===== Lista de salas ===== */

async function loadRooms() {
  const box = $("rooms-list");
  if (!box) return;

  const status = await api().account_status();
  if (!status.user) {
    box.innerHTML =
      `<div class="empty">faça login em Ajustes → Conta para usar o chat</div>`;
    $("room-actions")?.classList.add("hidden");
    return;
  }
  $("room-actions")?.classList.remove("hidden");

  const res = await api().room_list();
  if (!res.ok) {
    box.innerHTML = `<div class="empty">${esc(res.error)}</div>`;
    return;
  }
  if (!res.rooms.length) {
    box.innerHTML = `<div class="empty">nenhuma sala — crie uma ou entre com um código</div>`;
    return;
  }

  box.innerHTML = "";
  res.rooms.forEach((r) => {
    const el = document.createElement("div");
    el.className = "room-item" + (r.id === room.id ? " active" : "");
    el.innerHTML =
      `<div class="room-name">${esc(r.name)}</div>` +
      `<div class="room-code">${esc(r.code)}</div>`;
    el.addEventListener("click", () => openRoom(r));
    box.appendChild(el);
  });
}

/* ===== Entrar e sair ===== */

async function openRoom(info) {
  closeRoom();

  room.id = info.id;
  room.name = info.name;
  room.code = info.code;
  room.lastId = 0;

  $("room-title").textContent = info.name;
  $("room-code-tag").textContent = info.code;
  $("room-view").classList.remove("hidden");
  $("rooms-empty")?.classList.add("hidden");
  $("room-log").innerHTML = `<div class="loading">carregando...</div>`;

  await refreshMessages(true);
  await refreshMembers();
  beat();

  room.pollMsg = setInterval(refreshMessages, 3000);
  room.pollMembers = setInterval(() => { refreshMembers(); beat(); }, 15000);
  loadRooms();
}

function closeRoom() {
  clearInterval(room.pollMsg);
  clearInterval(room.pollMembers);
  clearInterval(room.pollSync);
  room.pollMsg = room.pollMembers = room.pollSync = 0;
  room.listenTogether = false;
  $("listen-together")?.classList.remove("on");
}

/* ===== Mensagens ===== */

async function refreshMessages(first = false) {
  if (!room.id) return;
  const res = await api().room_history(room.id, first ? 0 : room.lastId);
  if (!res.ok) {
    if (first) $("room-log").innerHTML = `<div class="empty">${esc(res.error)}</div>`;
    return;
  }

  const log = $("room-log");
  if (first) log.innerHTML = "";
  if (!res.messages.length && first) {
    log.innerHTML = `<div class="empty">ninguém falou nada ainda</div>`;
    return;
  }

  const wasAtBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 60;

  res.messages.forEach((m) => {
    if (first && !log.querySelector(".room-msg")) log.innerHTML = "";
    log.appendChild(messageBubble(m));
    room.lastId = Math.max(room.lastId, m.id);
  });

  if (first || wasAtBottom) log.scrollTop = log.scrollHeight;
}

function messageBubble(m) {
  const el = document.createElement("div");
  el.className = "room-msg" + (m.mine ? " mine" : "");

  const when = new Date(m.created_at).toLocaleTimeString("pt-BR",
    { hour: "2-digit", minute: "2-digit" });

  let inner =
    `<div class="room-msg-head">` +
      `<span class="room-who">${esc(m.nickname)}</span>` +
      `<span class="room-time">${when}</span>` +
    `</div>`;

  if (m.body) inner += `<div class="room-body">${esc(m.body)}</div>`;

  if (m.track && m.track.video_id) {
    inner +=
      `<div class="room-track" data-track='${esc(JSON.stringify(m.track))}'>` +
        `<img src="${esc(m.track.thumbnail || "")}" alt="">` +
        `<div class="room-track-meta">` +
          `<div class="room-track-title">${esc(m.track.title || "")}</div>` +
          `<div class="room-track-artist">${esc(m.track.artist || "")}</div>` +
        `</div>` +
        `<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>` +
      `</div>`;
  }

  el.innerHTML = inner;

  el.querySelector(".room-track")?.addEventListener("click", (ev) => {
    try {
      const track = JSON.parse(ev.currentTarget.dataset.track);
      playTrack(track, [track]);
    } catch {}
  });

  return el;
}

async function sendMessage() {
  const input = $("room-input");
  const text = input.value.trim();
  if (!text || !room.id) return;

  input.value = "";
  const res = await api().room_send(room.id, text, null);
  if (!res.ok) return toast(res.error, true);
  refreshMessages();
}

/** Manda a faixa que está tocando para a sala. */
async function shareCurrentTrack() {
  if (!room.id) return toast("entre numa sala primeiro", true);
  const track = state.queue[state.index];
  if (!track) return toast("nada tocando", true);

  const res = await api().room_send(room.id, "", {
    video_id: track.video_id, title: track.title,
    artist: track.artist, thumbnail: track.thumbnail,
  });
  if (!res.ok) return toast(res.error, true);
  refreshMessages();
  toast("faixa enviada para a sala");
}

/* ===== Quem está online ===== */

async function refreshMembers() {
  if (!room.id) return;
  const res = await api().room_members(room.id);
  if (!res.ok) return;

  const box = $("room-members");
  box.innerHTML = "";
  const online = res.members.filter((m) => m.online);
  $("room-online").textContent = `${online.length} online`;

  res.members.forEach((m) => {
    const el = document.createElement("div");
    el.className = "room-member" + (m.online ? "" : " offline");
    const playing = m.now_playing && m.now_playing.title
      ? `<div class="member-playing">♪ ${esc(m.now_playing.title)} — ${esc(m.now_playing.artist || "")}</div>`
      : `<div class="member-playing quiet">em silêncio</div>`;
    el.innerHTML =
      `<div class="member-name">${esc(m.nickname)}</div>` + playing;
    box.appendChild(el);
  });
}

/** Avisa que continua na sala e o que está tocando. */
function beat() {
  if (!room.id) return;
  const track = state.queue[state.index];
  const playing = track && !audio.paused
    ? { title: track.title, artist: track.artist, video_id: track.video_id }
    : null;
  api().room_heartbeat(room.id, playing);
}

/* ===== Ouvir junto ===== */

async function toggleListenTogether() {
  if (!room.id) return toast("entre numa sala primeiro", true);

  room.listenTogether = !room.listenTogether;
  $("listen-together").classList.toggle("on", room.listenTogether);

  if (!room.listenTogether) {
    clearInterval(room.pollSync);
    room.pollSync = 0;
    return toast("ouvir junto desligado");
  }

  toast("ouvir junto ligado — a sala toca a mesma música");

  // quem liga com música tocando define o que todos vão ouvir
  const track = state.queue[state.index];
  if (track && !audio.paused) await pushPlayback();

  room.pollSync = setInterval(syncPlayback, 4000);
  syncPlayback();
}

async function pushPlayback() {
  if (!room.id || !room.listenTogether || room.applyingRemote) return;
  const track = state.queue[state.index];
  if (!track) return;

  await api().room_set_playback(room.id, {
    video_id: track.video_id, title: track.title,
    artist: track.artist, thumbnail: track.thumbnail,
  }, audio.currentTime || 0, !audio.paused);
}

async function syncPlayback() {
  if (!room.id || !room.listenTogether) return;

  const res = await api().room_get_playback(room.id);
  if (!res.ok || !res.playback) return;

  const p = res.playback;
  if (p.mine) return;                       // fui eu que mandei
  if (!p.track || !p.track.video_id) return;

  const current = state.queue[state.index];
  const sameTrack = current && current.video_id === p.track.video_id;

  room.applyingRemote = true;
  try {
    if (!sameTrack) {
      await playTrack(p.track, [p.track]);
      // espera o áudio existir antes de posicionar
      setTimeout(() => {
        if (audio.duration) audio.currentTime = Math.min(p.position, audio.duration - 1);
      }, 900);
      toast(`tocando junto: ${p.track.title}`);
    } else {
      // já é a mesma faixa: corrige só se estiver longe
      const drift = Math.abs((audio.currentTime || 0) - p.position);
      if (drift > 3 && audio.duration) {
        audio.currentTime = Math.min(p.position, audio.duration - 1);
      }
      if (p.playing && audio.paused) audio.play().catch(() => {});
      if (!p.playing && !audio.paused) audio.pause();
    }
  } finally {
    setTimeout(() => { room.applyingRemote = false; }, 1200);
  }
}

/* ===== Ligações ===== */

function initRooms() {
  $("room-send")?.addEventListener("click", sendMessage);
  $("room-input")?.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") sendMessage();
  });
  $("share-track")?.addEventListener("click", shareCurrentTrack);
  $("listen-together")?.addEventListener("click", toggleListenTogether);

  $("create-room")?.addEventListener("click", () => {
    modal({
      title: "Nova sala",
      fields: [{ placeholder: "nome da sala" }],
      confirmText: "Criar",
      onConfirm: async ([name]) => {
        const res = await api().room_create(name);
        if (!res.ok) return toast(res.error, true);
        await loadRooms();
        openRoom(res);
        toast(`sala criada — código ${res.code}`);
      },
    });
  });

  $("join-room")?.addEventListener("click", () => {
    modal({
      title: "Entrar numa sala",
      fields: [{ placeholder: "APT-XXXX" }],
      confirmText: "Entrar",
      onConfirm: async ([code]) => {
        const res = await api().room_join(code);
        if (!res.ok) return toast(res.error, true);
        await loadRooms();
        openRoom(res);
        toast(`você entrou em "${res.name}"`);
      },
    });
  });

  $("copy-room-code")?.addEventListener("click", async () => {
    if (!room.code) return;
    try {
      await navigator.clipboard.writeText(room.code);
      toast(`código ${room.code} copiado — mande para seu amigo`);
    } catch {
      toast(room.code);
    }
  });

  $("leave-room")?.addEventListener("click", () => {
    if (!room.id) return;
    confirmBox("Sair desta sala?", async () => {
      await api().room_leave(room.id);
      closeRoom();
      room.id = null;
      $("room-view").classList.add("hidden");
      loadRooms();
      toast("você saiu da sala");
    });
  });
}
