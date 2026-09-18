# AptPlayer

Player de música com visual Cyberpunk que busca no YouTube, mantém sua
biblioteca local e conversa com uma IA rodando na sua máquina (Ollama) —
sem API key, sem conta, sem nuvem.

## Como rodar

**Pronto para usar:** `dist/AptPlayer.exe` — clique duas vezes, não precisa
instalar nada.

**Pelo código:**

```bash
pip install -r requirements.txt
python main.py
```

## Instalador

`dist/AptPlayer-Setup.exe` instala em `%LOCALAPPDATA%\Programs\AptPlayer`,
cria atalhos e registra a desinstalação no Painel de Controle. Não precisa de
administrador, e o desinstalador **preserva sua biblioteca**.

Gerar (exige o `dist/AptPlayer.exe` já compilado):

```bash
python -m PyInstaller installer.spec --noconfirm --clean
```

## Gerar o .exe

```bash
pip install pyinstaller
python -m PyInstaller AptPlayer.spec --noconfirm --clean
```

Sai um `dist/AptPlayer.exe` de ~25MB, arquivo único.

### Compartilhando com outra pessoa

Mande só o `AptPlayer.exe`. O que acontece na máquina dela:

| | Vai junto? |
|---|---|
| Player, busca no YouTube, cache, playlists | ✅ Funciona na hora |
| Sua biblioteca, seu cache, suas playlists | ❌ Ficam só na sua máquina — ela começa do zero |
| A IA (Ollama) | ❌ É um programa separado; ela precisa instalar |

Sem o Ollama, o app funciona normal e as abas de IA mostram como ativá-la.

Os dados de cada pessoa ficam em `%LOCALAPPDATA%\AptPlayer\data\` quando
roda pelo `.exe`, e em `data/` na pasta do projeto quando roda pelo `.py`.

## Tela inicial

O app abre numa home de descoberta, não numa busca vazia:

- **22 categorias** — gênero, clima e década. Clique e navegue.
- **Seções do seu histórico** — "Continuar ouvindo", "Suas mais tocadas",
  "Favoritas" e "Porque você ouviu X" (mix montado a partir do que você tocou).
- **Carrosséis horizontais** com capas grandes.

Carrega em ~4s (as seções são buscadas em paralelo) e fica em cache por 6h.
O botão **↻ Atualizar** sorteia categorias novas.

## Download sob demanda

Além do cache automático (3 reproduções), você pode baixar na hora:

- **Por faixa** — o botão ⬇ em qualquer lista ou capa. O ícone vira ✓ quando
  a faixa está offline, e pisca em ciano enquanto baixa.
- **Playlist inteira** — botão **⬇ Baixar tudo** na tela da playlist.

## Importar do Spotify

Em **Ferramentas IA → Importar do Spotify**, cole o link de uma playlist ou
álbum público. O app lê a lista de faixas pelo player embutido do Spotify
(sem API key, sem login) e procura cada uma no YouTube.

Leva ~3 segundos por faixa, e roda em background — dá para continuar usando
o player enquanto importa.

## Conta e backup

Duas formas de não perder suas playlists ao trocar de PC:

**Backup em arquivo** (funciona sem conta) — Ajustes → Backup: exporta um
`.json` com playlists, favoritas e contagens. Guarde onde quiser e importe
no PC novo.

**Conta na nuvem** (opcional) — login por email, com a biblioteca salva num
Supabase seu. Vem desligado; para ligar, siga [SUPABASE.md](SUPABASE.md).
É gratuito e leva uns 5 minutos.

Os áudios em cache não vão no backup (são MBs demais) — são rebaixados
conforme você ouve.

## Busca só de música

O player usa duas camadas para não trazer vlog e gameplay:

1. **YouTube Music** (`music.youtube.com`) só indexa música — os IDs que ele
   devolve são confirmados e ganham prioridade.
2. **Heurística de relevância** pontua cada resultado por duração, canal
   (`- Topic` é sempre música), formato do título e palavras de vlog.

Na prática: buscar `"como eu dei um tapa na minha amiga"` não devolve o vlog,
e `"gameplay minecraft"` devolve zero resultados. Ajuste em
[core/youtube.py](core/youtube.py) (`_NOT_MUSIC`, `music_score`).

## Rádio

Clique no ícone de ondas no player (ou no botão de rádio de qualquer faixa) e
o app monta uma **fila infinita** de músicas parecidas. Quando a fila está
acabando, ele busca mais sozinho — não acaba enquanto você não desligar.

Duas fontes combinadas:

1. **Mix do YouTube** — o algoritmo deles a partir da faixa semente. Rápido e
   certeiro: de *Creep* saem Audioslave, Nirvana, Cranberries, Oasis.
2. **IA local** — analisa gênero e clima e sugere artistas parecidos. Entra
   quando o mix se esgota. Dá pra desligar em **Ajustes** se quiser mais
   velocidade.

Ele nunca repete faixa dentro da mesma sessão de rádio.

## Mascote

O **Byte** é um gato cyberpunk em pixel art que mora no player. Ele anda pela
tela, senta, dorme quando você some e dança enquanto a música toca. Comenta o
que você faz — são mais de 200 falas, e ele nunca repete a última.

Clique nele para abrir o menu: três perguntas prontas e um campo livre. Se a
pergunta casar com algo que ele conhece, responde; se não entender, **sai
correndo**. Dá para desligá-lo em Ajustes.

O sprite é gerado por código: [tools_sprite.py](tools_sprite.py) desenha as 11
poses e salva em `ui/sprites/`. Edite as cores ou as formas e rode de novo.

## Letras

Tecla `L` ou o botão no player. As letras vêm do
[LRCLIB](https://lrclib.net) (público, sem cadastro) e, quando há versão
sincronizada, a linha atual acompanha a música. Clique em qualquer verso para
pular até ele.

## Temas

Doze temas em **Ajustes**, cada um com personalidade própria — muda cor,
brilho, scanlines, cantos e fonte:

| Tema | Cara |
|---|---|
| **Edgerunners** | Amarelo ácido e ciano, scanlines e glitch (padrão) |
| **Synthwave** | Roxo e rosa neon, grid retrô dos anos 80 |
| **Matrix** | Verde fósforo em terminal, tudo monoespaçado |
| **Vaporwave** | Pastel suave, cantos redondos, sem scanline |
| **Blood** | Vermelho sobre preto, agressivo |
| **Clean** | Sóbrio, zero efeito, para quem quer foco |
| **Arasaka** | Corporativo e frio: vermelho sobre preto absoluto |
| **Acid** | Verde-limão tóxico, radioativo |
| **Midnight** | Azul profundo e calmo, sem barulho visual |
| **Amber** | Monitor âmbar dos anos 80, scanlines pesadas |
| **Arcade** | Fliperama em fonte pixelada (Press Start 2P) |
| **Snow** | O único claro, para ambientes iluminados |

Tipografia: **Orbitron** nos títulos, **Chakra Petch** no corpo e
**JetBrains Mono** nos detalhes. Matrix, Amber e Arcade trocam por fontes
próprias.

A escolha fica salva entre sessões.

## IA (Ollama)

Requer o [Ollama](https://ollama.com) com pelo menos um modelo:

```bash
ollama pull llama3.2
```

| Onde | O que faz |
|---|---|
| **Chat IA** | Conversa livre sobre música. A IA conhece sua biblioteca e, quando sugere faixas, elas viram botões clicáveis que tocam na hora |
| Rádio | Sugere músicas parecidas quando o mix do YouTube se esgota |
| Busca inteligente | "algo tipo Pink Floyd mas mais pesado" → acha as músicas |
| Gerar playlist | Descreve um clima e ele monta a playlist da sua biblioteca |
| Organizar | Classifica gênero e clima das faixas automaticamente |

Sem Ollama o player funciona normal — só as abas de IA ficam desativadas.

> A **primeira** mensagem depois de abrir o Ollama demora (carrega ~2GB na RAM)
> e pode engasgar o PC por alguns segundos. Depois fica rápido.

## Playlists

Crie pela lateral (`+`), e em cada playlist você pode:

- **Renomear** a qualquer momento
- **Definir uma capa** — clique na capa grande ou no botão `Capa` e escolha uma
  imagem; ela é copiada para `data/covers/`
- **Tocar tudo** ou **Aleatório**

## Áudio híbrido

Toca por streaming na hora. Depois de **3 reproduções** da mesma faixa, ela é
baixada em background e passa a tocar do disco (badge `offline` no player).
O limite fica em [core/cache.py](core/cache.py) (`CACHE_THRESHOLD`).

## Atalhos

| Tecla | Ação |
|---|---|
| `Espaço` | Tocar / pausar |
| `Ctrl` + `→` | Próxima |
| `Ctrl` + `←` | Anterior |
| `L` | Letra da música |
| `↑` / `↓` | Volume |

As teclas de mídia do teclado (play/pausa e faixa anterior/próxima) também
funcionam.

## Estrutura

```
main.py           janela + servidor local (áudio em cache e capas)
core/
  api.py          ponte Python <-> interface
  youtube.py      busca filtrada por música + resolução de stream
  library.py      SQLite: faixas, playlists, capas, histórico
  cache.py        download automático em background
  ai.py           Ollama: chat, busca, playlists, auto-tag
  radio.py        radio infinito (mix do YouTube + IA)
  discover.py     secoes da tela inicial
  lyrics.py       letras via LRCLIB
  updater.py      verificacao de versao
  paths.py        onde ficam os dados
  spotify.py      importar playlists do Spotify
  account.py      login e sincronizacao (Supabase)
