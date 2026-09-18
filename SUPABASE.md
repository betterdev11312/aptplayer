# Ligar o login (Supabase) — passo a passo

Isto faz suas playlists sobreviverem a uma troca de PC: você faz login,
envia a biblioteca, e no computador novo faz login e baixa tudo de volta.

**Custo: zero.** O plano gratuito do Supabase dá 500 MB de banco e 50 mil
usuários ativos por mês. Sua biblioteca inteira ocupa alguns KB — cabe
folgado, e não pede cartão de crédito.

> Se preferir não criar conta nenhuma, o **backup em arquivo** (em Ajustes,
> ao lado) resolve o mesmo problema: exporta um `.json`, você guarda no
> pendrive ou no Google Drive e importa no PC novo.

---

## 1. Criar o projeto (3 minutos)

1. Entre em **https://supabase.com** e clique em *Start your project*
2. Faça login com o GitHub (ou email)
3. Clique em **New project** e preencha:
   - **Name**: `aptplayer`
   - **Database Password**: gere uma e **guarde** (você não vai usar no app,
     mas é a senha mestra do banco)
   - **Region**: escolha `South America (São Paulo)` — fica mais rápido
4. Clique em **Create new project** e espere ~2 minutos

## 2. Criar a tabela

No menu lateral, abra **SQL Editor** → **New query**, cole isto e clique em
**Run**:

```sql
-- Uma linha por usuário, guardando a biblioteca inteira em JSON.
create table if not exists libraries (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  data       jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

-- Row Level Security: cada pessoa só enxerga a própria linha.
alter table libraries enable row level security;

create policy "dono le" on libraries
  for select using (auth.uid() = user_id);

create policy "dono escreve" on libraries
  for insert with check (auth.uid() = user_id);

create policy "dono atualiza" on libraries
  for update using (auth.uid() = user_id);
```

Deve aparecer *Success. No rows returned*.

> A parte importante é o **Row Level Security**. Sem ele, qualquer pessoa com
> a chave pública conseguiria ler a biblioteca de todo mundo. Com ele, o banco
> recusa qualquer acesso a linha que não seja sua.

## 3. Pegar as duas chaves

Menu lateral → **Project Settings** (engrenagem) → **API**. Copie:

- **Project URL** — algo como `https://abcdefgh.supabase.co`
- **anon public** (em *Project API keys*) — uma chave longa começando com `eyJ...`

A chave `anon` é **pública por design** — ela vai dentro do app, e qualquer um
que baixar consegue lê-la. Quem protege os dados é o RLS do passo 2.

⚠️ **Nunca** use a chave `service_role`. Ela ignora o RLS.

## 4. Colar no app

Abra `core/account.py` e preencha as duas linhas do topo:

```python
SUPABASE_URL = "https://abcdefgh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Recompile:

```bash
python -m PyInstaller AptPlayer.spec --noconfirm --clean
```

## 5. (Opcional) Desligar a confirmação por email

Por padrão o Supabase manda um email de confirmação antes de liberar a conta.
Para testar mais rápido: **Authentication** → **Providers** → **Email** →
desmarque *Confirm email* → **Save**.

Para uso real, deixe ligado — impede alguém de criar conta com o email de outra
pessoa.

---

## Usando

Em **Ajustes → Conta**:

| Botão | O que faz |
|---|---|
| **Criar conta** | Cadastra com email e senha |
| **Entrar** | Faz login (fica salvo entre sessões) |
| **Enviar** | Manda sua biblioteca para a nuvem (substitui o backup anterior) |
| **Baixar** | Traz a biblioteca da nuvem e **mescla** com a daqui |

### Trocando de PC

1. No PC antigo: **Enviar**
2. No PC novo: instale o AptPlayer, faça **Entrar** e clique em **Baixar**

Voltam as playlists, favoritas, gêneros e contagens de reprodução. Os áudios
em cache **não** vão junto (são MBs demais) — eles são baixados de novo
conforme você ouve.

---

## Vídeos, se preferir acompanhar em vídeo

Busque no YouTube por:

- **"Supabase tutorial português criar projeto"** — cobre os passos 1 a 3
- **"Supabase Row Level Security explicado"** — entender o passo 2
- No canal oficial (em inglês): **"Supabase in 100 seconds"** (Fireship) para
  uma visão geral rápida

O painel do Supabase muda de aparência de tempos em tempos; se o vídeo estiver
diferente da tela, os nomes dos menus (*SQL Editor*, *Project Settings → API*)
continuam os mesmos.

---

## Se der errado

| Mensagem | Causa provável |
|---|---|
| "Conta nao configurada neste build" | Faltou preencher o passo 4 |
| "Invalid login credentials" | Email ou senha errados |
| "Email not confirmed" | Confirme pelo link no email, ou desligue no passo 5 |
| Servidor respondeu 401 | Chave `anon` copiada errada |
| Servidor respondeu 403 ou 42501 | A policy do passo 2 não foi criada |
| "Nenhum backup salvo nesta conta ainda" | Clique em **Enviar** primeiro |
