/* Equalizer e visualização de áudio.
 *
 * Usa a Web Audio API: o <audio> passa por uma cadeia de filtros (o
 * equalizer) e por um analisador que alimenta as barras na tela.
 *
 * A cadeia só é montada no primeiro uso — criar um AudioContext antes de
 * qualquer interação é bloqueado pelo navegador.
 */

const fx = {
  ctx: null,
  source: null,
  analyser: null,
  gain: null,
  bands: [],          // filtros do equalizer
  data: null,         // buffer de frequências
  raf: 0,
  canvas: null,
  view: "bars",       // bars | wave | off
  ready: false,
};

/* Frequências centrais: graves à esquerda, agudos à direita. */
const EQ_BANDS = [
  { hz: 60, label: "60" },
  { hz: 170, label: "170" },
  { hz: 400, label: "400" },
  { hz: 1000, label: "1k" },
  { hz: 3000, label: "3k" },
  { hz: 8000, label: "8k" },
  { hz: 14000, label: "14k" },
];

const EQ_PRESETS = {
  flat:    [0, 0, 0, 0, 0, 0, 0],
  bass:    [7, 5, 2, 0, 0, 0, 1],
  vocal:   [-2, -1, 2, 4, 4, 2, 0],
  treble:  [0, 0, 0, 1, 3, 5, 6],
  rock:    [5, 3, -1, -1, 2, 4, 4],
  eletro:  [6, 4, 0, -2, 1, 4, 5],
  podcast: [-4, -2, 3, 5, 3, 0, -2],
};

function fxSetup() {
  if (fx.ready) return true;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return false;

    fx.ctx = new Ctx();
    fx.source = fx.ctx.createMediaElementSource(audio);

    // equalizer: filtros peaking em série
    fx.bands = EQ_BANDS.map((band) => {
      const filter = fx.ctx.createBiquadFilter();
      filter.type = "peaking";
      filter.frequency.value = band.hz;
      filter.Q.value = 1;
      filter.gain.value = 0;
      return filter;
    });

    fx.analyser = fx.ctx.createAnalyser();
    fx.analyser.fftSize = 256;
    fx.analyser.smoothingTimeConstant = 0.78;
    fx.data = new Uint8Array(fx.analyser.frequencyBinCount);

    fx.gain = fx.ctx.createGain();

    // source -> banda1 -> ... -> bandaN -> gain -> analyser -> saída
    let node = fx.source;
    fx.bands.forEach((band) => {
      node.connect(band);
      node = band;
    });
    node.connect(fx.gain);
    fx.gain.connect(fx.analyser);
    fx.analyser.connect(fx.ctx.destination);

    fx.ready = true;
    return true;
  } catch (err) {
    // Alguns webviews não suportam; o player continua tocando normalmente.
    return false;
  }
}

function fxResume() {
  if (fx.ctx && fx.ctx.state === "suspended") fx.ctx.resume();
}

/* ===== Equalizer ===== */

function fxSetBand(index, db) {
  if (!fx.ready || !fx.bands[index]) return;
  fx.bands[index].gain.value = db;
  saveEq();
}

function fxApplyPreset(name) {
  const values = EQ_PRESETS[name] || EQ_PRESETS.flat;
  if (!fxSetup()) return;
  values.forEach((db, i) => {
    if (fx.bands[i]) fx.bands[i].gain.value = db;
  });
  document.querySelectorAll(".eq-slider").forEach((el, i) => {
    el.value = values[i] ?? 0;
    const out = el.parentElement.querySelector(".eq-val");
    if (out) out.textContent = (values[i] > 0 ? "+" : "") + (values[i] ?? 0);
  });
  saveEq(name);
}

function saveEq(preset) {
  try {
    localStorage.setItem("aptplayer-eq", JSON.stringify({
      preset: preset || "custom",
      gains: fx.bands.map((b) => b.gain.value),
    }));
  } catch {}
}

function loadEq() {
  try {
    const saved = JSON.parse(localStorage.getItem("aptplayer-eq") || "null");
    if (!saved || !Array.isArray(saved.gains)) return null;
    return saved;
  } catch { return null; }
}

/* ===== Visualização ===== */

function fxDraw() {
  if (!fx.ready || fx.view === "off" || !fx.canvas) {
    fx.raf = 0;
    return;
  }
  fx.raf = requestAnimationFrame(fxDraw);

  const canvas = fx.canvas;
  const g = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  g.clearRect(0, 0, w, h);

  // cores do tema atual
  const css = getComputedStyle(document.documentElement);
  const c1 = css.getPropertyValue("--yellow").trim() || "#fcee0a";
  const c2 = css.getPropertyValue("--cyan").trim() || "#00f0ff";

  if (fx.view === "wave") {
    fx.analyser.getByteTimeDomainData(fx.data);
    g.lineWidth = 2;
    g.strokeStyle = c2;
    g.beginPath();
    const step = w / fx.data.length;
    fx.data.forEach((value, i) => {
      const y = (value / 128) * (h / 2);
      i ? g.lineTo(i * step, y) : g.moveTo(0, y);
    });
    g.stroke();
    return;
  }

  // barras
  fx.analyser.getByteFrequencyData(fx.data);
  const count = 48;
  const barW = w / count;
  const grad = g.createLinearGradient(0, h, 0, 0);
  grad.addColorStop(0, c2);
  grad.addColorStop(1, c1);
  g.fillStyle = grad;

  for (let i = 0; i < count; i++) {
    // escala logarítmica: agudos ocupam menos espaço no espectro
    const index = Math.floor((i / count) ** 1.6 * fx.data.length);
    const value = fx.data[index] || 0;
    const barH = (value / 255) * h;
    g.fillRect(i * barW + 1, h - barH, barW - 2, barH);
  }
}

function fxStartDraw() {
  if (!fx.raf && fx.view !== "off") fxDraw();
}

function fxSetView(view) {
  fx.view = view;
  try { localStorage.setItem("aptplayer-viz", view); } catch {}
  const wrap = $("viz-wrap");
  if (wrap) wrap.classList.toggle("hidden", view === "off");
  if (view === "off") {
    cancelAnimationFrame(fx.raf);
    fx.raf = 0;
  } else {
    fxStartDraw();
  }
}

/** Nível de áudio 0..1 — o mascote usa para dançar no ritmo real. */
function fxLevel() {
  if (!fx.ready || !fx.data) return 0;
  fx.analyser.getByteFrequencyData(fx.data);
  let sum = 0;
  for (let i = 0; i < 24; i++) sum += fx.data[i];
  return sum / (24 * 255);
}

/* ===== Ligações ===== */

function initAudioFx() {
  fx.canvas = $("viz-canvas");
  if (fx.canvas) {
    const resize = () => {
      fx.canvas.width = fx.canvas.clientWidth || 300;
      fx.canvas.height = fx.canvas.clientHeight || 46;
    };
    resize();
    window.addEventListener("resize", resize);
  }

  try {
    fx.view = localStorage.getItem("aptplayer-viz") || "bars";
  } catch { fx.view = "bars"; }

  // a cadeia só pode ser montada depois que o usuário interage
  audio.addEventListener("play", () => {
    if (fxSetup()) {
      fxResume();
      const saved = loadEq();
      if (saved) saved.gains.forEach((db, i) => {
        if (fx.bands[i]) fx.bands[i].gain.value = db;
      });
      fxSetView(fx.view);
    }
  }, { once: false });

  audio.addEventListener("pause", () => {
    cancelAnimationFrame(fx.raf);
    fx.raf = 0;
  });
}
