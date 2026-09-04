-- LegalMente — almacén canónico de piezas aprobadas. Migración 0001.
--
-- Esquema MÍNIMO del primer cimiento: piezas aprobadas y sus estados.
-- No incluye, deliberadamente: usuarios, PII, documentos de personas, casos
-- personales, pagos ni servicios profesionales (decisión del fundador
-- 2026-09-04, requisitos 7 y 8). Añadir cualquiera de esos exige cerrar antes
-- privacidad, retención, borrado, seguridad y términos.
--
-- REGLA DE ORO DE ESTE ESQUEMA: la base de datos no decide qué está aprobado.
-- El criterio vive en `scripts/validate-claim-packet.py` y en la revisión
-- humana. Aquí solo se REGISTRA lo ya decidido, y se impide que se registre
-- una aprobación incompleta. Por eso todas las restricciones son de negativa:
-- ninguna concede autoridad, todas la niegan si falta algo.
--
-- Vocabulario tomado literalmente del validador (VALID_ESTADO, VALID_ALCANCE,
-- VALID_GATE, VALID_REVISION_ESTADO, VALID_TIPO_FUENTE). No se inventa ningún
-- estado nuevo: un estado que aquí no exista tampoco existe en el sistema.

begin;

create schema if not exists legalmente;

-- ---------------------------------------------------------------------------
-- 1. Piezas
-- ---------------------------------------------------------------------------

create table if not exists legalmente.piezas (
    content_id            text primary key,
    version               integer not null default 1 check (version >= 1),

    -- Estado agregado de la pieza, calculado por el validador. Nunca a mano.
    estado_agregado       text not null
        check (estado_agregado in (
            'REQUIERE_INVESTIGACION', 'APTO_CON_MATICES', 'APTO_PARA_NARRATIVA',
            'PENDIENTE_APROBACION_HUMANA', 'BLOQUEADO')),

    -- El gate de arte NO es "aprobado": es "puede empezar a producirse arte".
    gate_global_arte      text not null default 'CERRADO'
        check (gate_global_arte in ('CERRADO', 'ABIERTO')),

    capa_jurisdiccional   text not null default 'NO_DETERMINADO'
        check (capa_jurisdiccional in (
            'CAPA_A_TRANSVERSAL', 'CAPA_B_VARIABLE', 'CAPA_C_NACIONAL',
            'NO_DETERMINADO', 'NO_APLICA')),

    -- Hash canónico del contenido exacto. Es lo que liga la aprobación al
    -- texto aprobado: si el texto cambia, el hash deja de coincidir y la
    -- aprobación queda invalidada (misma regla que el validador).
    contenido_hash_sha256 text
        check (contenido_hash_sha256 is null
               or contenido_hash_sha256 ~ '^[0-9a-f]{64}$'),

    titulo_de_trabajo     text not null check (length(btrim(titulo_de_trabajo)) > 0),
    materia               text not null check (length(btrim(materia)) > 0),

    creado_en             timestamptz not null default now(),
    actualizado_en        timestamptz not null default now(),

    -- Publicación: un cuarto estado, NO equivalente a aprobación.
    publicacion           text not null default 'NOT_PUBLISHED'
        check (publicacion in ('NOT_PUBLISHED', 'PUBLISHED')),

    unique (content_id, version)
);

comment on table legalmente.piezas is
    'Pieza canónica. estado_agregado, gate_global_arte, aprobación humana y publicación son CUATRO estados no equivalentes: ninguno implica el siguiente.';

-- ---------------------------------------------------------------------------
-- 2. Claims
-- ---------------------------------------------------------------------------

