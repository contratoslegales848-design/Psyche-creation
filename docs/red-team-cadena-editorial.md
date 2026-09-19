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

**A10. Hacer avanzar una pieza basada en un caso reconocible declarando que la
revisión de confidencialidad "no aplica".** *(Era C1, el hueco más serio.)*
Doce indicadores deterministas se aplican sobre los campos publicables del claim.
Si alguno dispara, `required` pasa a ser obligatoriamente `true` y el gate solo se
abre con revisión humana firmada y motivada. Aprobar exige constancia real de qué
se revisó; bloquear exige revisor y motivo, porque bloquear también es una decisión
con responsable. Fixtures: `bad-47`, `bad-48`, `bad-49`.
Límite declarado: los indicadores son un **suelo**, no un techo — ver B5.

**A12. Sostener un claim aprobado con una fuente derogada o sustituida.**
El libro mayor de vigencia bloquea el claim: `SUPERSEDED`/`REPEALED` → veredicto
BLOQUEADO; `NEEDS_REVIEW`, sin registrar o `UNKNOWN` sobre una norma → REQUIERE
REVISIÓN. El veredicto se **deriva y nunca se escribe en el claim**: hacerlo
cambiaría su hash e invalidaría en silencio la aprobación firmada. Pruebas:
`test_fuente_superseded_exige_revision`, `test_fuente_repealed_exige_revision`,
`test_unknown_falla_cerrado_cuando_la_vigencia_es_necesaria`,
`test_el_veredicto_nunca_se_escribe_en_el_claim`.

**A13. Cambiar la URL de una fuente para heredar su vigencia comprobada.**
El `source_id` se deriva de la URL canonicalizada: una URL nueva **es otra fuente**,
sin vigencia heredada. Enlazarlas exige `supersedes`/`superseded_by` simétricos y sin
ciclos. Prueba: `test_url_cambiada_deja_de_emparejar`.

**A14. Registrar dos veces la misma fuente, o atribuirla al país equivocado.**
`canonical_url` es única en el libro mayor —dos entradas serían dos verdades sobre
la misma vigencia— y cada entrada se contrasta contra el registro de organismos:
hostname por frontera real de subdominio, jurisdicción y tipo entre los que ese
organismo admite. Pruebas: `test_url_canonica_duplicada_es_error`,
`test_pais_incorrecto_para_el_organismo_es_error`,
`test_hostname_que_no_pertenece_al_organismo_es_error`.

**A15. Inventario obsoleto que muestra un estado que ya no es cierto.**
El índice es determinista y **no depende del reloj**; `inventory.py check` lo
regenera y compara. Si discrepa de los artefactos, falla — y los artefactos mandan.
Pruebas: `test_check_detecta_un_inventario_obsoleto`,
`test_el_inventario_almacenado_no_depende_del_reloj`.

**A16. Registrar dos veces la misma publicación, o medir la pieza equivocada.**
`PUBLICACION_YA_REGISTRADA` detecta dos piezas apuntando a la misma URL publicada;
la cadena post-aprobación ya exigía que una medición corresponda a una publicación
existente de ese `content_id` y esa plataforma. Pruebas:
`test_publicacion_ya_registrada_se_detecta`, `test_medicion_sin_publicacion_falla`.

**A11. Renderizar como pieza publicable un JSON sin ningún claim packet detrás.**
*(Era C2, la cadena cortada.)* Cada artefacto de `content/` declara su procedencia
en uno de tres modos, sin modo por defecto. `src/content.ts` falla cerrado sobre la
forma en tiempo de bundle — comprobado: quitando `procedencia`, el bundle de
Remotion falla con exit 1 — y `scripts/validate-content-provenance.py` verifica el
fondo en CI: que el handoff exista y valide, que los hashes coincidan con el hash
canónico del claim, y que la capa jurisdiccional no se reetiquete al pasar a arte.

---

## B. Vectores parcialmente mitigados

