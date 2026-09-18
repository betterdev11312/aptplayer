/* Idiomas da interface.
 *
 * Oito idiomas traduzidos com cuidado. As letras das músicas podem ser
 * traduzidas para 89 idiomas (isso é feito no backend, sob demanda).
 *
 * Como usar no HTML: <span data-i18n="nav.home">Início</span>
 * O texto que está no HTML é o padrão (português) e serve de fallback.
 */

const I18N = {
  pt: {
    _name: "Português",
    "nav.home": "Início", "nav.search": "Buscar", "nav.library": "Biblioteca",
    "nav.favorites": "Favoritas", "nav.history": "Histórico",
    "nav.stats": "Retrospectiva", "nav.chat": "Chat IA",
    "nav.ai": "Ferramentas IA", "nav.settings": "Ajustes",
    "player.idle": "Sistema em espera", "player.noTrack": "// nenhuma faixa carregada",
    "queue.title": "Fila", "queue.empty": "fila vazia",
    "playlists.title": "Playlists",
    "search.hint": "artista, música ou link do YouTube",
    "search.sub": "Filtro de música ativo — vlogs e gameplays são descartados",
    "home.question": "O que você quer ouvir hoje?",
    "home.refresh": "Atualizar",
    "lyrics.title": "Letra", "lyrics.none": "nada tocando",
    "lyrics.translate": "Traduzir", "lyrics.original": "Original",
    "settings.themes": "Temas", "settings.audio": "Áudio",
    "settings.language": "Idioma", "settings.account": "Conta",
    "settings.about": "Sobre", "settings.playback": "Reprodução",
    "btn.playAll": "Tocar tudo", "btn.shuffle": "Aleatório",
    "btn.rename": "Renomear", "btn.delete": "Excluir",
    "btn.share": "Compartilhar", "btn.cancel": "Cancelar",
    "btn.import": "Importar", "btn.save": "Salvar",
  },

  en: {
    _name: "English",
    "nav.home": "Home", "nav.search": "Search", "nav.library": "Library",
    "nav.favorites": "Favorites", "nav.history": "History",
    "nav.stats": "Wrapped", "nav.chat": "AI Chat",
    "nav.ai": "AI Tools", "nav.settings": "Settings",
    "player.idle": "System idle", "player.noTrack": "// no track loaded",
    "queue.title": "Queue", "queue.empty": "queue empty",
    "playlists.title": "Playlists",
    "search.hint": "artist, song or YouTube link",
    "search.sub": "Music filter on — vlogs and gameplays are discarded",
    "home.question": "What do you want to hear today?",
    "home.refresh": "Refresh",
    "lyrics.title": "Lyrics", "lyrics.none": "nothing playing",
    "lyrics.translate": "Translate", "lyrics.original": "Original",
    "settings.themes": "Themes", "settings.audio": "Audio",
    "settings.language": "Language", "settings.account": "Account",
    "settings.about": "About", "settings.playback": "Playback",
    "btn.playAll": "Play all", "btn.shuffle": "Shuffle",
    "btn.rename": "Rename", "btn.delete": "Delete",
    "btn.share": "Share", "btn.cancel": "Cancel",
    "btn.import": "Import", "btn.save": "Save",
  },

  es: {
    _name: "Español",
    "nav.home": "Inicio", "nav.search": "Buscar", "nav.library": "Biblioteca",
    "nav.favorites": "Favoritas", "nav.history": "Historial",
    "nav.stats": "Resumen", "nav.chat": "Chat IA",
    "nav.ai": "Herramientas IA", "nav.settings": "Ajustes",
    "player.idle": "Sistema en espera", "player.noTrack": "// ninguna pista cargada",
    "queue.title": "Cola", "queue.empty": "cola vacía",
    "playlists.title": "Listas",
    "search.hint": "artista, canción o enlace de YouTube",
    "search.sub": "Filtro de música activo — se descartan vlogs y gameplays",
    "home.question": "¿Qué quieres escuchar hoy?",
    "home.refresh": "Actualizar",
    "lyrics.title": "Letra", "lyrics.none": "nada sonando",
    "lyrics.translate": "Traducir", "lyrics.original": "Original",
    "settings.themes": "Temas", "settings.audio": "Audio",
    "settings.language": "Idioma", "settings.account": "Cuenta",
    "settings.about": "Acerca de", "settings.playback": "Reproducción",
    "btn.playAll": "Reproducir todo", "btn.shuffle": "Aleatorio",
    "btn.rename": "Renombrar", "btn.delete": "Eliminar",
    "btn.share": "Compartir", "btn.cancel": "Cancelar",
    "btn.import": "Importar", "btn.save": "Guardar",
  },

  fr: {
    _name: "Français",
    "nav.home": "Accueil", "nav.search": "Rechercher", "nav.library": "Bibliothèque",
    "nav.favorites": "Favoris", "nav.history": "Historique",
    "nav.stats": "Rétrospective", "nav.chat": "Chat IA",
    "nav.ai": "Outils IA", "nav.settings": "Réglages",
    "player.idle": "Système en veille", "player.noTrack": "// aucune piste chargée",
    "queue.title": "File", "queue.empty": "file vide",
    "playlists.title": "Playlists",
    "search.hint": "artiste, morceau ou lien YouTube",
    "search.sub": "Filtre musical actif — vlogs et gameplays écartés",
    "home.question": "Qu'est-ce que vous voulez écouter ?",
    "home.refresh": "Actualiser",
    "lyrics.title": "Paroles", "lyrics.none": "rien en lecture",
    "lyrics.translate": "Traduire", "lyrics.original": "Original",
    "settings.themes": "Thèmes", "settings.audio": "Audio",
    "settings.language": "Langue", "settings.account": "Compte",
    "settings.about": "À propos", "settings.playback": "Lecture",
    "btn.playAll": "Tout lire", "btn.shuffle": "Aléatoire",
    "btn.rename": "Renommer", "btn.delete": "Supprimer",
    "btn.share": "Partager", "btn.cancel": "Annuler",
    "btn.import": "Importer", "btn.save": "Enregistrer",
  },

  de: {
    _name: "Deutsch",
    "nav.home": "Start", "nav.search": "Suche", "nav.library": "Bibliothek",
    "nav.favorites": "Favoriten", "nav.history": "Verlauf",
    "nav.stats": "Rückblick", "nav.chat": "KI-Chat",
    "nav.ai": "KI-Werkzeuge", "nav.settings": "Einstellungen",
    "player.idle": "System bereit", "player.noTrack": "// kein Titel geladen",
    "queue.title": "Warteschlange", "queue.empty": "Warteschlange leer",
    "playlists.title": "Playlists",
    "search.hint": "Künstler, Titel oder YouTube-Link",
    "search.sub": "Musikfilter aktiv — Vlogs und Gameplays werden verworfen",
    "home.question": "Was möchtest du heute hören?",
    "home.refresh": "Aktualisieren",
    "lyrics.title": "Songtext", "lyrics.none": "nichts läuft",
    "lyrics.translate": "Übersetzen", "lyrics.original": "Original",
    "settings.themes": "Themes", "settings.audio": "Audio",
    "settings.language": "Sprache", "settings.account": "Konto",
    "settings.about": "Über", "settings.playback": "Wiedergabe",
    "btn.playAll": "Alle abspielen", "btn.shuffle": "Zufall",
    "btn.rename": "Umbenennen", "btn.delete": "Löschen",
    "btn.share": "Teilen", "btn.cancel": "Abbrechen",
    "btn.import": "Importieren", "btn.save": "Speichern",
  },

  it: {
    _name: "Italiano",
    "nav.home": "Home", "nav.search": "Cerca", "nav.library": "Libreria",
    "nav.favorites": "Preferiti", "nav.history": "Cronologia",
    "nav.stats": "Riepilogo", "nav.chat": "Chat IA",
    "nav.ai": "Strumenti IA", "nav.settings": "Impostazioni",
    "player.idle": "Sistema in attesa", "player.noTrack": "// nessun brano caricato",
    "queue.title": "Coda", "queue.empty": "coda vuota",
    "playlists.title": "Playlist",
    "search.hint": "artista, brano o link YouTube",
    "search.sub": "Filtro musicale attivo — vlog e gameplay esclusi",
    "home.question": "Cosa vuoi ascoltare oggi?",
    "home.refresh": "Aggiorna",
    "lyrics.title": "Testo", "lyrics.none": "niente in riproduzione",
    "lyrics.translate": "Traduci", "lyrics.original": "Originale",
    "settings.themes": "Temi", "settings.audio": "Audio",
    "settings.language": "Lingua", "settings.account": "Account",
    "settings.about": "Informazioni", "settings.playback": "Riproduzione",
    "btn.playAll": "Riproduci tutto", "btn.shuffle": "Casuale",
    "btn.rename": "Rinomina", "btn.delete": "Elimina",
    "btn.share": "Condividi", "btn.cancel": "Annulla",
    "btn.import": "Importa", "btn.save": "Salva",
  },

  ja: {
    _name: "日本語",
    "nav.home": "ホーム", "nav.search": "検索", "nav.library": "ライブラリ",
    "nav.favorites": "お気に入り", "nav.history": "履歴",
    "nav.stats": "まとめ", "nav.chat": "AIチャット",
    "nav.ai": "AIツール", "nav.settings": "設定",
    "player.idle": "待機中", "player.noTrack": "// 曲が読み込まれていません",
    "queue.title": "再生キュー", "queue.empty": "キューは空です",
    "playlists.title": "プレイリスト",
    "search.hint": "アーティスト、曲名、YouTubeリンク",
    "search.sub": "音楽フィルター有効 — 動画や実況は除外されます",
    "home.question": "今日は何を聴きますか？",
    "home.refresh": "更新",
    "lyrics.title": "歌詞", "lyrics.none": "再生していません",
    "lyrics.translate": "翻訳", "lyrics.original": "原文",
    "settings.themes": "テーマ", "settings.audio": "オーディオ",
    "settings.language": "言語", "settings.account": "アカウント",
    "settings.about": "情報", "settings.playback": "再生",
    "btn.playAll": "すべて再生", "btn.shuffle": "シャッフル",
    "btn.rename": "名前を変更", "btn.delete": "削除",
    "btn.share": "共有", "btn.cancel": "キャンセル",
    "btn.import": "インポート", "btn.save": "保存",
  },

  ru: {
    _name: "Русский",
    "nav.home": "Главная", "nav.search": "Поиск", "nav.library": "Библиотека",
    "nav.favorites": "Избранное", "nav.history": "История",
    "nav.stats": "Итоги", "nav.chat": "ИИ-чат",
    "nav.ai": "Инструменты ИИ", "nav.settings": "Настройки",
    "player.idle": "Система ожидает", "player.noTrack": "// трек не загружен",
    "queue.title": "Очередь", "queue.empty": "очередь пуста",
    "playlists.title": "Плейлисты",
    "search.hint": "исполнитель, песня или ссылка YouTube",
    "search.sub": "Музыкальный фильтр включён — влоги и геймплеи отсеиваются",
    "home.question": "Что послушаем сегодня?",
    "home.refresh": "Обновить",
    "lyrics.title": "Текст", "lyrics.none": "ничего не играет",
    "lyrics.translate": "Перевести", "lyrics.original": "Оригинал",
    "settings.themes": "Темы", "settings.audio": "Звук",
    "settings.language": "Язык", "settings.account": "Аккаунт",
    "settings.about": "О программе", "settings.playback": "Воспроизведение",
    "btn.playAll": "Играть всё", "btn.shuffle": "Вперемешку",
    "btn.rename": "Переименовать", "btn.delete": "Удалить",
    "btn.share": "Поделиться", "btn.cancel": "Отмена",
    "btn.import": "Импорт", "btn.save": "Сохранить",
  },
};

let currentLang = "pt";

function t(key) {
  return I18N[currentLang]?.[key] ?? I18N.pt[key] ?? key;
}

function applyLanguage(code) {
  if (!I18N[code]) code = "pt";
  currentLang = code;
  try { localStorage.setItem("aptplayer-lang", code); } catch {}

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const value = t(el.dataset.i18n);
    // preserva ícones SVG: só troca o nó de texto
    const textNode = [...el.childNodes].find((n) => n.nodeType === 3 && n.textContent.trim());
    if (textNode) textNode.textContent = " " + value + " ";
    else el.textContent = value;
  });

  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPh);
  });

  document.documentElement.lang = code;
}

function initLanguage() {
  let saved = "pt";
  try { saved = localStorage.getItem("aptplayer-lang") || "pt"; } catch {}
  applyLanguage(saved);
}

function uiLanguages() {
  return Object.entries(I18N).map(([code, dict]) => ({
    code, name: dict._name,
  }));
}