create table if not exists legalmente.claims (
    claim_id              text primary key,
    content_id            text not null
        references legalmente.piezas (content_id) on delete cascade,

    texto_exacto          text not null check (length(btrim(texto_exacto)) > 0),

    tipo                  text not null
        check (tipo in ('regla', 'definicion', 'cita', 'atribucion', 'dato',
                        'procedimiento', 'consecuencia', 'consejo')),
    ubicacion             text not null
        check (ubicacion in ('titulo', 'hook', 'texto_imagen', 'caption', 'lista',
                             'cta', 'prompt_visual', 'descripcion_tema')),
    alcance               text not null
        check (alcance in ('CAPA_A_TRANSVERSAL', 'CAPA_B_VARIABLE',
                           'CAPA_C_NACIONAL', 'NO_DETERMINADO', 'NO_APLICA')),

    -- Jurisdicciones declaradas. Vacío es legítimo (NO_APLICA), pero entonces
    -- el alcance no puede ser nacional: lo comprueba el trigger de abajo.
    jurisdiccion          text[] not null default '{}',

    estado                text not null
        check (estado in ('REQUIERE_INVESTIGACION', 'APTO_CON_MATICES',
                          'APTO_PARA_NARRATIVA', 'PENDIENTE_APROBACION_HUMANA',
                          'BLOQUEADO')),
    gate_arte             text not null default 'CERRADO'
        check (gate_arte in ('CERRADO', 'ABIERTO')),

    -- Revisión humana. El revisor es un identificador de rol o alias, NUNCA
    -- un dato personal (requisito 7: nada de PII en esta fase).
    revision_estado       text not null default 'PENDIENTE'
        check (revision_estado in ('PENDIENTE', 'APROBADO', 'RECHAZADO')),
    revision_revisor      text,
    revision_fecha        timestamptz,
    revision_hash_sha256  text
        check (revision_hash_sha256 is null
               or revision_hash_sha256 ~ '^[0-9a-f]{64}$'),

    creado_en             timestamptz not null default now(),

    -- FAIL-CLOSED 1: una aprobación humana incompleta no se puede registrar.
    -- Sin revisor, sin fecha y sin el hash del contenido aprobado, "APROBADO"
    -- no significa nada verificable.
    constraint aprobacion_completa check (
        revision_estado <> 'APROBADO'
        or (revision_revisor is not null and length(btrim(revision_revisor)) > 0
            and revision_fecha is not null
            and revision_hash_sha256 is not null)
    ),

    -- FAIL-CLOSED 2: el gate de arte exige, a la vez, evidencia suficiente y
    -- aprobación humana ligada por hash. Es la misma conjunción que calcula
    -- el validador; aquí se repite para que la BD no pueda contradecirlo.
    constraint gate_exige_evidencia_y_aprobacion check (
        gate_arte = 'CERRADO'
        or (estado = 'APTO_PARA_NARRATIVA'
            and revision_estado = 'APROBADO'
            and revision_hash_sha256 is not null)
    ),

    -- FAIL-CLOSED 3: un claim nacional sin país declarado es una falsa
    -- universalización esperando a ocurrir.
    constraint nacional_exige_jurisdiccion check (
        alcance <> 'CAPA_C_NACIONAL' or array_length(jurisdiccion, 1) >= 1
    ),

    -- FAIL-CLOSED 4: la Capa A exige el mínimo de jurisdicciones comparadas
    -- que el motor de transversalidad ya declara (3).
    constraint capa_a_exige_tres_jurisdicciones check (
        alcance <> 'CAPA_A_TRANSVERSAL' or array_length(jurisdiccion, 1) >= 3
    )
);

create index if not exists claims_por_pieza on legalmente.claims (content_id);

-- ---------------------------------------------------------------------------
-- 3. Fuentes
-- ---------------------------------------------------------------------------

