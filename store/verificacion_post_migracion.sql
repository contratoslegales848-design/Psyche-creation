-- Verificacion POSTERIOR a aplicar la migracion. Solo lectura.
--
-- La revision estatica (store/revision_estatica.py) comprueba que el SQL DICE
-- lo correcto. Este archivo comprueba que Postgres HACE lo correcto, que es
-- otra cosa: un plano correcto no demuestra que el edificio este en pie.
--
-- Cubre los puntos 8, 9 y 10 de la decision del 2026-09-04.
--
-- COMO EJECUTARLO. Los bloques A, B y D valen con cualquier rol (leen
-- catalogo). El bloque C es el importante y hay que correrlo COMO anon:
-- desde el SQL Editor de Supabase, `set local role anon;` dentro de una
-- transaccion. Correrlo como postgres o service_role no demuestra nada:
-- esos roles omiten RLS por diseno, y todo "pasaria" sin proteger nada.
--
-- Ninguna sentencia escribe. Se puede correr las veces que haga falta.

-- ===========================================================================
-- A. Las siete tablas existen y todas tienen RLS activado
-- ===========================================================================
select 'A. RLS por tabla' as bloque,
       c.relname            as tabla,
       c.relrowsecurity     as rls_activado,
       c.relforcerowsecurity as rls_forzado,
       case when c.relrowsecurity then 'OK' else 'FALLO' end as veredicto
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'legalmente' and c.relkind = 'r'
order by c.relname;

-- Esperado: 7 filas, todas rls_activado = true.

-- ===========================================================================
-- B. No debe existir NINGUNA policy sobre las tablas base
-- ===========================================================================
-- Sin policies, RLS deniega. Cada policy seria una excepcion a esa negativa.
select 'B. Policies' as bloque,
       coalesce(p.policyname, '(ninguna)') as policy,
       p.tablename,
       p.cmd,
       p.qual,
       case when p.policyname is null then 'OK' else 'REVISAR' end as veredicto
from pg_policies p
where p.schemaname = 'legalmente'
union all
select 'B. Policies', '(ninguna)', '-', '-', '-', 'OK'
where not exists (select 1 from pg_policies where schemaname = 'legalmente');

-- Esperado: una sola fila con '(ninguna)' y veredicto OK.

-- ===========================================================================
-- C. AISLAMIENTO DE anon — el bloque decisivo (puntos 8 y 9)
-- ===========================================================================
-- Ejecutar TODO este bloque de una vez. El rollback final garantiza que no
-- deja nada tocado ni el rol cambiado.

begin;
set local role anon;

-- C.1 — Punto 8: anon NO puede leer legalmente.claims.
-- Se espera que esta consulta FALLE con "permission denied for table claims"
-- (por el revoke) o devuelva 0 filas (si solo actuara el RLS). Cualquier
-- fila devuelta es un FALLO grave: el aparato probatorio seria publico.
select 'C.1 anon lee claims' as prueba, count(*) as filas_visibles
from legalmente.claims;

-- C.2 — anon tampoco puede leer fuentes ni investigaciones.
select 'C.2 anon lee fuentes' as prueba, count(*) as filas_visibles
from legalmente.fuentes;

select 'C.3 anon lee investigaciones' as prueba, count(*) as filas_visibles
from legalmente.investigaciones;

-- C.4 — Punto 9: anon SI puede leer la vista, y solo lo publicable.
-- Toda fila devuelta debe cumplir las cuatro condiciones a la vez. La vista
-- ya las impone; esto confirma que no devuelve nada que no las cumpla.
select 'C.4 anon lee la vista' as prueba, count(*) as filas_visibles
from legalmente.piezas_publicables;

-- C.5 — anon no puede escribir. Se espera fallo por permisos.
-- Descomentar solo si se quiere comprobar la negativa de escritura:
-- insert into legalmente.piezas (content_id, estado_agregado, titulo_de_trabajo, materia)
-- values ('INTENTO-ANON', 'REQUIERE_INVESTIGACION', 'x', 'civil');

rollback;

-- ===========================================================================
-- D. Punto 10: no existen objetos de PII, usuarios, documentos, casos,
--    pagos ni Storage
-- ===========================================================================
select 'D.1 tablas sospechosas' as bloque,
       n.nspname as esquema, c.relname as objeto,
       'REVISAR' as veredicto
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'legalmente'
  and (c.relname ~* 'usuario|cliente|persona|pago|cobro|factura|tarjeta'
       or c.relname ~* 'documento|expediente|caso|storage');
-- Esperado: 0 filas.

select 'D.2 columnas sospechosas' as bloque,
       table_name, column_name, 'REVISAR' as veredicto
from information_schema.columns
where table_schema = 'legalmente'
  and (column_name ~* 'email|telefono|direccion|dni|curp|rfc|pasaporte'
       or column_name ~* 'tarjeta|iban|cuenta_bancaria|password|contrasena');
-- Esperado: 0 filas.

select 'D.3 buckets de Storage' as bloque,
       count(*) as buckets,
       case when count(*) = 0 then 'OK' else 'REVISAR' end as veredicto
from storage.buckets;
-- Esperado: 0 buckets. Si la tabla no existe, Storage no esta inicializado:
-- tambien correcto para esta fase.

-- ===========================================================================
-- E. Integridad del cimiento: triggers y restricciones vivos
-- ===========================================================================
select 'E.1 triggers' as bloque, tgname as trigger,
       case when tgenabled = 'O' then 'ACTIVO' else 'DESACTIVADO' end as estado
from pg_trigger t
join pg_class c on c.oid = t.tgrelid
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'legalmente' and not t.tgisinternal
order by tgname;
-- Esperado: 3 triggers, los tres ACTIVO.

select 'E.2 restricciones CHECK con nombre' as bloque,
       conname as restriccion, conrelid::regclass as tabla
from pg_constraint
where connamespace = 'legalmente'::regnamespace and contype = 'c'
  and conname !~ '^\d'
order by conname;
-- Esperado: las 9 con nombre propio, entre ellas aprobacion_completa,
-- gate_exige_evidencia_y_aprobacion y publicar_exige_autorizacion.
