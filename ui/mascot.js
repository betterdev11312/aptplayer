/* Byte — o gato mascote do AptPlayer.
 *
 * Anda pela base da tela, senta, dorme, dança quando toca música e comenta o
 * que você faz. Clicar nele abre um menu: 3 perguntas prontas + campo livre.
 * Se o texto livre não casar com nenhuma intenção conhecida, ele foge.
 */

const Cat = {
  el: null,
  sprite: null,
  bubble: null,
  menu: null,

  x: 120,
  dir: 1,
  state: "idle",      // idle | walk | sit | sleep | dance | run
  frame: 0,
  lastLines: {},      // evita repetir a última fala de cada categoria
  idleSince: Date.now(),
  clickCount: 0,
  clickResetAt: 0,
  enabled: true,
  bubbleTimer: null,
  moveTimer: null,

  // índices dos quadros no sprite sheet (mesma ordem de tools_sprite.py)
  FRAMES: {
    idle: [0, 1], blink: [2], walk: [3, 4],
    sit: [5], sleep: [6], dance: [7, 8], run: [9, 10],
  },
  FRAME_W: 96,   // largura exibida (sprite 128 reduzido via background-size)
};

/* ---------- fala ---------- */

function catPick(category) {
  const pool = CAT_LINES[category];
  if (!pool || !pool.length) return null;
  if (pool.length === 1) return pool[0];

  let line;
  do {
    line = pool[Math.floor(Math.random() * pool.length)];
  } while (line === Cat.lastLines[category] && pool.length > 1);
  Cat.lastLines[category] = line;
  return line;
}

function catSay(categoryOrText, { duration = 4200, raw = false } = {}) {
  if (!Cat.enabled || !Cat.bubble) return;
  const text = raw ? categoryOrText : catPick(categoryOrText);
  if (!text) return;

  Cat.bubble.textContent = text;
  Cat.bubble.classList.add("show");
  clearTimeout(Cat.bubbleTimer);
  Cat.bubbleTimer = setTimeout(() => Cat.bubble.classList.remove("show"), duration);
  Cat.idleSince = Date.now();
}

/* ---------- animação ---------- */

function catSetState(state) {
  if (Cat.state === state) return;
  Cat.state = state;
  Cat.frame = 0;
}

function catTick() {
  if (!Cat.sprite) return;

  const frames = Cat.FRAMES[Cat.state] || Cat.FRAMES.idle;
  Cat.frame = (Cat.frame + 1) % frames.length;

  // piscada ocasional quando parado
  let index = frames[Cat.frame];
  if (Cat.state === "idle" && Math.random() < 0.12) index = Cat.FRAMES.blink[0];

  Cat.sprite.style.backgroundPosition = `-${index * Cat.FRAME_W}px 0`;
  Cat.sprite.style.transform = Cat.dir < 0 ? "scaleX(-1)" : "none";
}

function catMove() {
  if (!Cat.el || !Cat.enabled) return;

  if (Cat.state === "walk" || Cat.state === "run") {
    const speed = Cat.state === "run" ? 14 : 3;
    Cat.x += Cat.dir * speed;

    const max = window.innerWidth - 140;
    if (Cat.x > max) { Cat.x = max; Cat.dir = -1; }
    if (Cat.x < 10) { Cat.x = 10; Cat.dir = 1; }

    Cat.el.style.left = Cat.x + "px";

    // fugindo: some ao chegar na borda
    if (Cat.state === "run" && (Cat.x <= 12 || Cat.x >= max - 2)) {
      catHideTemporarily();
    }
  }
}

