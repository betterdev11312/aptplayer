# Perfis — SQL do Supabase

Rode uma vez em **SQL Editor → New query → Run**. Cria a tabela de perfis
(nickname, foto e bio) que aparece para os amigos nas salas.

```sql
create table if not exists profiles (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  nickname   text not null default 'alguem',
  avatar     text,          -- data URL da foto, ja reduzida pelo app
  bio        text,
  updated_at timestamptz not null default now()
);

alter table profiles enable row level security;

-- Todo mundo logado ve os perfis (precisa disso para mostrar os amigos).
create policy "ver perfis" on profiles
  for select using (auth.role() = 'authenticated');

-- Cada um edita apenas o proprio.
create policy "criar proprio perfil" on profiles
  for insert with check (auth.uid() = user_id);

create policy "editar proprio perfil" on profiles
  for update using (auth.uid() = user_id);
```

Deve aparecer *Success. No rows returned*.

---

## Como funciona

Em **Ajustes → Perfil** você define:

| Campo | Limite |
|---|---|
| **Nickname** | 24 caracteres — é o nome que aparece no chat |
| **Foto** | qualquer imagem; o app recorta quadrada e reduz para 256px |
| **Bio** | 200 caracteres |

A foto vai junto do perfil, como imagem codificada. Isso evita configurar um
bucket de arquivos no Supabase, e 256px é suficiente para a lista de membros.

O perfil fica na sua conta, então acompanha você ao trocar de PC.