ui/
  index.html      telas
  themes.css      os 6 temas
  style.css       layout e efeitos
  app.js          player, fila, chat, modais
  extras.js       letras, fila arrastavel, teclas de midia
  mascot.js       o gato Byte
  mascot-lines.js as falas dele
  sprites/        pixel art do mascote
icon/
  app.ico         ícone da janela
  app.png         ícone da sidebar
data/
  library.db      seu banco
  cache/          áudios baixados
  covers/         capas das playlists
```

## Site

A pasta [site/](site/) tem a landing page pronta para o Netlify, com o `.exe`
para download e o changelog. Publicar: arraste a pasta em
[netlify.com/drop](https://app.netlify.com/drop). Detalhes em
[site/COMO-PUBLICAR.md](site/COMO-PUBLICAR.md).

Ao lançar uma versão nova, lembre de copiar o executável novo para lá:

```bash
python -m PyInstaller AptPlayer.spec --noconfirm --clean
copy dist\AptPlayer.exe site\AptPlayer.exe
```

## Notas

- **Streams expiram.** As URLs do YouTube valem algumas horas; o app resolve
  de novo sozinho quando precisa.
- **Clientes do YouTube.** O YouTube bloqueia alguns clientes com verificação
  anti-bot, e quais funcionam muda com o tempo. O app tenta vários em ordem
  (`PLAYER_CLIENTS` em [core/youtube.py](core/youtube.py)). Se um dia parar de
  tocar, rode `pip install -U yt-dlp` primeiro — geralmente resolve.
- **Uso pessoal.** Baixar áudio do YouTube vai contra os termos de serviço
  deles. Isto é para sua máquina e seu uso; não distribua.