/** Decide sozinho o que fazer quando ninguém interage. */
function catBrain() {
  if (!Cat.enabled || Cat.state === "run") return;

  const idleFor = Date.now() - Cat.idleSince;
  const playing = typeof audio !== "undefined" && !audio.paused && audio.src;

  // dança enquanto toca música
  if (playing && Cat.state !== "dance" && Math.random() < 0.35) {
    catSetState("dance");
    return;
  }
  if (!playing && Cat.state === "dance") {
    catSetState("idle");
    return;
  }

  // dorme depois de muito tempo parado
  if (!playing && idleFor > 90000) {
    catSetState("sleep");
    return;
  }

  if (Cat.state === "sleep") return;

  // alterna entre andar, sentar e ficar parado
  const roll = Math.random();
  if (roll < 0.28) {
    Cat.dir = Math.random() < 0.5 ? 1 : -1;
    catSetState("walk");
  } else if (roll < 0.45) {
    catSetState("sit");
  } else if (roll < 0.62) {
    catSetState("idle");
  }

  // comentário espontâneo
  if (idleFor > 40000 && Math.random() < 0.3) {
    catSay(playing ? "idleWhilePlaying" : "idle");
  }
}

function catHideTemporarily() {
  Cat.el.classList.add("gone");
  setTimeout(() => {
    // volta do outro lado, como se tivesse dado a volta
    Cat.x = Math.random() < 0.5 ? 20 : window.innerWidth - 160;
    Cat.dir = Cat.x < 100 ? 1 : -1;
    Cat.el.style.left = Cat.x + "px";
    catSetState("idle");
    Cat.el.classList.remove("gone");
    Cat.idleSince = Date.now();
  }, 5000);
}

/* ---------- interação ---------- */

function catNormalize(text) {
  return (text || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")   // tira acentos
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Procura uma intenção conhecida no texto livre. Null = não entendeu. */
function catUnderstand(text) {
  const clean = catNormalize(text);
  if (!clean) return null;

  let best = null;
  let bestScore = 0;

  CAT_INTENTS.forEach((intent) => {
    intent.keys.forEach((key) => {
      const k = catNormalize(key);
      if (!k) return;
      // palavra inteira vale mais que trecho solto
      const whole = new RegExp(`(^| )${k}( |$)`).test(clean);
      const partial = clean.includes(k);
      const weight = intent.weight ?? 1;
      const score = (whole ? k.length * 2 : partial ? k.length : 0) * weight;
      if (score > bestScore) {
        bestScore = score;
        best = intent;
      }
    });
  });

  // trecho curto demais casando por acaso não conta
  if (!best || bestScore < 4) return null;
  return best.a[Math.floor(Math.random() * best.a.length)];
}

function catRunAway() {
  catSay("runaway", { duration: 2600 });
  catCloseMenu();
  catSetState("run");
  Cat.dir = Math.random() < 0.5 ? 1 : -1;
}

function catOpenMenu() {
  if (Cat.menu.classList.contains("open")) return catCloseMenu();

  const questions = CAT_QUESTIONS.map((item, i) =>
    `<button class="cat-q" data-q="${i}">${item.q}</button>`
  ).join("");

  Cat.menu.innerHTML =
    `<div class="cat-menu-title">Byte</div>` +
    questions +
    `<div class="cat-ask">` +
      `<input id="cat-input" type="text" placeholder="ou pergunte outra coisa..." autocomplete="off">` +
      `<button id="cat-send">→</button>` +
    `</div>`;

  Cat.menu.classList.add("open");
  document.body.classList.add("cat-menu-open");
  positionMenu();

  Cat.menu.querySelectorAll(".cat-q").forEach((btn) =>
    btn.addEventListener("click", () => {
      const item = CAT_QUESTIONS[Number(btn.dataset.q)];
      catSay(item.a[Math.floor(Math.random() * item.a.length)], { raw: true, duration: 5200 });
      catCloseMenu();
    })
  );

  const input = Cat.menu.querySelector("#cat-input");
  const send = () => {
    const text = input.value.trim();
    if (!text) return;
    const answer = catUnderstand(text);
    if (answer) {
      catSay(answer, { raw: true, duration: 5200 });
      catCloseMenu();
    } else {
      catRunAway();
    }
  };
  Cat.menu.querySelector("#cat-send").addEventListener("click", send);
  input.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") send();
    if (ev.key === "Escape") catCloseMenu();
  });
  input.focus();
}

