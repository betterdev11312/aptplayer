# Como publicar o site

## Publicar agora (2 minutos)

1. Abra **https://app.netlify.com/drop**
2. Arraste a pasta `site` inteira para a área indicada
3. Pronto — o site sobe e você recebe um endereço tipo
   `random-name-123.netlify.app`

Não precisa de conta para o primeiro deploy. Se criar uma (grátis), o site
fica salvo no seu painel e você pode trocar o nome para algo como
`aptplayer.netlify.app`.

## Atualizar depois

Repita o passo 2 com a pasta atualizada — o Netlify substitui a versão
anterior no mesmo endereço.

> Se você criou conta: no painel do site, aba **Deploys**, arraste a pasta na
> área "Drag and drop your site output folder here".

## Quando sair uma versão nova do app

1. Recompile: `python -m PyInstaller AptPlayer.spec --noconfirm --clean`
2. Copie o novo executável para cá:
   `copy dist\AptPlayer.exe site\AptPlayer.exe`
3. Adicione a entrada no changelog do `index.html` (veja abaixo)
4. Arraste a pasta no Netlify de novo

## Adicionar uma versão ao changelog

Em `index.html`, procure `<div class="timeline">` e **cole o novo bloco logo
acima** do que já existe (o mais recente fica em cima). Tire o
`<span class="badge-new">atual</span>` da entrada antiga.

```html
<article class="entry">
  <div class="entry-mark"></div>
  <div class="entry-body">
    <div class="entry-head">
      <span class="version">v1.1</span>
      <span class="date">20 set 2026</span>
      <span class="badge-new">atual</span>
    </div>
    <h3>Título da atualização</h3>
    <ul>
      <li><strong>Novidade</strong> — o que mudou.</li>
      <li>Correção: o que foi consertado.</li>
    </ul>
  </div>
</article>
```

Lembre de atualizar também o `// v1.0 · Windows · 25 MB` no topo da página
(`class="kicker"` dentro do hero).

## Ligar a verificação de atualização

O app já sabe verificar se existe versão nova, mas isso vem **desligado** até
você publicar o site — senão ele consultaria um endereço que não existe.

Depois de publicar e saber seu endereço (por exemplo
`https://meu-player.netlify.app`):

1. Abra `core/updater.py`
2. Preencha a linha `UPDATE_URL`:

```python
UPDATE_URL = "https://meu-player.netlify.app/version.json"
```

3. Recompile o app

A partir daí, o botão **Procurar atualização** em Ajustes compara a versão
local com o `version.json` do site. Para anunciar uma versão nova, basta
editar esse arquivo:

```json
{
  "version": "1.3.0",
  "url": "https://meu-player.netlify.app/AptPlayer-Setup.exe",
  "notes": "O que mudou nesta versão."
}
```

## Estrutura

```
site/
├── index.html        página
├── style.css         visual
├── script.js         copiar comando + animações
├── netlify.toml      força o .exe a baixar em vez de abrir
├── _headers          mesma coisa (redundância segura)
├── robots.txt
├── AptPlayer.exe     o download (25 MB)
└── assets/
    ├── icon.png      logo
    ├── favicon.ico
    └── shot-*.png    screenshots do app
```

## Gerar screenshots novos

Os screenshots em `assets/` foram capturados do app rodando. Para atualizá-los
depois de mudanças visuais, rode o app, deixe na tela desejada e capture a
janela — o importante é manter 1264px de largura e recortar a barra de título
do Windows.

## Limites do Netlify (plano grátis)

- 100 MB por arquivo — o `.exe` tem 25 MB, tranquilo
- 100 GB de banda por mês — dá uns 4.000 downloads
