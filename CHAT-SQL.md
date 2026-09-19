# Ligar o chat — SQL do Supabase

Rode isto uma vez em **SQL Editor → New query → Run**, no painel do Supabase.
Cria as tabelas de salas, membros e mensagens, com as regras de acesso.

```sql
-- ============ SALAS ============
create table if not exists rooms (
  id         uuid primary key default gen_random_uuid(),
  code       text unique not null,
  name       text not null,
  owner_id   uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

-- ============ MEMBROS ============
create table if not exists room_members (
  room_id    uuid not null references rooms(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  nickname   text not null default 'alguem',
  now_playing jsonb,
  seen_at    timestamptz not null default now(),
  primary key (room_id, user_id)
);

-- ============ MENSAGENS ============
create table if not exists messages (
  id         bigserial primary key,
  room_id    uuid not null references rooms(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  nickname   text not null default 'alguem',
  body       text,
  track      jsonb,          -- faixa compartilhada, quando houver
  created_at timestamptz not null default now()
);

create index if not exists idx_messages_room on messages(room_id, created_at desc);

-- ============ OUVIR JUNTO ============
-- Uma linha por sala: o que esta tocando e desde quando.
create table if not exists room_playback (
  room_id    uuid primary key references rooms(id) on delete cascade,
  track      jsonb,
  position   double precision not null default 0,
  playing    boolean not null default false,
  updated_by uuid references auth.users(id) on delete set null,
  updated_at timestamptz not null default now()
);

-- ============ SEGURANÇA ============
alter table rooms         enable row level security;
alter table room_members  enable row level security;
alter table messages      enable row level security;
alter table room_playback enable row level security;

-- Quem esta logado pode procurar sala pelo codigo e criar salas.
create policy "ver salas"   on rooms for select using (auth.role() = 'authenticated');
create policy "criar sala"  on rooms for insert with check (auth.uid() = owner_id);
create policy "dono apaga"  on rooms for delete using (auth.uid() = owner_id);

-- Membros: cada um gerencia a propria entrada; todos veem quem esta na sala.
create policy "ver membros" on room_members for select using (auth.role() = 'authenticated');
create policy "entrar"      on room_members for insert with check (auth.uid() = user_id);
create policy "atualizar"   on room_members for update using (auth.uid() = user_id);
create policy "sair"        on room_members for delete using (auth.uid() = user_id);

-- Mensagens: so quem e membro da sala le; cada um escreve em seu nome.
create policy "ler mensagens" on messages for select using (
  exists (select 1 from room_members m
          where m.room_id = messages.room_id and m.user_id = auth.uid())
);
create policy "escrever" on messages for insert with check (
  auth.uid() = user_id
  and exists (select 1 from room_members m
              where m.room_id = messages.room_id and m.user_id = auth.uid())
);

-- Ouvir junto: membros leem e controlam.
create policy "ler playback" on room_playback for select using (
  exists (select 1 from room_members m
          where m.room_id = room_playback.room_id and m.user_id = auth.uid())
);
create policy "mudar playback" on room_playback for insert with check (
  exists (select 1 from room_members m
          where m.room_id = room_playback.room_id and m.user_id = auth.uid())
);
create policy "atualizar playback" on room_playback for update using (
  exists (select 1 from room_members m
          where m.room_id = room_playback.room_id and m.user_id = auth.uid())
);
```

Deve aparecer *Success. No rows returned*.

---

## Limpeza automática (opcional)

Mensagens antigas ocupam espaço à toa. Para apagar as com mais de 30 dias,
rode isto de vez em quando:

```sql
delete from messages where created_at < now() - interval '30 days';
```

## Como funciona

1. Você cria uma sala e recebe um código como `APT-7K3F`
2. Manda o código para quem quiser
3. A pessoa cola em **Chat → Entrar numa sala**
4. Dentro da sala: conversa, vê o que cada um está ouvindo, manda faixas
   e pode ligar o **ouvir junto**

Só quem tem o código entra. Ninguém descobre salas dos outros.

---

## Atualização para o início sincronizado (v1.8)

Rode também este SQL, que adiciona as colunas do início agendado:

```sql
alter table room_playback
  add column if not exists start_at timestamptz,
  add column if not exists start_position double precision not null default 0;
```

Sem isso a sala continua funcionando, só sem o início no mesmo segundo.
