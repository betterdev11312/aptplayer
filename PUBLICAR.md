# Publicar no GitHub (Pages + Releases)

O site fica no **GitHub Pages** (grátis, sem limite prático) e os executáveis
no **Releases** (aceita até 2 GB por arquivo, contra os 25 MB do Cloudflare).

---

## 1. Ligar o GitHub Pages (uma vez só)

1. Abra **https://github.com/betterdev11312/aptplayer/settings/pages**
2. Em *Source*, escolha **Deploy from a branch**
3. Em *Branch*, selecione **main** e a pasta **/docs**
4. **Save**

Em um ou dois minutos o site fica no ar em:

**https://betterdev11312.github.io/aptplayer**

## 2. Publicar os executáveis

1. Abra **https://github.com/betterdev11312/aptplayer/releases/new**
2. Preencha:
   - **Choose a tag**: digite `v1.3.0` e clique em *Create new tag*
   - **Release title**: `AptPlayer 1.3.0`
   - **Describe this release**: cole as novidades (estão no site, seção
     *Registro de atualizações*)
3. Arraste os quatro arquivos da pasta `site/` para a área de anexos:
   - `AptPlayer-Setup.exe`
   - `AptPlayer-Setup.zip`
   - `AptPlayer.exe`
   - `AptPlayer.zip`
4. **Publish release**

Pronto — os botões de download do site já apontam para esses arquivos.

---

## Lançando uma versão nova

```bash
# 1. recompile
python -m PyInstaller AptPlayer.spec --noconfirm --clean
python -m PyInstaller installer.spec --noconfirm --clean
python tools_package.py          # gera os .zip em site/

# 2. atualize o site e envie
git add -A
git commit -m "v1.4: o que mudou"
git push
```

Depois crie um Release novo com a tag `v1.4.0` e anexe os arquivos. Lembre de
atualizar `docs/version.json` para a versão nova — é ele que faz o app avisar
que há atualização.

---

## Por que não o Cloudflare Workers

O Workers limita uploads a **25 MB por arquivo**, e o instalador tem 44 MB.
Daria para quebrar em partes, mas Releases existe exatamente para isso.

Se quiser manter o endereço do Workers, dá para deixá-lo servindo a página e
apontar os downloads para o Release do GitHub — foi o que fizemos aqui.
