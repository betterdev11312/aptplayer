/* Transição entre músicas e sleep timer.
 *
 * O crossfade usa DOIS elementos <audio> que se alternam: enquanto um baixa
 * o volume, o outro sobe. Um elemento só não consegue tocar duas faixas ao
 * mesmo tempo.
 *
 * Importante: nada aqui usa Web Audio API — foi o que tirou o som antes.
 * Mexemos apenas na propriedade .volume dos elementos, que é segura.
 */

const fade = {
  seconds: 0,        // 0 = desligado (corte seco)
  gapless: false,    // emenda sem silêncio, sem sobrepor
  other: null,       // o segundo elemento <audio>
  timer: 0,
  fading: false,
  baseVolume: 0.8,   // volume "cheio", o que o usuário escolheu
};

function fadeInit() {
  // segundo player, espelhando as configurações do principal
  fade.other = new Audio();
  fade.other.preload = "auto";
  fade.other.volume = 0;
  fade.baseVolume = audio.volume;

  try {
    const saved = JSON.parse(localStorage.getItem("aptplayer-fade") || "null");
    if (saved) {
      fade.seconds = Number(saved.seconds) || 0;
      fade.gapless = !!saved.gapless;
    }
  } catch {}

  // vigia o fim da faixa para começar a transição na hora certa
  audio.addEventListener("timeupdate", fadeWatch);
}

/** Cancela uma transicao em andamento e silencia o elemento secundario.
 *  Sem isto, pular faixa no meio do crossfade deixa duas musicas tocando. */
function fadeCancel() {
  clearInterval(fade.timer);
  fade.timer = 0;
  fade.fading = false;

  const other = fade.other;
  if (other) {
    try {
      other.pause();
      other.removeAttribute("src");
      other.load();          // descarrega de vez, nao so pausa
      other.volume = 0;
    } catch {}
  }
  if (audio) audio.volume = fade.baseVolume;
}

/** Para tudo o que estiver tocando, nos dois elementos. */
function stopAll() {
  fadeCancel();
  try { audio.pause(); } catch {}
}

function fadeSave() {
  try {
    localStorage.setItem("aptplayer-fade", JSON.stringify({
      seconds: fade.seconds, gapless: fade.gapless,
    }));
  } catch {}
}

/** O volume do usuário mudou: o fade precisa saber qual é o teto. */
function fadeSetBaseVolume(value) {
  fade.baseVolume = value;
}

function fadeWatch() {
  if (!fade.seconds || fade.fading || !audio.duration) return;
  if (audio.paused) return;          // pausado nao inicia transicao
  if (state.repeat) return;                    // repetindo: não faz sentido

  const remaining = audio.duration - audio.currentTime;
  if (remaining > fade.seconds || remaining <= 0) return;

  const next = state.queue[state.index + 1];
  if (!next) return;                           // última da fila

  startCrossfade(next);
}

async function startCrossfade(track) {
  if (fade.fading) return;
  fade.fading = true;

  // Guarda de qual faixa esta transicao trata: se o usuario trocar de musica
  // durante a busca do stream, a transicao perde a validade.
  const origem = state.queue[state.index]?.video_id;

  const res = await api().resolve_stream(track.video_id);

  if (!res.ok || state.queue[state.index]?.video_id !== origem) {
    fadeCancel();
    return;
  }

  const other = fade.other;
  other.src = res.source === "cache" ? mediaUrl(res.url) : res.url;
  other.volume = 0;
  other.currentTime = 0;

  try {
    await other.play();
  } catch {
    fade.fading = false;
    return;
  }

  const steps = 30;
  const stepMs = (fade.seconds * 1000) / steps;
  let i = 0;
  const from = audio.volume;

  clearInterval(fade.timer);
  fade.timer = setInterval(() => {
    // a faixa mudou no meio da transicao: aborta em vez de sobrepor
    if (!fade.fading || state.queue[state.index]?.video_id !== origem) {
      fadeCancel();
      return;
    }

    i += 1;
    const ratio = i / steps;
    audio.volume = Math.max(0, from * (1 - ratio));
    other.volume = Math.min(1, fade.baseVolume * ratio);

    if (i >= steps) {
      clearInterval(fade.timer);
      swapPlayers(track);
    }
  }, stepMs);
}

/** Troca os papéis: quem estava entrando vira o player principal. */
function swapPlayers(track) {
  const old = audio;
  const next = fade.other;

  old.pause();
  old.removeAttribute("src");
  old.load();                // sem isto o antigo pode voltar a tocar
  old.volume = fade.baseVolume;

  // o elemento novo assume o lugar do antigo no DOM e nas variáveis
  next.id = "audio";
  old.id = "audio-old";
  fade.other = old;
  window.audio = next;

  bindAudioEvents(next);
  next.volume = fade.baseVolume;

  state.index += 1;
  fade.fading = false;

  // atualiza a interface como se a faixa tivesse começado normalmente
  onTrackStarted(track);
}

/* ===== Sleep timer ===== */

const sleep = { until: 0, timer: 0, fadeOut: true };

function sleepStart(minutes) {
  sleepCancel();
  if (!minutes) return;

  sleep.until = Date.now() + minutes * 60000;
  sleep.timer = setInterval(sleepTick, 1000);
  updateSleepUi();
  toast(`o app pausa em ${minutes} min`);
}

function sleepTick() {
  const left = sleep.until - Date.now();
  updateSleepUi();

  if (left <= 0) {
    clearInterval(sleep.timer);
    sleep.timer = 0;
    sleepFadeOut();
    return;
  }
  // último minuto: começa a abaixar o volume aos poucos
  if (sleep.fadeOut && left < 60000) {
    audio.volume = fade.baseVolume * (left / 60000);
  }
}

function sleepFadeOut() {
  audio.pause();
  audio.volume = fade.baseVolume;
  sleep.until = 0;
  updateSleepUi();
  toast("boa noite — o timer pausou a música");
  if (typeof catSay === "function") catSay("pause");
}

function sleepCancel() {
  clearInterval(sleep.timer);
  sleep.timer = 0;
  sleep.until = 0;
  audio.volume = fade.baseVolume;
  updateSleepUi();
}

function updateSleepUi() {
  const badge = $("sleep-badge");
  if (!badge) return;
  if (!sleep.until) {
    badge.classList.add("hidden");
    return;
  }
  const left = Math.max(0, sleep.until - Date.now());
  const m = Math.floor(left / 60000);
  const s = Math.floor((left % 60000) / 1000);
  badge.textContent = `⏱ ${m}:${String(s).padStart(2, "0")}`;
  badge.classList.remove("hidden");
}
