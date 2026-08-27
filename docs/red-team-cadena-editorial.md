# Red team de la cadena editorial

Ejercicio adversarial sobre el sistema de verificación y publicación de LegalMente.
Pregunta guía: **¿cómo publicaría yo una falsedad jurídica sin que este repositorio
me detuviera?** Cada vector se declara mitigado, parcialmente mitigado o abierto,
con la evidencia concreta.

Fecha: 2026-08-27 · Alcance: `origin/main` + rama `chore/phase1-technical-readiness`.

---

## A. Vectores cerrados (hay un control ejecutable que los bloquea)

**A1. Declarar el gate abierto a mano en el JSON.**
El validador recalcula el gate y compara con el declarado; una discrepancia es error.
Evidencia: `validate_claim` devuelve el gate canónico; `check_pilot_governance.py`
lo verifica en CI. Fixture: `bad-19-gate-abierto-sin-revision-humana.json`.

**A2. Firmar la aprobación con un hash inventado o desactualizado.**
`compute_content_hash` se recalcula en cada validación. Fixture:
`bad-11-aprobacion-hash-no-coincide.json`.

**A3. Editar el texto del claim después de que un humano lo aprobó.**
Cambia el contenido → cambia el hash → la aprobación deja de ser válida.
`HASH_EXCLUDED_FIELDS` solo excluye `revision_humana` y `gate_arte`, precisamente
para que ningún campo de contenido quede fuera del hash.

**A4. Editar el texto entre la aprobación y el arte.**
Cubierto desde hoy por `ProductionHandoff`: `approved_text` debe ser literalmente
`texto_exacto`. Fixture: `bad-3-texto-modificado-tras-aprobacion.json`.

**A5. Publicar apoyándose solo en el gate de arte.**
Cubierto desde hoy: no hay `PublicationRecord` válido sin `PublicationDecision`
AUTORIZADA. Fixture: `bad-1-publicacion-sin-decision.json`.

**A6. Hacer pasar un dominio parecido por fuente oficial** (`boe.es.evil.com`).
El registro compara por frontera real de subdominio, nunca por subcadena.
Fixtures: `bad-2-boe-es-evil-com.json`, `bad-3-notboe-es.json`,
`bad-44-url-barra-invertida-userinfo.json`.

**A7. Universalizar una regla nacional.**
Capa A exige fuente propia por país; el techo de un claim multijurisdiccional es el
**mínimo** de los países declarados. Fixtures: `bad-4-una-fuente-espanola-cuatro-paises.json`,
`bad-46-capa-b-cobertura-incompleta.json`.

**A8. Apuntar el handoff a un claim packet fuera del repositorio.**
`_resolve_packet` rechaza cualquier ruta que escape de la raíz de la skill.
Prueba: `test_claim_packet_fuera_de_la_skill_falla`.

**A9. Perder por el camino la redacción prohibida de un claim.**
El handoff debe transportarla. Fixture: `bad-13-redaccion-prohibida-no-viaja.json`.

---

## B. Vectores parcialmente mitigados

**B1. Fuente oficial que cambió después de consultarse.**
No hay verificación de deriva: el validador no tiene red por diseño. Solo constan
`fecha_consulta`, `fecha_comprobacion` y `vigencia_comprobada`, que son declaraciones
humanas fechadas. Un cambio normativo posterior **no se detecta**. Ver ADR 0001.

**B2. Un humano firma sin haber leído.**
El sistema comprueba que la firma **conste y esté completa**, no que haya habido
lectura. Es un límite estructural de cualquier control automatizado: la calidad de
la revisión no es verificable por código. Mitigación real: la firma es nominal y
queda registrada con hash del contenido exacto — hay responsabilidad trazable.

**B3. Verificación de fuente autodeclarada.**
`origen_oficial_confirmado`, `texto_exacto_consultado` y `vigencia_comprobada` son
booleanos que declara quien construye el packet. El registro oficial acota el abuso
(el hostname debe corresponder al organismo declarado y a la jurisdicción), pero
declarar `true` sin haber comprobado nada es posible.

**B4. QA de publicación autodeclarado.**
Las seis comprobaciones de `PublicationDecision.qa` las marca el decisor. Son
deliberadamente deterministas y verificables *a ojo* sobre la pieza, pero el
repositorio no ve la pieza: no puede comprobar que la jurisdicción esté realmente
visible en la imagen.

---

## C. Vectores abiertos (sin control ejecutable — riesgo declarado)

**C1. Confidencialidad. Es el hueco más serio.**
`confidentiality_review` existe como campo y puede bloquear el gate, pero **nadie
comprueba su contenido**: no hay detección de nombres, empresas, montos, fechas ni
operaciones identificables procedentes de experiencia profesional privada
(CLAUDE.md §5). El único control ejecutable relacionado es la lista negra de
nombres reales en fixtures y scripts, que protege el *material de prueba*, no el
*contenido publicable*. Una pieza que reutilice un caso reconocible pasaría todos
los controles actuales.
Consecuencia potencial: deber de secreto profesional. Es el candidato número uno a
próximo control.

**C2. El renderizador no exige procedencia.**
`content/*.json` solo valida forma (`src/content.ts`): id, título, frase, remate,
marca, imagen, duración. **No hay ningún campo que ligue una pieza renderizada a un
claim packet aprobado.** `content/ejemplo.json` se renderiza en CI sin respaldo
jurídico alguno. Hoy la cadena está cortada en dos mitades que no se hablan: la
jurídica (`.claude/skills/`) y la de producción (`content/` + `src/`). El
`ProductionHandoff` es el puente diseñado, pero el renderizador todavía no lo exige.

**C3. Nada impide publicar fuera del sistema.**
La cadena registra decisiones; no controla las cuentas. Alguien con acceso a la
plataforma publica sin pasar por aquí. El repositorio es un registro de
responsabilidad, no un control de acceso — y debe leerse así.

**C4. Sin control de duplicados a nivel de contenido.**
La unicidad se comprueba por identificadores (`handoff_id`, `decision_id`,
`content_id`+plataforma), no por semejanza del contenido. Dos piezas casi idénticas
con IDs distintos pasan.

**C5. Las métricas son autodeclaradas.**
`MeasurementRecord` exige coherencia interna (no inventar claves) y una `source`,
pero las cifras las teclea un humano. No hay lectura automatizada de ninguna
plataforma.

---

## D. Lo que este ejercicio NO cubre

- Seguridad de las cuentas y credenciales de plataforma.
- La calidad jurídica sustantiva de una afirmación bien fundamentada pero mal
  razonada: el sistema verifica *procedencia y trazabilidad*, no *corrección
  doctrinal*. Eso sigue siendo humano y siempre lo será.
- El repositorio `legalmente-web`, que tiene su propia superficie.

---

## E. Prioridad sugerida de cierre

1. **C1 (confidencialidad)** — mayor consecuencia, ningún control.
2. **C2 (procedencia en el renderizador)** — convierte la cadena en una cadena real.
3. **B3/B4 (autodeclaración)** — mitigable con evidencia adjunta, no con más lógica.
4. **C4 (duplicados por contenido)** — relevante solo al escalar el volumen.
