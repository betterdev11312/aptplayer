/* Retrospectiva, equalizer e teclas globais — parte da interface. */

/* ===== Retrospectiva ===== */

function fmtDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  if (h >= 24) {
    const d = Math.floor(h / 24);
    return `${d}d ${h % 24}h`;
  }
  return h ? `${h}h ${m}min` : `${m}min`;
}

function rankRow(position, name, sub, plays, max) {
  const pct = max ? Math.round((plays / max) * 100) : 0;
  return (
    `<div class="rank-row" style="--pct:${pct}%">` +
      `<div class="rank-pos">${position}</div>` +
      `<div>` +
        `<div class="rank-name">${esc(name)}</div>` +
        (sub ? `<div class="rank-sub">${esc(sub)}</div>` : "") +
      `</div>` +
      `<div class="rank-plays">${plays}×</div>` +
    `</div>`
  );
}

async function loadStats() {
  const days = Number($("stats-period").value || 0);
  const box = $("stats-body");
  box.innerHTML = `<div class="loading">calculando...</div>`;

  const s = await api().get_stats(days);
  if (!s.ok) {
    box.innerHTML = `<div class="empty">${esc(s.error)}</div>`;
    return;
  }
  if (!s.total_plays) {
    box.innerHTML = `<div class="empty">nada tocado neste período</div>`;
    return;
  }

  const maxArtist = s.top_artists[0]?.plays || 1;
  const maxTrack = s.top_tracks[0]?.plays || 1;
  const peakHour = s.by_hour.reduce((a, b) => (b.plays > a.plays ? b : a), s.by_hour[0]);
  const maxHour = peakHour.plays || 1;

  let html =
    `<div class="stat-grid">` +
      `<div class="stat-box"><div class="stat-num">${s.total_plays}</div>` +
        `<div class="stat-label">reproduções</div></div>` +
      `<div class="stat-box"><div class="stat-num">${fmtDuration(s.total_seconds)}</div>` +
        `<div class="stat-label">ouvindo</div></div>` +
      `<div class="stat-box"><div class="stat-num">${s.unique_artists}</div>` +
        `<div class="stat-label">artistas</div></div>` +
      `<div class="stat-box"><div class="stat-num">${s.unique_tracks}</div>` +
        `<div class="stat-label">músicas</div></div>` +
      `<div class="stat-box"><div class="stat-num">${s.streak.best}</div>` +
        `<div class="stat-label">dias seguidos (recorde)</div></div>` +
    `</div>`;

  if (s.top_artists.length) {
    html += `<div class="stat-section">` +
      `<div class="stat-title">Artistas mais ouvidos</div>` +
      `<div class="rank">` +
      s.top_artists.map((a, i) =>
        rankRow(i + 1, a.name, "", a.plays, maxArtist)).join("") +
      `</div></div>`;
  }

  if (s.top_tracks.length) {
    html += `<div class="stat-section">` +
      `<div class="stat-title">Músicas mais tocadas</div>` +
      `<div class="rank">` +
      s.top_tracks.map((t, i) =>
        rankRow(i + 1, t.title, t.artist, t.plays, maxTrack)).join("") +
      `</div></div>`;
  }

  // gráfico por hora do dia
  html += `<div class="stat-section">` +
    `<div class="stat-title">Quando você ouve (30 dias)</div>` +
    `<div class="hours">` +
    s.by_hour.map((h) => {
      const height = Math.max(2, Math.round((h.plays / maxHour) * 100));
      const peak = h.plays === maxHour && h.plays > 0 ? " peak" : "";
      return `<div class="hour-bar${peak}" style="height:${height}%" ` +
             `title="${h.hour}h — ${h.plays} reproduções"></div>`;
    }).join("") +
    `</div>` +
    `<div class="hours-axis"><span>00h</span><span>06h</span>` +
    `<span>12h</span><span>18h</span><span>23h</span></div>` +
    `</div>`;

  if (s.genres.length) {
    const maxGenre = s.genres[0].plays || 1;
    html += `<div class="stat-section">` +
      `<div class="stat-title">Gêneros</div><div class="rank">` +
      s.genres.map((g, i) => rankRow(i + 1, g.name, "", g.plays, maxGenre)).join("") +
      `</div></div>`;
  }

  if (s.first) {
    const when = new Date(s.first.played_at * 1000).toLocaleDateString("pt-BR");
    html += `<div class="stat-section">` +
      `<div class="stat-title">A primeira</div>` +
      `<div class="rank"><div class="rank-row">` +
        `<div class="rank-pos">♪</div><div>` +
        `<div class="rank-name">${esc(s.first.title)}</div>` +
        `<div class="rank-sub">${esc(s.first.artist)} · ${when}</div>` +
        `</div><div class="rank-plays"></div>` +
      `</div></div></div>`;
  }

  box.innerHTML = html;
}

