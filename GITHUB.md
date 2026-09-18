# Publicar no GitHub

O repositório local já está pronto: `git init` feito, `.gitignore` ajustado e
o primeiro commit criado com os 49 arquivos do projeto (1,9 MB — os `.exe`
ficaram de fora de propósito).

Falta só criar o repositório no site e enviar.

---

## 1. Criar o repositório (1 minuto)

1. Entre em **https://github.com/new** (faça login ou crie a conta — é grátis)
2. Preencha:
   - **Repository name**: `aptplayer`
   - **Description**: `Player de música com IA local, sem conta e sem API key`
   - **Public** ou **Private** — tanto faz para o projeto funcionar
3. **NÃO marque** nenhuma das caixas de *Initialize this repository*
   (README, .gitignore, license). Seu projeto já tem tudo, e marcar cria
   conflito no primeiro push.
4. Clique em **Create repository**

## 2. Enviar o código

O GitHub mostra uma tela com comandos. Ignore e use estes, no terminal dentro
da pasta do projeto (troque `SEU-USUARIO`):

```bash
git remote add origin https://github.com/SEU-USUARIO/aptplayer.git
git push -u origin main
```

Na primeira vez o Git vai pedir login. Vai abrir uma janela do navegador —
autorize por ali (é o jeito mais simples; não precisa criar token manualmente).

Pronto. Atualize a página do GitHub e o código estará lá.

## 3. Daqui pra frente

Sempre que mudar algo e quiser salvar:

```bash
git add -A
git commit -m "o que mudou"
git push
```

O `commit` salva no seu PC; o `push` envia para o GitHub.

Para ver o histórico: `git log --oneline`
Para desfazer mudanças não commitadas num arquivo: `git checkout -- arquivo`

---

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
