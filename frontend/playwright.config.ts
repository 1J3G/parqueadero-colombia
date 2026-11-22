import { defineConfig } from '@playwright/test';
import { resolve } from 'node:path';

const frontendRoot = __dirname;
const backendRoot = resolve(frontendRoot, '../backend');
const pythonExecutable = resolve(backendRoot, '.venv/Scripts/python.exe');

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:4201',
    browserName: 'chromium',
    headless: true,
  },
  webServer: [
    {
      command: `"${pythonExecutable}" -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --no-access-log`,
      cwd: backendRoot,
      url: 'http://127.0.0.1:8011/openapi.json',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: 'npm start -- --host 127.0.0.1 --port 4201 --proxy-config proxy.e2e.conf.json',
      cwd: frontendRoot,
      url: 'http://127.0.0.1:4201',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