**B1. Fuente oficial que cambió después de consultarse.** *(Parcialmente cerrado
el 2026-08-27.)* Existe ahora un libro mayor de vigencia
(`references/source-freshness.json`) y un control offline: una fuente marcada
`SUPERSEDED` o `REPEALED` bloquea el claim que sostiene, una `NEEDS_REVIEW` o
`UNKNOWN` donde hace falta vigencia lo manda a revisión, y el plazo de revisión
vencido degrada un `CURRENT` automáticamente. Fail-closed sobre claims con gate
ABIERTO; advertencia con el gate cerrado. Ver `A12` y `references/README-vigencia.md`.
Lo que sigue abierto es lo que ningún control offline puede cerrar: **nadie avisa
desde fuera**. Si un humano no investiga y no actualiza el libro mayor, una norma
derogada sigue marcada `CURRENT` hasta que venza su plazo. El control convierte
"nadie se entera nunca" en "nadie se entera hasta la fecha de revisión", que es una
mejora real y una garantía limitada. Ver también ADR 0001.

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

**B5. Contenido identificable que ningún indicador reconoce.**
Lo que queda de C1. Los indicadores detectan las formas habituales de fuga (caso
propio, primera persona, expediente, identificador, importe, dato de contacto,
razón social, tratamiento con nombre). No detectan un caso reconocible narrado en
tercera persona, sin cifras y sin marcadores léxicos — que es precisamente la forma
más peligrosa, porque es la que un profesional escribe sin darse cuenta. Por eso la
revisión humana sigue siendo obligatoria por decisión del fundador, y el control
solo decide **cuándo mirar**, nunca si algo es confidencial.
Cobertura verificada del estado de partida: ninguno de los 56 fixtures ni de los 3
paquetes del piloto dispara un indicador, y 9 frases de contenido educativo
legítimo permanecen limpias — un control que marcara todo se acabaría desactivando.

**B6. Una pieza NO_APLICA mal clasificada.**
Lo que queda de C2. El modo `NO_APLICA` existe porque hay piezas que legítimamente
no llevan afirmación jurídica (cita histórica, formato de marca). Exige motivo
tipificado de una lista cerrada, justificación de al menos 30 caracteres y un
humano identificado con fecha — pero no puede comprobar que la clasificación sea
correcta. Alguien puede etiquetar como cita histórica algo que en realidad enuncia
una regla vigente. El control lo convierte en una decisión trazable con
responsable; no la sustituye.

---

## C. Vectores abiertos (sin control ejecutable — riesgo declarado)

**C1 y C2 se cerraron el 2026-08-27.** Se conserva su enunciado original en la
sección A (A10 y A11) junto al control que ahora los bloquea. Lo que queda de
ambos, que no es poco, está en B5 y B6.

**C3. Nada impide publicar fuera del sistema.**
La cadena registra decisiones; no controla las cuentas. Alguien con acceso a la
plataforma publica sin pasar por aquí. El repositorio es un registro de
responsabilidad, no un control de acceso — y debe leerse así.

**C4. Duplicados por paráfrasis.** *(Lo literal, cerrado; lo semántico, abierto.)*
Se detectan cinco colisiones deterministas: `content_id` repetido, composición
repetida, casilla `materia/submateria/concepto` ocupada dos veces, huella
normalizada idéntica y publicación ya registrada. Sigue abierto lo semántico: dos
piezas que dicen lo mismo con palabras distintas pasan los cinco. Exigiría
embeddings o un motor semántico, que no se construye todavía. Hay una prueba que
fija el límite por escrito (`test_la_parafrasis_NO_se_detecta_y_queda_declarado`)
para que nadie suponga una cobertura que no existe.

**C6. Nadie avisa desde fuera de que una norma cambió.**
Lo que queda de B1, y el límite estructural de todo control offline. El libro mayor
solo sabe lo que un humano escribió en él. La vigilancia activa de boletines
oficiales sería un proceso aparte, con red, fuera del validador — y no existe.

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

1. **C6 (vigilancia activa de cambios normativos)** — lo que queda de B1. No se
   cierra con más lógica offline: exige un proceso de research con red, separado
   del validador, que marque fuentes para revisión.
2. **B5 (contenido identificable sin marcadores léxicos)** — no se cierra con más
   expresiones regulares; se cierra con disciplina de revisión y, quizá, con
   evidencia adjunta de qué se leyó.
3. **B3/B4 (autodeclaración)** — mitigable con evidencia adjunta, no con más lógica.
4. **C4 (duplicados por paráfrasis)** — relevante solo al escalar el volumen.

Cerrados el 2026-08-27: C1 (ahora A10), C2 (ahora A11), y los vectores de vigencia,
inventario y duplicación registrados como A12–A16. B1 queda parcialmente cerrado;
lo que resta es C6.
