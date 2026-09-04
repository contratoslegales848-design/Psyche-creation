# Almacén canónico de piezas aprobadas

Primer cimiento técnico, según la **decisión de arquitectura del 2026-09-04**:
el almacén vive en un **proyecto Supabase propio y dedicado de LegalMente**. El
proyecto existente de la cuenta `legallmente-alt` **no se reutiliza** (otra
cuenta, hibernado, sin decisión expresa de reutilización).

**Estado: `CONFIGURATION_REQUIRED`.** No hay ninguna conexión abierta, ningún
proyecto creado y ninguna credencial en este repositorio. Lo que hay es el
diseño completo, listo para revisar antes de tocar nada.

```bash
python3 store/config.py          # estado de configuración (nunca imprime claves)
python3 store/seed_sintetico.py  # los datos sintéticos y su veredicto
cd store && python3 -m unittest test_store   # 52 pruebas
```

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `migrations/0001_almacen_piezas_aprobadas.sql` | Migración propuesta: 7 tablas, 3 triggers, 1 vista, RLS |
| `config.py` | Variables de entorno y estado. Nunca simula una conexión |
| `fail_closed.py` | Guardián de escritura en Python, antes de la base de datos |
| `seed_sintetico.py` | Datos de desarrollo imposibles de confundir con lo real |
| `test_store.py` | 52 pruebas, casi todas de negativa |

---

## 1. Modelo de datos

Siete tablas, una vista. La forma sigue la exigencia de trazabilidad: desde una
URL publicada se puede llegar hacia atrás hasta la fuente oficial que la
sostiene, y hacia delante hasta el aprendizaje que produjo.

```
piezas (content_id, version, estado_agregado, gate_global_arte,
        capa_jurisdiccional, contenido_hash_sha256, publicacion)
  │
  ├── claims (claim_id, texto_exacto, tipo, ubicación, alcance,
  │           jurisdicción[], estado, gate_arte, revisión_*)
  │     ├── fuentes (tipo_fuente, organismo, localizador,
  │     │            registro_oficial_id, los 3 booleanos de Nivel 1)
  │     └── investigaciones (hallazgo, método, autor, fecha)
  │
  └── piezas_derivadas (superficie, formato, asset_sha256,
        │               url_publicada, autorización_publicación_*)
        ├── metricas (reacciones, compartidos, guardados, origen_del_dato)
        └── aprendizajes (texto, decidido_por)
```

La cadena de trazabilidad que pediste, columna por columna:

| Lo exigido | Dónde vive |
|---|---|
| `content_id` | `piezas.content_id`, propagado por FK a todo lo demás |
| investigación | `investigaciones` (hallazgo + método + autor) |
| claims | `claims` |
| fuentes | `fuentes`, con localizador y registro oficial |
| jurisdicción | `claims.jurisdiccion[]` y `fuentes.jurisdicciones_cubiertas[]` |
| aprobación humana | `claims.revision_*` (estado, revisor, fecha, **hash**) |
| versión | `piezas.version`, único junto a `content_id` |
| piezas derivadas | `piezas_derivadas`, una por superficie |
| URL publicada | `piezas_derivadas.url_publicada` |
| métricas | `metricas`, con `origen_del_dato` |
| aprendizaje | `aprendizajes`, siempre anclado a una derivada o a una pieza |

### Los cuatro estados no equivalentes, en columnas distintas

Esta es la razón de que no haya un único campo `aprobado`:

1. `claims.estado = APTO_PARA_NARRATIVA` → la evidencia permite **pedir**
   revisión humana.
2. `claims.revision_estado = APROBADO` (+ hash) → un humano aprobó **ese texto
   exacto**.
3. `gate_arte = ABIERTO` → puede empezar a producirse arte.
4. `piezas_derivadas.autorizacion_publicacion = AUTORIZADA` → puede publicarse.

Ninguno implica el siguiente. Colapsarlos en un booleano es exactamente el
fallo que este esquema existe para impedir.

---

## 2. Fail-closed: dos barreras que dicen lo mismo

**Barrera 1 — Python (`fail_closed.py`)**, antes de enviar nada.
**Barrera 2 — Postgres**, restricciones y triggers en la migración.

Se repiten a propósito. Una prueba compara ambas listas: si divergen, la
divergencia es el fallo.

Las once negativas implementadas:

| # | No se puede registrar… | Dónde |
|---|---|---|
| 1 | una aprobación sin revisor, fecha y hash | `CHECK aprobacion_completa` |
| 2 | un `gate_arte` abierto sin evidencia + aprobación + hash | `CHECK gate_exige_evidencia_y_aprobacion` |
| 3 | un claim nacional sin país | `CHECK nacional_exige_jurisdiccion` |
| 4 | Capa A con menos de 3 jurisdicciones | `CHECK capa_a_exige_tres_jurisdicciones` |
| 5 | "comprobado" sin fecha de comprobación | `CHECK verificacion_fechada` |
| 6 | una fuente oficial sin localizador concreto | `CHECK oficial_exige_localizador` |
| 7 | una publicación sin autorización humana identificada | `CHECK publicar_exige_autorizacion` |
| 8 | una publicación sin URL | `CHECK publicada_exige_url` |
| 9 | un gate global abierto con algún claim cerrado | trigger `fn_gate_global_es_el_minimo` |
| 10 | `APTO_PARA_NARRATIVA` sin ninguna fuente Nivel 1 | trigger `fn_apto_exige_fuente_nivel_1` |
| 11 | `PUBLISHED` sin derivada publicada | trigger `fn_published_exige_derivada` |

