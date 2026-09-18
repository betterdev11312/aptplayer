# GitHub

O projeto está publicado em **https://github.com/betterdev11312/aptplayer**

O `remote` já está configurado neste repositório local, então daqui pra frente
basta commitar e dar push.

---

## Dia a dia

Sempre que mudar algo e quiser salvar no GitHub:

```bash
git add -A
git commit -m "o que mudou"
git push
```

O `commit` salva no seu PC; o `push` envia para o GitHub.

Para ver o histórico: `git log --oneline`
Para desfazer mudanças não commitadas num arquivo: `git checkout -- arquivo`

---

> **Nota sobre a tela de comandos**: ela só aparece em repositório vazio. Como
> o repo foi criado com um README, o GitHub já mostrou a visualização normal.
> Os comandos acima funcionam do mesmo jeito.

## Por que os .exe ficaram de fora

O GitHub avisa em arquivos acima de 50 MB e recusa acima de 100 MB. Mais
importante: binários incham o repositório para sempre — cada versão nova
guardaria mais 25 MB, e isso nunca é removido do histórico.

Os executáveis ficam no site publicado. Quem baixar o código recompila com:

```bash
pip install -r requirements.txt
python -m PyInstaller AptPlayer.spec --noconfirm --clean
```

### Se quiser oferecer download pelo GitHub também

Use **Releases** (feito para binários, não conta no tamanho do repositório):

1. Na página do repo → **Releases** → **Create a new release**
2. **Tag**: `v1.2.0` · **Title**: `AptPlayer 1.2.0`
3. Arraste o `dist/AptPlayer-Setup.exe` para a área de anexos
4. **Publish release**

---

## Publicar o site direto do GitHub (opcional)

Hoje você publica arrastando a pasta. Dá para automatizar: conecte o
repositório ao Cloudflare Pages ou Netlify, aponte a pasta `site/` e cada
`git push` republica sozinho.

O porém: os `.exe` não estão no repositório, então o download quebraria. Para
isso funcionar, o site precisaria apontar para os arquivos de uma **Release**
em vez dos locais.

Enquanto o projeto for só seu, arrastar a pasta continua sendo mais simples.

---

## Sobre segredos

O `.gitignore` já protege: `data/` (sua biblioteca e sessão), os `.exe` e
arquivos `.env`.

Uma coisa a lembrar: quando você preencher as chaves em `core/account.py`
seguindo o [SUPABASE.md](SUPABASE.md), **elas serão versionadas** no próximo
commit. A chave `anon` é pública por design — ela vai dentro do app de
qualquer forma, e quem protege os dados é o Row Level Security.

Mas se o repositório for público e você preferir não expô-la, mova as chaves
para um arquivo `.env` (já ignorado) e leia com `os.environ`. Posso fazer essa
mudança quando você configurar.

**Nunca** versione a chave `service_role` nem a senha do banco.
