# CLAUDE.md — LegalMente / Psyche-creation

Reglas operativas. No es la estrategia (eso vive en Drive) ni la fórmula visual (eso vive en la skill `legalmente-visual-system`). Esto es lo que cualquier sesión de Claude Code debe respetar en este repositorio.

## 1. Identidad

LegalMente es una marca panhispánica de educación jurídica (no una cuenta de asesoría individual). La calidad se sostiene en tres pilares igual de exigibles: rigor jurídico, claridad narrativa, dirección visual. Ninguno sustituye a los otros dos.

## 2. Fuente de verdad

- **Google Drive**: estrategia, decisiones del fundador, contenido aprobado, inventario de publicaciones, matriz de contenido.
- **Este repositorio**: implementación, automatización, trabajo técnico (pipeline de video, sitio web, skills).
- **Este archivo**: reglas operativas de ejecución.

Una mención en un documento de Drive **no es** una capacidad implementada. Antes de asumir que algo existe (una skill, un agente, un hook), verificar el archivo real en `.claude/` o `/root/.claude/`.

## 3. Jerarquía de autoridad

1. Decisiones expresas del fundador.
2. Documento constitucional vigente (neutralidad jurisdiccional).
3. Documento maestro de estado del proyecto.
4. Matriz de contenido e inventario de publicaciones.
5. Skills implementadas en este repo o sincronizadas.
6. Documentos históricos o descartados.
7. Inferencias de cualquier modelo (incluido este).

Ante un conflicto, gana el nivel más alto disponible.

## 4. Reglas jurídicas

- Jurisdicción por defecto: panhispánica / conceptual / comparada. Lo nacional es excepción explícita, nunca supuesto implícito.
- Toda afirmación se clasifica en Capa A (núcleo transversal), Capa B (misma lógica, varía por país) o Capa C (necesariamente nacional, país visible desde el título).
- Prohibida la falsa universalización: presentar una regla de un país como si fuera panhispánica.
- Ninguna IA (este modelo incluido) es fuente jurídica. Toda afirmación necesita fuente identificable y verificable.
- Una cita necesita autor/obra identificable, no solo atribución viral.
- Si una fuente no se verifica, la pieza se bloquea — no se publica "con reserva".
- La aprobación final de cualquier pieza jurídica es siempre humana.
- Todo título, hook, definición, lista, consejo o consecuencia con carga jurídica pasa por verificación **antes** de generar arte — un título también puede contener una afirmación falsa, no solo el cuerpo del texto.

## 5. Reglas de confidencialidad

- No usar nombres, empresas, montos, fechas, operaciones, contratos ni hechos identificables de experiencias profesionales privadas (incluidas las del fundador).
- El material de experiencia práctica (p. ej. el "Addendum" de Drive) solo se usa como patrón anonimizado, nunca como caso reconocible.
- No hay todavía un control automatizado de esto en el repositorio — es un hueco conocido (ver `docs/` y la skill de verificación jurídica, que registra el riesgo pero no lo bloquea por sí sola).

## 6. Reglas de producción

- No producir nuevos bancos grandes de temas/prompts mientras el lote piloto activo no se haya publicado y medido, salvo orden expresa del fundador.
- El arte nunca valida el contenido jurídico — son verificaciones independientes y en ese orden (jurídico antes que visual).
- Canva se usa para texto y montaje controlados, no para generar arte con IA.
- No publicar de forma automática en ninguna plataforma.
- No modificar Google Drive sin autorización explícita para esa sesión.

## 7. Capacidades reales (verificar antes de asumir más)

- Conectados y probados: Google Drive, GitHub.
- Presentes pero sin validar en producción: Canva, Higgsfield, Descript, Meta Ads, Gmail, Google Calendar.
- Bloqueado por autorización pendiente: Instagram.
- Skill operativa: `legalmente-visual-system` (sincronizada, global).
- Skill operativa: `legalmente-legal-verification` (local de este repo, ver `.claude/skills/`).
- No implementados todavía: `legalmente-story-engine`, `legalmente-confidentiality`, los 6 agentes (`legal-researcher`, `legal-auditor`, `narrative-editor`, `visual-director`, `privacy-reviewer`, `growth-analyst`), y los 4 hooks (PRE-NARRATIVA, PRE-ARTE, PRE-PUBLICACIÓN, POST-PUBLICACIÓN). No dar por hecho que existen solo porque están descritos en Drive.

## 8. Límites entre repositorios

- **Psyche-creation** (este repo, público, cuenta `contratoslegales848-design`): pipeline de video Remotion, skills, docs operativos, catálogo de contenido para producción.
- **legalmente-web** (privado, cuenta `legallmente-alt`, si está disponible en la sesión): sitio web Next.js. Esta sesión normalmente no puede hacer push directo ahí (cuentas distintas) — se trabaja por bundle o sesión aparte.

No mezclar código ni responsabilidades de ambos repos sin una decisión explícita del fundador.

## 9. Cierre de tareas

Toda ejecución de Claude Code en este repo termina indicando:
1. Qué se hizo.
2. Qué se verificó (con evidencia, no solo afirmación).
3. Qué se bloqueó y por qué.
4. Qué requiere aprobación humana.
5. Cuál es el siguiente paso ejecutable.
