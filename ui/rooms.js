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
  startTimer: 0,           // play agendado
  countTimer: 0,           // contagem regressiva
  scheduledFor: null,      // horário já agendado, para não repetir
  lastPushed: null,        // última faixa anunciada à sala
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
  clearTimeout(room.startTimer);
  clearTimeout(room.countTimer);
  hideCountdown();
  room.scheduledFor = null;
  room.lastPushed = null;
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
    // so avisa sobre o que chega depois de abrir a sala
    if (!first) notifyMessage(m);
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

  // busca os perfis para mostrar foto e nickname escolhidos
  const perfis = (await api().profile_many(res.members.map((m) => m.id)))
    .profiles || {};

  res.members.forEach((m) => {
    const perfil = perfis[m.id] || {};
    const nome = perfil.nickname || m.nickname;
    const el = document.createElement("div");
    el.className = "room-member" + (m.online ? "" : " offline");

    const foto = perfil.avatar
      ? `<img src="${esc(perfil.avatar)}" alt="">`
      : esc((nome || "?").charAt(0).toUpperCase());

    const playing = m.now_playing && m.now_playing.title
      ? `<div class="member-playing">♪ ${esc(m.now_playing.title)}</div>`
      : `<div class="member-playing quiet">em silêncio</div>`;

    el.innerHTML =
      `<div class="member-row">` +
        `<div class="member-avatar">${foto}</div>` +
        `<div style="min-width:0;flex:1">` +
          `<div class="member-name">${esc(nome)}</div>` +
          playing +
        `</div>` +
      `</div>` +
      (perfil.bio ? `<div class="member-playing quiet">${esc(perfil.bio)}</div>` : "");
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

  // quem liga com música tocando agenda o início para todos
  const track = state.queue[state.index];
  if (track) await startTogether(track, audio.currentTime || 0);

  room.pollSync = setInterval(syncPlayback, 3000);
  syncPlayback();
}

/* Quantos segundos de antecedência o início é agendado. Precisa dar tempo
   de todo mundo receber o aviso e carregar o áudio. */
const SYNC_DELAY = 5;

/** Agenda o início da faixa para daqui a alguns segundos, para todos. */
async function startTogether(track, position = 0) {
  if (!room.id) return;

  audio.pause();
  showCountdown(SYNC_DELAY);

  await api().room_set_playback(room.id, {
    video_id: track.video_id, title: track.title,
    artist: track.artist, thumbnail: track.thumbnail,
  }, position, true, SYNC_DELAY);

  // quem agendou também espera: todos começam juntos
  scheduleLocalStart(track, position, SYNC_DELAY);
}

/** Carrega o áudio agora e dá play no instante combinado. */
async function scheduleLocalStart(track, position, secondsLeft) {
  room.applyingRemote = true;

  const current = state.queue[state.index];
  if (!current || current.video_id !== track.video_id) {
    await playTrack(track, [track]);
  }
  audio.pause();                       // carregado, mas parado

  // espera o áudio ter dados suficientes antes de posicionar
  await waitReady();
  try { audio.currentTime = position; } catch {}

  const waitMs = Math.max(0, secondsLeft * 1000 - 120);
  clearTimeout(room.startTimer);
  room.startTimer = setTimeout(() => {
    audio.play().catch(() => {});
    hideCountdown();
    setTimeout(() => { room.applyingRemote = false; }, 800);
  }, waitMs);
}

/** Espera o elemento de áudio ter dados (readyState 3+), com teto de 4s. */
function waitReady(timeout = 4000) {
  return new Promise((resolve) => {
    if (audio.readyState >= 3) return resolve();
    const done = () => { cleanup(); resolve(); };
    const cleanup = () => {
      audio.removeEventListener("canplay", done);
      clearTimeout(timer);
    };
    const timer = setTimeout(done, timeout);
    audio.addEventListener("canplay", done, { once: true });
  });
}

/* ===== Contagem regressiva na tela ===== */

function showCountdown(seconds) {
  let el = $("sync-countdown");
  if (!el) {
    el = document.createElement("div");
    el.id = "sync-countdown";
    el.className = "sync-countdown";
    document.body.appendChild(el);
  }
  el.classList.add("show");

  const tick = (left) => {
    el.innerHTML =
      `<div class="sync-num">${left}</div>` +
      `<div class="sync-label">todos começam juntos</div>`;
    if (left > 0) room.countTimer = setTimeout(() => tick(left - 1), 1000);
    else hideCountdown();
  };
  clearTimeout(room.countTimer);
  tick(Math.ceil(seconds));
}

function hideCountdown() {
  clearTimeout(room.countTimer);
  $("sync-countdown")?.classList.remove("show");
}

async function pushPlayback() {
  if (!room.id || !room.listenTogether || room.applyingRemote) return;
  const track = state.queue[state.index];
  if (!track) return;

  // Troca de faixa vira um novo agendamento, para todos pularem juntos.
  if (track.video_id !== room.lastPushed) {
    room.lastPushed = track.video_id;
    return startTogether(track, 0);
  }

  await api().room_set_playback(room.id, {
    video_id: track.video_id, title: track.title,
    artist: track.artist, thumbnail: track.thumbnail,
  }, audio.currentTime || 0, !audio.paused, 0);
}

async function syncPlayback() {
  if (!room.id || !room.listenTogether) return;

  const res = await api().room_get_playback(room.id);
  if (!res.ok || !res.playback) return;

  const p = res.playback;
  if (!p.track || !p.track.video_id) return;

  // Início agendado que ainda não chegou: prepara e espera.
  if (typeof p.starts_in === "number" && p.starts_in > 0.3) {
    if (room.scheduledFor !== p.start_at) {
      room.scheduledFor = p.start_at;
      showCountdown(p.starts_in);
      scheduleLocalStart(p.track, p.start_position || 0, p.starts_in);
    }
    return;
  }

  if (p.mine) return;                  // daqui pra baixo, só o que veio de fora
  if (room.applyingRemote) return;     // já estou aplicando um agendamento

  const current = state.queue[state.index];
  const sameTrack = current && current.video_id === p.track.video_id;

  room.applyingRemote = true;
  try {
    if (!sameTrack) {
      // entrou no meio: começa já no ponto certo
      await playTrack(p.track, [p.track]);
      await waitReady();
      if (audio.duration) {
        audio.currentTime = Math.min(p.position, audio.duration - 1);
      }
      toast(`tocando junto: ${p.track.title}`);
    } else {
      // mesma faixa: corrige só se o desvio for audível
      const drift = Math.abs((audio.currentTime || 0) - p.position);
      if (drift > 1.5 && audio.duration) {
        audio.currentTime = Math.min(p.position, audio.duration - 1);
      }
      if (p.playing && audio.paused) audio.play().catch(() => {});
      if (!p.playing && !audio.paused) audio.pause();
    }
  } finally {
    setTimeout(() => { room.applyingRemote = false; }, 900);
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

/* ===== Perfil ===== */

const profile = { data: null, avatar: null, cache: {} };

async function loadProfile() {
  const res = await api().profile_get();
  const hint = $("profile-hint");

  if (!res.ok) {
    if (hint) hint.textContent = res.error;
    return;
  }

  profile.data = res.profile;
  const nick = $("profile-nick");
  const bio = $("profile-bio");
  if (nick) nick.value = res.profile.nickname || "";
  if (bio) bio.value = res.profile.bio || "";

  renderAvatar(res.profile.avatar, res.profile.nickname);
  if (hint) {
    hint.textContent = res.profile.new
      ? "salve para criar seu perfil"
      : "seu perfil aparece para os amigos nas salas";
  }
}

function renderAvatar(dataUrl, nickname) {
  const box = $("profile-avatar");
  if (!box) return;
  if (dataUrl) {
    box.innerHTML = `<img src="${esc(dataUrl)}" alt="">`;
  } else {
    const letra = (nickname || "?").trim().charAt(0).toUpperCase() || "?";
    box.innerHTML = `<span>${esc(letra)}</span>`;
  }
}

$("profile-avatar")?.addEventListener("click", async () => {
  const res = await api().profile_pick_avatar();
  if (res.cancelled) return;
  if (!res.ok) return toast(res.error, true);

  profile.avatar = res.avatar;
  renderAvatar(res.avatar, $("profile-nick")?.value);
  toast("foto escolhida — clique em salvar");
});

$("profile-save")?.addEventListener("click", async () => {
  const btn = $("profile-save");
  btn.disabled = true;
  btn.textContent = "Salvando...";

  const res = await api().profile_save(
    $("profile-nick")?.value || "",
    $("profile-bio")?.value || "",
    profile.avatar,          // null mantém a foto atual
  );

  btn.disabled = false;
  btn.textContent = "Salvar perfil";

  if (!res.ok) return toast(res.error, true);
  profile.avatar = null;
  profile.data = res.profile;
  toast("perfil salvo");
  if (room.id) refreshMembers();
});

/* ===== Notificações de mensagem ===== */

/** Bipe curto, gerado na hora — evita carregar arquivo de som. */
function playNotificationSound() {
  let quer = true;
  try { quer = localStorage.getItem("aptplayer-notify-sound") !== "off"; } catch {}
  if (!quer) return;

  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    const ctx = new Ctx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.setValueAtTime(1180, ctx.currentTime + 0.09);

    gain.gain.setValueAtTime(0.0001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.3);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.32);
    // fecha o contexto para não acumular recursos
    setTimeout(() => ctx.close().catch(() => {}), 600);
  } catch {
    // sem áudio disponível: a notificação visual ainda aparece
  }
}

/** Avisa sobre uma mensagem nova que não é sua. */
function notifyMessage(m) {
  let quer = true;
  try { quer = localStorage.getItem("aptplayer-notify") !== "off"; } catch {}
  if (!quer || m.mine) return;

  const corpo = m.body || (m.track ? `enviou ${m.track.title}` : "");
  api().notify(`${m.nickname} · ${room.name}`, corpo);
  playNotificationSound();
}

$("notify-toggle")?.addEventListener("change", (ev) => {
  try {
    localStorage.setItem("aptplayer-notify", ev.target.checked ? "on" : "off");
  } catch {}
  toast(ev.target.checked ? "notificações ligadas" : "notificações desligadas");
  if (ev.target.checked) {
    api().notify("AptPlayer", "as notificações estão funcionando");
    playNotificationSound();
  }
});

$("notify-sound")?.addEventListener("change", (ev) => {
  try {
    localStorage.setItem("aptplayer-notify-sound", ev.target.checked ? "on" : "off");
  } catch {}
  if (ev.target.checked) playNotificationSound();
});

function initNotifyToggles() {
  try {
    const t = $("notify-toggle");
    const s = $("notify-sound");
    if (t) t.checked = localStorage.getItem("aptplayer-notify") !== "off";
    if (s) s.checked = localStorage.getItem("aptplayer-notify-sound") !== "off";
  } catch {}
}
