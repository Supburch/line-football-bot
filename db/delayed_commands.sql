-- Create this once in the Supabase SQL editor.
--
-- Backs the delayed-reply feature ("ได้รม") so it survives Render free-tier
-- sleeps/restarts: the command is persisted here when the wake word arrives,
-- then delivered by the external /cron/delayed hook (and/or the in-process
-- scheduler). The status claim prevents double delivery.
create table if not exists public.delayed_commands (
    id         text primary key,
    target_id  text not null,
    command    text not null default '',
    due_at     timestamptz not null,
    status     text not null default 'pending',
    created_at timestamptz not null default now()
);

create index if not exists delayed_commands_due_idx
    on public.delayed_commands (status, due_at);
