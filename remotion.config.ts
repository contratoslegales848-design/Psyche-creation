import {Config} from '@remotion/cli/config';

// Los JSON conservan rutas como assets/images/pieza.jpg.
// Remotion sirve esta carpeta como raíz de archivos estáticos.
Config.setPublicDir('./assets');
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
