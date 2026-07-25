import {Config} from '@remotion/cli/config';

// Chromium ist in dieser Umgebung vorinstalliert (PLAYWRIGHT_BROWSERS_PATH).
// Remotion braucht einen eigenen Browser-Pfad — auf dasselbe Binary zeigen,
// statt ein zweites Chromium herunterzuladen.
const browserPath = process.env.REMOTION_CHROME_PATH;
if (browserPath) {
  Config.setBrowserExecutable(browserPath);
}

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
