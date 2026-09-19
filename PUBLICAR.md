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

### Pelo script (recomendado)

O upload pelo site do GitHub falha com frequência em arquivos de 36 MB —
o navegador corta a conexão no meio. Use o script:

```bash
python tools_release.py
```

Ele cria o release, sobe os quatro arquivos pela API e repete sozinho se a
conexão cair. Se algum falhar, rode de novo — ele continua de onde parou.

Na primeira vez pede um token do GitHub:

1. Abra **https://github.com/settings/tokens/new**
2. *Note*: `aptplayer-release`
3. Marque a caixa **repo**
4. **Generate token** e copie (começa com `ghp_`)
5. Cole quando o script pedir — ele guarda em `.github-token`, que já está
   no `.gitignore`

### Pelo site (se preferir)

1. Abra **https://github.com/betterdev11312/aptplayer/releases/new**
2. Preencha:
   - **Choose a tag**: digite `v1.3.0` e clique em *Create new tag*
   - **Release title**: `AptPlayer 1.3.0`
   - **Describe this release**: é o campo grande abaixo do título. Cole o
     conteúdo de [RELEASE-NOTES.md](RELEASE-NOTES.md) — já está pronto.
     (Esse campo é opcional; sem ele o release funciona igual.)
3. Arraste os quatro arquivos da pasta `site/` para a área de anexos:

   | Arquivo | Tamanho | Para quem |
   |---|---|---|
   | `AptPlayer-Setup.exe` | 37 MB | a maioria — é o botão grande do site |
   | `AptPlayer.exe` | 22 MB | quem prefere portátil |
   | `AptPlayer-Setup.zip` | 37 MB | se o navegador bloquear o .exe |
   | `AptPlayer.zip` | 22 MB | portátil, mesma situação |

   Os `.zip` não são menores (o executável já vem compactado por dentro) —
   servem só para contornar o alerta do navegador.
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