create table if not exists legalmente.fuentes (
    fuente_id                  text primary key,
    claim_id                   text not null
        references legalmente.claims (claim_id) on delete cascade,

    tipo_fuente                text not null
        check (tipo_fuente in ('NORMA_OFICIAL', 'JURISPRUDENCIA_OFICIAL',
                               'AUTORIDAD_PUBLICA_OFICIAL', 'ACADEMICA_IDENTIFICABLE',
                               'SECUNDARIA_ESPECIALIZADA', 'DRIVE_INTERNO')),
    organismo_autor            text not null check (length(btrim(organismo_autor)) > 0),
    titulo                     text not null check (length(btrim(titulo)) > 0),
    url                        text,
    localizador                text,
    -- Enlace al registro oficial cerrado. Una fuente oficial sin entrada en el
    -- registro no puede sostener el nivel máximo: lo comprueba el trigger.
    registro_oficial_id        text,
    jurisdicciones_cubiertas   text[] not null default '{}',

    -- Los tres booleanos del Nivel 1. Nunca autoafirmados: se copian del
    -- claim packet ya validado, y por defecto son falsos.
    origen_oficial_confirmado  boolean not null default false,
    texto_exacto_consultado    boolean not null default false,
    vigencia_comprobada        boolean not null default false,
    fecha_comprobacion         date,

    creado_en                  timestamptz not null default now(),

    -- FAIL-CLOSED 5: decir "comprobado" sin decir cuándo no es comprobable.
    constraint verificacion_fechada check (
        not (origen_oficial_confirmado or texto_exacto_consultado or vigencia_comprobada)
        or fecha_comprobacion is not null
    ),

    -- FAIL-CLOSED 6: una fuente oficial necesita localizador concreto. "La ley
    -- entera" no sostiene una afirmación sobre un artículo.
    constraint oficial_exige_localizador check (
        tipo_fuente not in ('NORMA_OFICIAL', 'JURISPRUDENCIA_OFICIAL',
                            'AUTORIDAD_PUBLICA_OFICIAL')
        or (localizador is not null and length(btrim(localizador)) > 0)
    )
);

create index if not exists fuentes_por_claim on legalmente.fuentes (claim_id);

-- ---------------------------------------------------------------------------
-- 4. Investigación (trazabilidad del research que sostiene cada claim)
-- ---------------------------------------------------------------------------

create table if not exists legalmente.investigaciones (
    investigacion_id  uuid primary key default gen_random_uuid(),
    claim_id          text not null
        references legalmente.claims (claim_id) on delete cascade,
    hallazgo          text not null check (length(btrim(hallazgo)) > 0),
    metodo            text not null
        check (metodo in ('LECTURA_TEXTO_OFICIAL', 'BUSQUEDA_WEB',
                          'CONSULTA_REGISTRO_OFICIAL', 'REVISION_DOCTRINA',
                          'APORTADO_POR_HUMANO')),
    -- Alias o rol, nunca un nombre real (requisito 7).
    autor             text not null check (length(btrim(autor)) > 0),
    fecha             timestamptz not null default now()
);

create index if not exists investigaciones_por_claim on legalmente.investigaciones (claim_id);

-- ---------------------------------------------------------------------------
-- 5. Piezas derivadas (una pieza aprobada, muchas superficies)
-- ---------------------------------------------------------------------------

create table if not exists legalmente.piezas_derivadas (
    derivada_id            uuid primary key default gen_random_uuid(),
    content_id             text not null
        references legalmente.piezas (content_id) on delete cascade,

    superficie             text not null
        check (superficie in ('WEB', 'INSTAGRAM', 'FACEBOOK', 'LINKEDIN',
                              'APP', 'JUEGO', 'OTRA')),
    formato                text not null
        check (formato in ('VERTICAL_9_16', 'SOCIAL_4_5', 'SOCIAL_1_1',
                           'HORIZONTAL_16_9')),
    asset_sha256           text
        check (asset_sha256 is null or asset_sha256 ~ '^[0-9a-f]{64}$'),

    url_publicada          text,
    publicada_en           timestamptz,

    -- Autorización humana de PUBLICACIÓN. Es distinta de la aprobación del
    -- claim: aprobar el contenido no autoriza publicarlo.
    autorizacion_publicacion         text not null default 'PENDIENTE'
        check (autorizacion_publicacion in ('PENDIENTE', 'AUTORIZADA', 'DENEGADA')),
    autorizacion_responsable         text,
    autorizacion_fecha               timestamptz,

    creado_en              timestamptz not null default now(),

    -- FAIL-CLOSED 7: no se registra una publicación sin autorización humana
    -- identificada y fechada.
    constraint publicar_exige_autorizacion check (
        publicada_en is null
        or (autorizacion_publicacion = 'AUTORIZADA'
            and autorizacion_responsable is not null
            and length(btrim(autorizacion_responsable)) > 0
            and autorizacion_fecha is not null)
    ),

    -- FAIL-CLOSED 8: publicada sin URL no es trazable.
    constraint publicada_exige_url check (
        publicada_en is null
        or (url_publicada is not null and length(btrim(url_publicada)) > 0)
    )
);

