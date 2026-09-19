# AptPlayer para Android

Versão nativa em Kotlin, que funciona sozinha no celular — sem depender do
PC ligado.

**Estado: o código está pronto, mas nunca foi compilado.** Eu não tenho o
Android SDK aqui para testar, então espere ajustes na primeira build.

---

## O que muda em relação ao desktop

O desktop usa **yt-dlp**, que precisa de Python — e Android não tem Python.
No lugar dele entra o **NewPipeExtractor**: biblioteca Java que faz o mesmo
trabalho (buscar no YouTube e resolver a URL do áudio) e roda nativa.

É a mesma biblioteca que o app NewPipe usa, com mais de 30 mil estrelas no
GitHub e manutenção ativa.

| | Desktop | Android |
|---|---|---|
| Resolver áudio | yt-dlp (Python) | NewPipeExtractor (Java) |
| Tocar | `<audio>` do navegador | ExoPlayer |
| Biblioteca | SQLite | Room (SQLite) |
| Interface | HTML/CSS | Kotlin + XML |

O filtro que descarta vlog e gameplay foi **portado com a mesma lógica** —
duração, canal `- Topic`, palavras suspeitas e título gritado.

### O que NÃO vai ter

- **IA** — o Ollama não roda em celular (são GB de modelo)
- **Play Store** — apps que baixam do YouTube são rejeitados; a instalação é
  por APK
- **iPhone** — nada disso funciona no iOS

---

## O que você precisa instalar

### 1. Android Studio

Baixe em **https://developer.android.com/studio** (grátis, ~1 GB).

Na instalação, aceite os componentes padrão — ele traz o SDK, o Gradle e o
emulador. Reserve ~8 GB de espaço.

### 2. Abrir o projeto

1. Abra o Android Studio
2. **Open** → escolha a pasta `android` dentro do projeto
3. Espere ele baixar as dependências (primeira vez demora, ~5 min)

Se pedir para atualizar o Gradle, aceite.

---

## Compilar o APK

### Pelo Android Studio

**Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**

O arquivo sai em `android/app/build/outputs/apk/debug/app-debug.apk`.

### Pelo terminal

```bash
cd android
./gradlew assembleDebug
```

No Windows:

```bash
cd android
gradlew.bat assembleDebug
```

---

## Instalar no celular

### Com cabo USB

1. No celular: **Configurações → Sobre o telefone** → toque 7 vezes em
   *Número da versão* (ativa as opções de desenvolvedor)
2. **Configurações → Opções do desenvolvedor** → ligue **Depuração USB**
3. Conecte o cabo e aceite a permissão que aparece
4. No PC: `adb install app-debug.apk`

### Sem cabo

Copie o APK para o celular (WhatsApp para você mesmo, Drive, cabo como
armazenamento) e toque nele. O Android vai pedir para permitir instalação de
fontes desconhecidas — é normal.

---

## O que está pronto

- Busca no YouTube com o filtro de música
- Reprodução com ExoPlayer
- Player na base da tela com anterior/play/próxima
- Serviço que mantém o som tocando com a tela apagada
- Tema escuro na paleta do desktop
- Ícone do app

## O que falta

- Biblioteca e playlists locais (a estrutura do Room já está declarada)
- Favoritas e histórico
- Rádio (o `YouTube.related()` já existe, falta a tela)
- Download para ouvir offline
- Sincronizar com a conta do desktop

Faz sentido conferir se o básico funciona antes de construir o resto.

---

## Se der erro na primeira build

| Erro | O que fazer |
|---|---|
| `SDK location not found` | Abra pelo Android Studio uma vez; ele cria o `local.properties` |
| `Could not resolve NewPipeExtractor` | Verifique se o `jitpack.io` está no `settings.gradle.kts` (está) |
| `Unsupported Java version` | Android Studio → Settings → Build → Gradle → use o JDK 17 embutido |
| App abre e fecha | Rode `adb logcat | findstr AptPlayer` para ver o erro real |
| Busca não retorna nada | O YouTube mudou algo; atualize a versão do NewPipeExtractor no `app/build.gradle.kts` |

---

## Estrutura

```
android/
├── settings.gradle.kts        repositórios (inclui jitpack)
├── build.gradle.kts           versões dos plugins
└── app/
    ├── build.gradle.kts       dependências
    ├── proguard-rules.pro     preserva o extractor no release
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/com/aptplayer/app/
        │   ├── AptApp.kt          inicializa o extractor
        │   ├── YouTube.kt         busca e resolve áudio (o coração)
        │   ├── HttpDownloader.kt  cliente HTTP do extractor
        │   ├── PlayerService.kt   som com a tela apagada
        │   └── MainActivity.kt    interface
        └── res/                   layouts, cores, ícones
```

O arquivo mais importante é o `YouTube.kt` — é o equivalente Android do
`core/youtube.py` do desktop.
