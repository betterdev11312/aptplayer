# Rich Presence no Discord — passo a passo

Isto faz o AptPlayer aparecer no seu perfil do Discord assim:

```
┌──────────────────────────────────────┐
│  🎧  Ouvindo AptPlayer               │
│                                      │
│  ▣   Psychosocial                    │
│      por Slipknot                    │
│      ▬▬▬▬▬▬▬▬▬░░░░░  2:41 restantes │
│                                      │
│      [ Ouvir no YouTube ]            │
└──────────────────────────────────────┘
```

**Custo: zero.** Não precisa de bot, servidor nem aprovação do Discord.

O código já está pronto no app — falta só criar a aplicação e pegar o
**Application ID**, que leva uns 5 minutos.

---

## Como funciona (pra entender o que você está fazendo)

O Discord instalado no seu PC abre um "cano" de comunicação local
(`\\.\pipe\discord-ipc-0`). Qualquer programa da máquina pode escrever nele
dizendo *"estou tocando tal música"*, e o Discord publica isso no seu perfil.

O **Application ID** serve só para o Discord saber qual nome e quais imagens
usar. Ele é público — aparece para quem vê seu perfil.

**Nada sai do seu computador por conta do AptPlayer**: quem publica é o
Discord, que você já usa.

---

## 1. Criar a aplicação (2 minutos)

1. Entre em **https://discord.com/developers/applications**
2. Faça login com sua conta normal do Discord
3. Clique em **New Application** (canto superior direito)
4. Em *Name*, escreva `AptPlayer` — **esse nome aparece no seu perfil**,
   depois de "Ouvindo"
5. Aceite os termos e clique em **Create**

## 2. Pegar o Application ID

Ainda na página da aplicação, em **General Information**:

- Procure **Application ID** (um número longo, tipo `1234567890123456789`)
- Clique em **Copy**

É só isso que o app precisa.

## 3. Subir as imagens

Menu lateral → **Rich Presence** → **Art Assets** → **Add Image(s)**.

Suba três imagens. **O nome que você dá a cada uma importa** — o código
procura exatamente por estes:

| Nome (exato) | O que é | Sugestão |
|---|---|---|
| `logo` | imagem grande, ao lado do texto | `icon/app.png` do projeto |
| `play` | ícone pequeno, quando tocando | qualquer ▶ |
| `pause` | ícone pequeno, quando pausado | qualquer ⏸ |

Requisitos: mínimo 512×512 pixels, formato PNG ou JPG.

> As imagens levam **alguns minutos** para ficarem disponíveis depois do
> upload. Se aparecer um quadrado vazio no perfil, espere e teste de novo.

Se quiser pular esta etapa, o status funciona mesmo assim — só fica sem
imagem.

## 4. Colar no app

Abra `core/discord.py` e preencha a primeira linha:

```python
APP_ID = "1234567890123456789"
```

Recompile:

```bash
python -m PyInstaller AptPlayer.spec --noconfirm --clean
```

## 5. Ativar

No app: **Ajustes → Discord → ligar**.

Toque uma música e olhe seu perfil no Discord. Deve aparecer na hora.

---

## Se não aparecer

| Sintoma | Causa provável |
|---|---|
| Nada aparece | O Discord precisa estar **aberto** (não só na bandeja) |
| Nada aparece | Discord → Configurações → **Atividade de jogos** → ativar *"Exibir atividade atual como status"* |
| "não configurado" no app | Faltou preencher o `APP_ID` (passo 4) |
| Aparece sem imagem | As imagens ainda estão sendo processadas, ou o nome não é exatamente `logo`/`play`/`pause` |
| Some depois de um tempo | O Discord limita a ~5 atualizações a cada 20 segundos; o app já respeita isso |

## Detalhes que podem surpreender

- **O botão "Ouvir no YouTube" não aparece para você mesmo.** É uma
  peculiaridade do Discord: botões de Rich Presence só aparecem para as
  outras pessoas. Peça para alguém olhar seu perfil.
- **O tipo é "Ouvindo"**, não "Jogando" — está configurado com `type: 2`
  no código.
- **A barra de progresso** é calculada pelo Discord a partir do horário de
  início e fim que o app envia. Se você pular no meio da música, ela se
  ajusta sozinha.

---

## Vídeos, se preferir

Busque no YouTube por:

- **"Discord Rich Presence tutorial português"**
- **"Discord Developer Portal Application ID"**

O portal do Discord muda de visual de vez em quando, mas os nomes dos menus
(*New Application*, *Rich Presence → Art Assets*) seguem os mesmos.