$("stats-period")?.addEventListener("change", loadStats);

/* ===== Equalizer ===== */

function renderEq() {
  const presets = $("eq-presets");
  const bands = $("eq-bands");
  if (!presets || presets.children.length) return;

  const names = {
    flat: "Neutro", bass: "Grave", vocal: "Vocal", treble: "Agudo",
    rock: "Rock", eletro: "Eletrônica", podcast: "Podcast",
  };
  Object.keys(EQ_PRESETS).forEach((key) => {
    const btn = document.createElement("button");
    btn.className = "eq-preset";
    btn.dataset.preset = key;
    btn.textContent = names[key] || key;
    btn.addEventListener("click", () => {
      fxApplyPreset(key);
      presets.querySelectorAll(".eq-preset").forEach((b) =>
        b.classList.toggle("active", b.dataset.preset === key));
      toast(`equalizer: ${names[key] || key}`);
    });
    presets.appendChild(btn);
  });

  const saved = loadEq();
  EQ_BANDS.forEach((band, i) => {
    const value = saved?.gains?.[i] ?? 0;
    const el = document.createElement("div");
    el.className = "eq-band";
    el.innerHTML =
      `<div class="eq-val">${value > 0 ? "+" : ""}${Math.round(value)}</div>` +
      `<input class="eq-slider" type="range" min="-12" max="12" step="1" value="${value}">` +
      `<div class="eq-hz">${band.label}</div>`;

    const slider = el.querySelector(".eq-slider");
    slider.addEventListener("input", () => {
      const db = Number(slider.value);
      el.querySelector(".eq-val").textContent = (db > 0 ? "+" : "") + db;
      if (fxSetup()) fxSetBand(i, db);
      presets.querySelectorAll(".eq-preset").forEach((b) =>
        b.classList.remove("active"));
    });
    bands.appendChild(el);
  });

  if (saved?.preset && saved.preset !== "custom") {
    presets.querySelector(`[data-preset="${saved.preset}"]`)?.classList.add("active");
  }
}

$("viz-mode")?.addEventListener("change", (ev) => {
  fxSetView(ev.target.value);
  toast(`visualização: ${ev.target.selectedOptions[0].textContent.toLowerCase()}`);
});

/* ===== Teclas de mídia globais ===== */

$("hotkeys-toggle")?.addEventListener("change", async (ev) => {
  if (ev.target.checked) {
    const r = await api().hotkeys_start();
    if (r.active) {
      toast("teclas de mídia ligadas — funcionam com o app minimizado");
      try { localStorage.setItem("aptplayer-hotkeys", "on"); } catch {}
    } else {
      ev.target.checked = false;
      toast("outro programa já está usando essas teclas", true);
    }
  } else {
    await api().hotkeys_stop();
    try { localStorage.setItem("aptplayer-hotkeys", "off"); } catch {}
    toast("teclas de mídia desligadas");
  }
});

async function initAudioSettings() {
  renderEq();

  const viz = $("viz-mode");
  if (viz) {
    try { viz.value = localStorage.getItem("aptplayer-viz") || "bars"; }
    catch { viz.value = "bars"; }
  }

  const toggle = $("hotkeys-toggle");
  if (toggle) {
    const status = await api().hotkeys_status();
    toggle.checked = status.active;
  }
}

/* Liga as teclas globais no boot, se o usuário deixou ativado. */
async function restoreHotkeys() {
  let want = "off";
  try { want = localStorage.getItem("aptplayer-hotkeys") || "off"; } catch {}
  if (want === "on") await api().hotkeys_start();
}
