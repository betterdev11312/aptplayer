Player de música com interface cyberpunk que busca no YouTube, mantém a
biblioteca local e usa IA rodando na sua própria máquina.

## Novidades desta versão

- **Equalizer e visualização** — 7 bandas e presets; barras reagindo à música.
  Vem desligado: ative em Ajustes → Áudio.
- **Retrospectiva** — seus artistas e músicas mais ouvidos, tempo total,
  sequência de dias e a que horas você escuta.
- **Teclas de mídia globais** — play, pausa e faixa anterior/próxima funcionam
  com o app minimizado.
- **Importar do Spotify** — cole o link de uma playlist pública e ela é
  recriada buscando cada faixa no YouTube.
- **Conta na nuvem (opcional)** — recupere suas playlists ao trocar de PC.
  Também há backup em arquivo, sem conta.
- **Byte, o mascote** — gato cyberpunk em pixel art com mais de 200 falas.
- **12 temas** — Edgerunners, Synthwave, Matrix, Arcade, Snow e outros.
- **Letras sincronizadas** — a linha acompanha a música (tecla `L`).

O executável ficou 9 MB menor nesta versão.

## Qual arquivo baixar

| Arquivo | Para quê |
|---|---|
| `AptPlayer-Setup.zip` | **Recomendado** — instala, cria atalhos e permite desinstalar pelo Painel de Controle |
| `AptPlayer.zip` | Portátil: um arquivo só, roda de onde estiver |
| `.exe` soltos | Mesma coisa, sem o zip — alguns navegadores reclamam mais |

Windows 10/11, 64-bit.

## O antivírus vai reclamar

É falso positivo. Acontece com programas feitos em Python e sem assinatura
digital (um certificado custa cerca de US$ 200 por ano).

- **Chrome**: clique na seta ao lado do aviso → *Manter*
- **Windows**: ao abrir → *Mais informações* → *Executar assim mesmo*

O código é aberto — dá para ler tudo e compilar você mesmo.

## IA (opcional)

Para ativar o chat e as ferramentas de IA, instale o
[Ollama](https://ollama.com) e rode:

```
ollama pull llama3.2
```

Sem isso o player funciona normalmente; só as abas de IA ficam desativadas.