create index if not exists derivadas_por_pieza on legalmente.piezas_derivadas (content_id);

-- ---------------------------------------------------------------------------
-- 6. Métricas y 7. Aprendizaje
-- ---------------------------------------------------------------------------

create table if not exists legalmente.metricas (
    metrica_id       uuid primary key default gen_random_uuid(),
    derivada_id      uuid not null
        references legalmente.piezas_derivadas (derivada_id) on delete cascade,
    capturada_en     timestamptz not null default now(),

    reacciones       integer check (reacciones is null or reacciones >= 0),
    compartidos      integer check (compartidos is null or compartidos >= 0),
    guardados        integer check (guardados is null or guardados >= 0),
    alcance          integer check (alcance is null or alcance >= 0),

    -- De dónde salió la cifra. Hoy siempre MANUAL: no hay ninguna API de
    -- métricas conectada, y decir lo contrario falsearía el origen del dato.
    origen_del_dato  text not null default 'MANUAL'
        check (origen_del_dato in ('MANUAL', 'API_PLATAFORMA', 'IMPORTADO_DRIVE'))
);

create index if not exists metricas_por_derivada on legalmente.metricas (derivada_id);

create table if not exists legalmente.aprendizajes (
    aprendizaje_id  uuid primary key default gen_random_uuid(),
    derivada_id     uuid references legalmente.piezas_derivadas (derivada_id) on delete set null,
    content_id      text references legalmente.piezas (content_id) on delete set null,

    texto           text not null check (length(btrim(texto)) > 0),
    -- Un aprendizaje lo decide un humano mirando datos; el sistema no concluye
    -- solo. Alias o rol, nunca nombre real.
    decidido_por    text not null check (length(btrim(decidido_por)) > 0),
    fecha           timestamptz not null default now(),

    -- Un aprendizaje colgado de nada no es trazable.
    constraint aprendizaje_anclado check (
        derivada_id is not null or content_id is not null
    )
);

-- ---------------------------------------------------------------------------
-- 8. Invariantes que una restricción de columna no puede expresar
-- ---------------------------------------------------------------------------

-- FAIL-CLOSED 9: una pieza no puede abrir su gate global si alguno de sus
-- claims lo tiene cerrado. El techo de la pieza es el mínimo de sus claims,
-- nunca el máximo — misma regla que el validador aplica por país.
create or replace function legalmente.fn_gate_global_es_el_minimo()
returns trigger
language plpgsql
security invoker
set search_path = legalmente, pg_temp
as $$
begin
    if new.gate_global_arte = 'ABIERTO' then
        if new.contenido_hash_sha256 is null then
            raise exception
                'gate_global_arte ABIERTO exige contenido_hash_sha256 (pieza %)', new.content_id;
        end if;
        if exists (select 1 from legalmente.claims c
                   where c.content_id = new.content_id and c.gate_arte <> 'ABIERTO')
        then
            raise exception
                'gate_global_arte ABIERTO pero la pieza % tiene claims con gate CERRADO', new.content_id;
        end if;
        if not exists (select 1 from legalmente.claims c where c.content_id = new.content_id) then
            raise exception
                'gate_global_arte ABIERTO sin ningun claim registrado (pieza %)', new.content_id;
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_gate_global_es_el_minimo on legalmente.piezas;
create trigger trg_gate_global_es_el_minimo
    before insert or update on legalmente.piezas
    for each row execute function legalmente.fn_gate_global_es_el_minimo();