function catCloseMenu() {
  Cat.menu?.classList.remove("open");
  document.body.classList.remove("cat-menu-open");
}

function positionMenu() {
  const left = Math.min(Cat.x, window.innerWidth - 280);
  Cat.menu.style.left = Math.max(10, left) + "px";
}

function catOnClick(ev) {
  ev.stopPropagation();
  if (Cat.state === "run") return;

  const now = Date.now();
  if (now > Cat.clickResetAt) Cat.clickCount = 0;
  Cat.clickCount += 1;
  Cat.clickResetAt = now + 4000;

  // clicar muito seguido irrita
  if (Cat.clickCount >= 5) {
    catSay("annoyed");
    if (Cat.clickCount >= 7) catRunAway();
    return;
  }

  if (Cat.menu.classList.contains("open")) return catCloseMenu();

  catSetState("sit");
  catSay("pet", { duration: 2400 });
  setTimeout(catOpenMenu, 500);
}

/* ---------- eventos do app ---------- */

const catOn = {
  play(track, isRepeat) {
    catSetState("dance");
    catSay(isRepeat ? "playAgain" : "play");
  },
  pause() { catSay("pause"); catSetState("idle"); },
  skip() { catSay("skip"); },
  favorite(on) { catSay(on ? "favorite" : "unfavorite"); },
  radio(on) { catSay(on ? "radioOn" : "radioOff"); },
  download() { catSay("download"); },
  downloadDone() { catSay("downloadDone"); },
  downloadPlaylist() { catSay("downloadPlaylist"); },
  playlistCreated() { catSay("playlistCreated"); },
  playlistCover() { catSay("playlistCover"); },
  error() { catSay("error"); },
  noResults() { catSay("noResults"); },
  milestone(count) {
    const key = count >= 500 ? "milestone500"
              : count >= 100 ? "milestone100"
              : count >= 50 ? "milestone50"
              : count >= 10 ? "milestone10" : null;
    if (key) catSay(key, { duration: 5200 });
  },
};

/* ---------- ciclo de vida ---------- */

function catInit() {
  const saved = (() => {
    try { return localStorage.getItem("aptplayer-cat"); } catch { return null; }
  })();
  if (saved === "off") { Cat.enabled = false; return; }

  Cat.el = document.createElement("div");
  Cat.el.className = "cat";
  Cat.el.innerHTML =
    `<div class="cat-bubble"></div>` +
    `<div class="cat-sprite"></div>`;
  document.body.appendChild(Cat.el);

  Cat.menu = document.createElement("div");
  Cat.menu.className = "cat-menu";
  document.body.appendChild(Cat.menu);

  Cat.sprite = Cat.el.querySelector(".cat-sprite");
  Cat.bubble = Cat.el.querySelector(".cat-bubble");

  Cat.x = Math.max(20, window.innerWidth * 0.18);
  Cat.el.style.left = Cat.x + "px";

  Cat.el.addEventListener("click", catOnClick);
  document.addEventListener("click", (ev) => {
    if (!Cat.menu.contains(ev.target) && !Cat.el.contains(ev.target)) catCloseMenu();
  });

  setInterval(catTick, 420);     // troca de quadro
  setInterval(catMove, 60);      // deslocamento
  setInterval(catBrain, 5000);   // decisões

  const hour = new Date().getHours();
  const greetKey = hour < 6 || hour >= 22 ? "greetNight"
                 : hour < 12 ? "greetMorning" : "greet";
  setTimeout(() => catSay(greetKey, { duration: 5200 }), 1800);
}

function catToggle(on) {
  Cat.enabled = on;
  try { localStorage.setItem("aptplayer-cat", on ? "on" : "off"); } catch {}
  if (!on) {
    Cat.el?.remove();
    Cat.menu?.remove();
    Cat.el = Cat.menu = Cat.sprite = Cat.bubble = null;
  } else if (!Cat.el) {
    catInit();
  }
}
