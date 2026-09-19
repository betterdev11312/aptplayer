# Como lançar uma versão

Você já compilou e os arquivos estão em `site/`. Falta publicá-los no GitHub
para que a atualização automática funcione.

---

## O que é o `tools_release.py`

É um comando que você roda **no seu computador**. Ele:

1. Cria o Release no GitHub (a "caixa" onde ficam os arquivos para download)
2. Sobe os quatro executáveis pela API — sem passar pelo navegador
3. Repete sozinho se a conexão cair no meio

Sem isso, o app do seu amigo tenta baixar de um endereço que não existe e dá
**404 Not Found** — foi exatamente o erro que ele viu.

> Ele não vai dentro do aplicativo. É ferramenta sua, de desenvolvimento.

---

## Rodando pela primeira vez

No terminal, dentro da pasta do projeto:

```bash
python tools_release.py
```

Ele vai pedir um token do GitHub. Para pegar:

1. Abra **https://github.com/settings/tokens/new**
2. **Note**: `aptplayer-release`
3. **Expiration**: 90 days (ou *No expiration*, se preferir não repetir)
4. Marque a caixa **`repo`** (a primeira da lista, com várias sub-opções)
5. Role até o fim e clique em **Generate token**
6. Copie o token (começa com `ghp_`) — **ele só aparece uma vez**
7. Cole no terminal quando o script pedir

O token fica salvo em `.github-token`, que já está no `.gitignore` — não vai
para o repositório.

Depois disso você verá:

```
Publicando v1.7.1...
  release criado
  AptPlayer-Setup.exe (36.5 MB) tentativa 1... OK
  AptPlayer-Setup.zip (36.3 MB) tentativa 1... OK
  AptPlayer.exe (21.4 MB) tentativa 1... OK
  AptPlayer.zip (21.2 MB) tentativa 1... OK

Pronto: https://github.com/betterdev11312/aptplayer/releases/tag/v1.7.1
```

## Nas próximas vezes

Só o comando — o token já está salvo:

```bash
python tools_release.py
```

Se algum arquivo falhar, rode de novo: ele pula os que já subiram.

---

## O ciclo completo de uma versão nova

```bash
# 1. mude a versão em core/updater.py, installer.py e version_info.txt
#    (e em docs/version.json, para o app saber que há atualização)

# 2. compile
python -m PyInstaller AptPlayer.spec --noconfirm --clean
python -m PyInstaller installer.spec --noconfirm --clean
python tools_package.py

# 3. publique o site e o código
git add -A
git commit -m "v1.8: o que mudou"
git push

# 4. publique os executáveis
python tools_release.py
```

Depois do passo 4, quem estiver numa versão antiga vê o aviso de atualização
e o app se atualiza sozinho.

---

## Por que não pelo site do GitHub

Você pode criar o Release pelo site e arrastar os arquivos, mas o
`AptPlayer-Setup.exe` tem **36 MB** e o navegador costuma cortar a conexão no
meio do upload — foi o que aconteceu quando você tentou.

Pela API é mais estável, e o script tenta de novo automaticamente.