-- FAIL-CLOSED 10: un claim no puede quedar APTO_PARA_NARRATIVA sin al menos
-- una fuente que alcance el Nivel 1 (los tres booleanos, y registro oficial
-- si es una fuente oficial).
create or replace function legalmente.fn_apto_exige_fuente_nivel_1()
returns trigger
language plpgsql
security invoker
set search_path = legalmente, pg_temp
as $$
begin
    if new.estado = 'APTO_PARA_NARRATIVA' then
        if not exists (
            select 1 from legalmente.fuentes f
            where f.claim_id = new.claim_id
              and f.origen_oficial_confirmado
              and f.texto_exacto_consultado
              and f.vigencia_comprobada
              and (f.tipo_fuente not in ('NORMA_OFICIAL', 'JURISPRUDENCIA_OFICIAL',
                                         'AUTORIDAD_PUBLICA_OFICIAL')
                   or (f.registro_oficial_id is not null
                       and length(btrim(f.registro_oficial_id)) > 0))
        ) then
            raise exception
                'claim % no puede ser APTO_PARA_NARRATIVA: ninguna fuente alcanza Nivel 1', new.claim_id;
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_apto_exige_fuente_nivel_1 on legalmente.claims;
create trigger trg_apto_exige_fuente_nivel_1
    after insert or update on legalmente.claims
    for each row execute function legalmente.fn_apto_exige_fuente_nivel_1();

-- FAIL-CLOSED 11: no se marca una pieza PUBLISHED si no tiene ninguna
-- derivada realmente publicada.
create or replace function legalmente.fn_published_exige_derivada()
returns trigger
language plpgsql
security invoker
set search_path = legalmente, pg_temp
as $$
begin
    if new.publicacion = 'PUBLISHED'
       and not exists (select 1 from legalmente.piezas_derivadas d
                       where d.content_id = new.content_id and d.publicada_en is not null)
    then
        raise exception
            'pieza % marcada PUBLISHED sin ninguna derivada publicada', new.content_id;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_published_exige_derivada on legalmente.piezas;
create trigger trg_published_exige_derivada
    before insert or update on legalmente.piezas
    for each row execute function legalmente.fn_published_exige_derivada();

-- ---------------------------------------------------------------------------
-- 9. La única superficie de lectura pública
-- ---------------------------------------------------------------------------

-- La web, la app y el juego leen de AQUÍ, nunca de las tablas base. Así, la
-- condición de "publicable" se define una sola vez: si mañana se endurece,
-- se endurece para todas las superficies a la vez.
create or replace view legalmente.piezas_publicables
with (security_invoker = true)
as
select p.content_id,
       p.version,
       p.titulo_de_trabajo,
       p.materia,
       p.capa_jurisdiccional,
       d.superficie,
       d.formato,
       d.url_publicada,
       d.publicada_en
from legalmente.piezas p
join legalmente.piezas_derivadas d on d.content_id = p.content_id
where p.publicacion = 'PUBLISHED'
  and p.gate_global_arte = 'ABIERTO'
  and p.contenido_hash_sha256 is not null
  and d.publicada_en is not null
  and d.autorizacion_publicacion = 'AUTORIZADA';

comment on view legalmente.piezas_publicables is
    'Único punto de lectura para superficies externas. No expone claims, fuentes ni investigación: una pieza publicada no necesita exponer su aparato probatorio para renderizarse.';

-- ---------------------------------------------------------------------------
-- 10. RLS — denegar por defecto, en TODAS las tablas
-- ---------------------------------------------------------------------------

alter table legalmente.piezas            enable row level security;
alter table legalmente.claims            enable row level security;
alter table legalmente.fuentes           enable row level security;
alter table legalmente.investigaciones   enable row level security;
alter table legalmente.piezas_derivadas  enable row level security;
alter table legalmente.metricas          enable row level security;
alter table legalmente.aprendizajes      enable row level security;

-- Sin ninguna policy, RLS deniega todo a anon y authenticated. Ese es el
-- estado deseado para las tablas base: NO se crean policies de lectura para
-- ellas. El rol service_role (usado solo por el pipeline, nunca por el
-- navegador) omite RLS por diseño de Supabase.
--
-- Lo único legible desde fuera es la vista, y solo para piezas ya publicadas:
grant usage on schema legalmente to anon, authenticated;
grant select on legalmente.piezas_publicables to anon, authenticated;

-- Y explícitamente NADA más:
revoke all on legalmente.piezas           from anon, authenticated;
revoke all on legalmente.claims           from anon, authenticated;
revoke all on legalmente.fuentes          from anon, authenticated;
revoke all on legalmente.investigaciones  from anon, authenticated;
revoke all on legalmente.piezas_derivadas from anon, authenticated;
revoke all on legalmente.metricas         from anon, authenticated;
revoke all on legalmente.aprendizajes     from anon, authenticated;

commit;
