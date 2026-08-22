# LegalMente — pipeline automatizado de video

Genera videos verticales 1080×1920 con Remotion 4, React y TypeScript. Cada JSON de `content/` registra una composición independiente con el mismo `id`.

La línea editorial, dirección de arte y reglas de redacción están definidas en [`docs/legalmente-marca-y-estilo.md`](docs/legalmente-marca-y-estilo.md). El pipeline valida automáticamente la regla de máximo 18 palabras por `frase` (§1.3 del manual); las demás reglas (tono, pilares temáticos, atribución) son editoriales y no se validan por código.

Las tipografías EB Garamond y UnifrakturCook están autoalojadas mediante paquetes npm para que el render no dependa de Google Fonts ni de una conexión externa.

## Requisitos locales

- Node.js 20
- npm

```bash
npm install
npx remotion studio
```

## Agregar una pieza nueva

1. Copia la imagen a `assets/images/`.
2. Si tendrá voz o música, copia el MP3 a `assets/audio/`.
3. Copia el JSON de ejemplo:

```bash
cp content/ejemplo.json content/maxima-001.json
```

4. Edita todos sus campos y usa un `id` único:

```json
{
  "id": "maxima-001",
  "titulo": "Dormientibus non succurrit ius",
  "frase": "El derecho no favorece a quien duerme sobre sus derechos",
  "remate": "Máxima del Derecho Romano",
  "marca": "LegalMente",
  "imagen": "assets/images/maxima-001.jpg",
  "audio": "assets/audio/maxima-001.mp3",
  "duracionSegundos": 10
}
```

`audio` puede ser `null`. La duración permitida es de 8 a 15 segundos.

## Validar y renderizar localmente

```bash
npm run typecheck
npx remotion studio
npx remotion render src/index.ts maxima-001 out/maxima-001.mp4 \
  --chromium-options="--no-sandbox --disable-setuid-sandbox"
```

Para renderizar todos los JSON:

```bash
npm run render:all
```

## GitHub Actions

El workflow se ejecuta automáticamente cuando cambia `content/**`.

Ejecución manual:

1. Abre **Actions → Renderizar videos LegalMente → Run workflow**.
2. Escribe un `composition_id` para renderizar una sola pieza.
3. Déjalo vacío para renderizar todas.
4. Descarga el artifact `videos-legalmente` al terminar.

En Ubuntu 24.04, `libasound2t64` sustituye a `libasound2`; el workflow detecta automáticamente cuál está disponible.
