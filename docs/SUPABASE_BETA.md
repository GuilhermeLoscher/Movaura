# Supabase para beta privado

Este fluxo libera o Movaura Beta com chaves unicas. Cada chave pode ser ativada
uma vez e fica vinculada ao hash local do computador.

## 1. Criar tabela e funcao segura

No SQL Editor do Supabase:

```sql
create table if not exists public.beta_keys (
  key text primary key,
  status text not null default 'available',
  assigned_email text,
  assigned_name text,
  machine_hash text,
  activated_at timestamptz,
  expires_at timestamptz,
  notes text
);

alter table public.beta_keys enable row level security;

create or replace function public.activate_beta_key(
  p_key text,
  p_email text,
  p_name text,
  p_machine_hash text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  item public.beta_keys%rowtype;
begin
  select *
  into item
  from public.beta_keys
  where key = upper(trim(p_key))
  for update;

  if not found then
    return jsonb_build_object('success', false, 'message', 'Chave beta nao encontrada.');
  end if;

  if item.expires_at is not null and item.expires_at < now() then
    return jsonb_build_object('success', false, 'message', 'Esta chave beta expirou.');
  end if;

  if item.status = 'used' then
    if item.machine_hash = p_machine_hash and lower(coalesce(item.assigned_email, '')) = lower(p_email) then
      return jsonb_build_object(
        'success', true,
        'message', 'Ativacao restaurada neste computador.',
        'expires_at', item.expires_at
      );
    end if;
    return jsonb_build_object('success', false, 'message', 'Esta chave beta ja foi usada em outro computador.');
  end if;

  if item.status <> 'available' then
    return jsonb_build_object('success', false, 'message', 'Esta chave beta nao esta disponivel.');
  end if;

  update public.beta_keys
  set status = 'used',
      assigned_email = lower(trim(p_email)),
      assigned_name = nullif(trim(p_name), ''),
      machine_hash = p_machine_hash,
      activated_at = now()
  where key = item.key;

  return jsonb_build_object(
    'success', true,
    'message', 'Movaura Beta ativado com sucesso.',
    'expires_at', item.expires_at
  );
end;
$$;

grant execute on function public.activate_beta_key(text, text, text, text) to anon;
```

Com essa funcao, o aplicativo nao precisa de permissao direta de `select` ou
`update` na tabela.

## 1.1. Alternativa simples para beta pequeno

Se voce ainda nao quiser usar RPC, apague `license_activation_rpc` das
configuracoes e use politicas diretas:

```sql
create policy "beta key lookup"
on public.beta_keys
for select
to anon
using (true);

create policy "beta key activation"
on public.beta_keys
for update
to anon
using (status = 'available')
with check (status = 'used');
```

Essa alternativa e mais simples, mas a RPC acima e mais adequada para um beta
comercial porque evita expor a tabela diretamente ao cliente.

## 2. Gerar chaves

```powershell
python scripts\generate_beta_keys.py --count 100
```

Importe o CSV gerado em:

```text
release/beta/movaura_beta_keys.csv
```

## 3. Configurar a build beta

No arquivo de configuracao da build beta, defina:

```json
{
  "license_required": true,
  "license_supabase_url": "https://SEU-PROJETO.supabase.co",
  "license_supabase_anon_key": "SUA_ANON_KEY",
  "license_table": "beta_keys",
  "license_activation_rpc": "activate_beta_key"
}
```

Tambem e possivel testar sem alterar arquivo usando variaveis de ambiente:

```powershell
$env:MOVAURA_LICENSE_REQUIRED="1"
$env:MOVAURA_SUPABASE_URL="https://SEU-PROJETO.supabase.co"
$env:MOVAURA_SUPABASE_ANON_KEY="SUA_ANON_KEY"
python app.py --control-panel
```

## 4. Comportamento esperado

- Se a build nao exigir licenca, o app abre normalmente.
- Se exigir licenca e nao houver ativacao local, aparece a janela `Ativar Movaura Beta`.
- A primeira ativacao muda a chave para `used` no Supabase.
- A mesma chave pode restaurar a ativacao no mesmo computador.
- Outro computador recebe a mensagem de chave ja usada.

## 5. Arquivo local

A ativacao local fica em:

```text
%LOCALAPPDATA%\Movaura\license.json
```

No codigo-fonte em desenvolvimento, ela fica em:

```text
C:\NovaWall\Movaura\data\license.json
```