El techo de una pieza es el **mínimo** de sus claims, nunca el máximo — la
misma regla que el validador aplica por país.

---

## 3. Políticas RLS

**Denegar por defecto, y no crear ni una sola policy sobre las tablas base.**
Con RLS activado y sin policies, Postgres deniega a `anon` y `authenticated`.
Eso es lo deseado: las fuentes, la investigación y las aprobaciones **no** son
datos públicos.

| Rol | Puede |
|---|---|
| `anon` (navegador) | `SELECT` sobre la vista `piezas_publicables`, nada más |
| `authenticated` | Lo mismo que `anon`. No hay usuarios todavía (requisito 7) |
| `service_role` | Todo — omite RLS por diseño de Supabase. **Solo el pipeline, nunca el navegador** |

La vista `piezas_publicables` exige las cuatro condiciones a la vez
(`PUBLISHED` + gate abierto + hash presente + autorización de publicación) y
**no expone claims, fuentes ni investigación**: una pieza publicada no necesita
enseñar su aparato probatorio para renderizarse.

Definir "publicable" una sola vez, en la vista, es lo que hace que endurecerlo
mañana lo endurezca para la web, la app y el juego a la vez.

> `SUPABASE_SERVICE_ROLE_KEY` nunca puede llegar al navegador. Si acaba en una
> variable `NEXT_PUBLIC_*` o en un bundle de cliente, RLS deja de proteger nada.

---

## 4. Variables de entorno

```bash
NEXT_PUBLIC_SUPABASE_URL=        # https://<ref>.supabase.co del proyecto DEDICADO
NEXT_PUBLIC_SUPABASE_ANON_KEY=   # clave anónima; solo lee la vista pública
SUPABASE_SERVICE_ROLE_KEY=       # solo servidor/pipeline. NUNCA en el cliente
```

- Lectura necesita las dos primeras; escritura, la primera y la tercera.
- Si falta cualquiera → `CONFIGURATION_REQUIRED`, y **no se intenta ninguna
  conexión**.
- Una URL que no tenga forma de proyecto Supabase → `ConfiguracionInvalida`.
- Una URL que apunte al proyecto de `legallmente-alt` → **rechazada**, con el
  motivo, para que una variable copiada por inercia no cree esa dependencia
  en silencio.

---

## 5. Seed sintético

Dos piezas, ambas verificables y ninguna confundible con contenido real:

- `LM-SINTETICO-001` — gate **cerrado**: el caso normal hoy.
- `LM-SINTETICO-002` — gate **abierto** con la conjunción completa: demuestra
  que el camino feliz existe de verdad, no solo el rechazo.

Salvaguardas: prefijo `LM-SINTETICO-` en todo id; URLs en `example.invalid`
(reservado por RFC 2606, nunca resolverá); revisores como `rol:...`, jamás
personas; todo texto empieza por `DATO SINTETICO`; **ninguna llega a
`PUBLISHED`** — un seed que simule una publicación enseña a saltarse la
autorización humana. El hash del seed se calcula de verdad sobre su texto: uno
constante haría pasar el camino feliz sin demostrar nada.

---

## 6. Procedimiento de configuración del proyecto dedicado

Ninguno de estos pasos está ejecutado. **Los pasos 1 a 3 son del fundador**: yo
no puedo crear proyectos ni manejar credenciales.

1. **Crear el proyecto** en la cuenta que LegalMente vaya a usar como propia.
   Nombre sugerido `legalmente-canon`. Región: la más cercana a la audiencia
   principal. Guardar la contraseña de base de datos en un gestor, no en el repo.
2. **Copiar las tres credenciales** desde *Project Settings → API*.
3. **Exportarlas** en el entorno de desarrollo (y como secretos del entorno de
   despliegue, nunca en un `.env` commiteado). Comprobar con
   `python3 store/config.py` que aparece `CONFIGURED`.
4. **Revisar la migración** `migrations/0001_almacen_piezas_aprobadas.sql`
   entera antes de aplicarla. Es un texto propuesto, no ejecutado.
5. **Aplicarla** en el proyecto dedicado (SQL Editor, o `apply_migration` con
   autorización expresa para esa sesión).
6. **Verificar el cierre**: que `anon` no pueda leer `legalmente.claims` ni
   `legalmente.fuentes`, y que sí pueda leer `piezas_publicables`. Si `anon`
   lee una tabla base, parar: RLS no está haciendo su trabajo.
7. **Cargar el seed sintético** y comprobar que el fail-closed rechaza lo que
   debe. Solo entonces tiene sentido pensar en datos reales.

### Lo que este diseño NO autoriza

Merge, deploy, publicación, activación de datos reales, PII, documentos de
usuarios, casos personales, pagos, servicios profesionales ni Supabase Storage.
Todo eso queda fuera hasta una decisión posterior — y Storage, además, hasta
cerrar privacidad, retención, borrado, seguridad y términos.
