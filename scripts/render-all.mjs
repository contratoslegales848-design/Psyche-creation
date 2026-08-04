import {readdirSync, readFileSync} from 'node:fs';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';

const contentDirectory = join(process.cwd(), 'content');
const files = readdirSync(contentDirectory)
  .filter((file) => file.endsWith('.json'))
  .sort();

if (files.length === 0) {
  throw new Error('No se encontraron archivos JSON en content/.');
}

for (const file of files) {
  const piece = JSON.parse(readFileSync(join(contentDirectory, file), 'utf8'));

  if (typeof piece.id !== 'string' || piece.id.trim() === '') {
    throw new Error(`${file}: falta un id válido.`);
  }

  console.log(`\nRenderizando composición: ${piece.id}`);
  const result = spawnSync(
    'npx',
    [
      'remotion',
      'render',
      'src/index.ts',
      piece.id,
      `out/${piece.id}.mp4`,
      '--chromium-options=--no-sandbox --disable-setuid-sandbox',
    ],
    {stdio: 'inherit', shell: process.platform === 'win32'},
  );

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
