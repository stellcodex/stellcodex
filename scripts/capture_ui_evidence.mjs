import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('/var/www/stellcodex/frontend/node_modules/playwright');

const BASE_URL = process.env.FRONT_BASE || 'http://127.0.0.1:3100';
const REPORT_DIR = process.env.REPORT_DIR || '/var/www/stellcodex/_reports/FINAL_SHIP';
const SCREENS_DIR = path.join(REPORT_DIR, 'screens');
const FILE_ID = process.env.UI_PROOF_FILE_ID || '';
const FILE_NAME = process.env.UI_PROOF_FILENAME || '';
const TOKEN = process.env.UI_PROOF_TOKEN || '';

if (!FILE_ID || !FILE_NAME || !TOKEN) {
  throw new Error('Missing UI_PROOF_FILE_ID/UI_PROOF_FILENAME/UI_PROOF_TOKEN');
}

function extractWorkspaceId(url) {
  const m = url.match(/\/workspace\/([^/?#]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

async function waitForText(page, pattern, timeout = 30000) {
  await page.locator(`text=${pattern}`).first().waitFor({ timeout });
}

async function existsText(page, pattern) {
  return (await page.locator(`text=${pattern}`).count()) > 0;
}

const evidence = {
  generated_at: new Date().toISOString(),
  base_url: BASE_URL,
  file_id: FILE_ID,
  file_name: FILE_NAME,
  urls: {},
  markers: {},
};

await fs.mkdir(SCREENS_DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
await context.addInitScript((token) => {
  window.localStorage.setItem('stellcodex_access_token', token);
  window.localStorage.removeItem('scx_token');
  document.cookie = `stellcodex_access_token=${encodeURIComponent(token)}; path=/; SameSite=Lax`;
  document.cookie = 'scx_token=; Max-Age=0; path=/; SameSite=Lax';
}, TOKEN);
const page = await context.newPage();

try {
  await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForText(page, 'STELLCODEX Landing Dashboard', 20000);
  evidence.urls.landing = page.url();
  evidence.markers.landing_dashboard = await existsText(page, 'STELLCODEX Landing Dashboard');
  evidence.markers.landing_new_workspace = await existsText(page, 'New Workspace');
  await page.screenshot({ path: path.join(SCREENS_DIR, '01_landing_page.png'), fullPage: true });

  await page.getByRole('link', { name: 'New Workspace' }).click();
  await page.waitForURL(/\/workspace\//, { timeout: 45000 });
  const workspaceId = extractWorkspaceId(page.url());
  if (!workspaceId) throw new Error(`workspaceId not found in URL: ${page.url()}`);

  const filesUrl = `${BASE_URL}/workspace/${encodeURIComponent(workspaceId)}/files`;
  await page.goto(filesUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForText(page, 'File Ledger', 30000);
  await waitForText(page, FILE_NAME, 30000);
  evidence.urls.files = page.url();
  evidence.markers.files_file_ledger = await existsText(page, 'File Ledger');
  evidence.markers.files_uploaded_item = await existsText(page, FILE_NAME);
  await page.screenshot({ path: path.join(SCREENS_DIR, '02_files_with_uploaded_item.png'), fullPage: true });

  const viewerUrl = `${BASE_URL}/view/${encodeURIComponent(FILE_ID)}`;
  await page.goto(viewerUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await waitForText(page, FILE_NAME, 45000);
  evidence.urls.viewer = page.url();
  evidence.markers.viewer_file_name = await existsText(page, FILE_NAME);
  evidence.markers.viewer_download_button = await existsText(page, 'Download');
  await page.screenshot({ path: path.join(SCREENS_DIR, '03_viewer_page_open.png'), fullPage: true });

  const agentUrl = `${BASE_URL}/workspace/${encodeURIComponent(workspaceId)}/app/agentdashboard?file_id=${encodeURIComponent(FILE_ID)}`;
  await page.goto(agentUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.getByRole('button', { name: 'Run', exact: true }).first().click();
  await page.getByRole('button', { name: 'Run Agent' }).first().click();
  await waitForText(page, 'Agent Output', 60000);
  evidence.urls.agent = page.url();
  evidence.markers.agent_output = await existsText(page, 'Agent Output');
  evidence.markers.agent_findings = await existsText(page, 'Findings');
  await page.screenshot({ path: path.join(SCREENS_DIR, '04_agent_output_tab.png'), fullPage: true });

  evidence.result = 'PASS';
} catch (error) {
  evidence.result = 'FAIL';
  evidence.error = error instanceof Error ? error.message : String(error);
  await page.screenshot({ path: path.join(SCREENS_DIR, '99_ui_error.png'), fullPage: true }).catch(() => {});
  throw error;
} finally {
  await fs.writeFile(path.join(SCREENS_DIR, 'ui_evidence.json'), `${JSON.stringify(evidence, null, 2)}\n`, 'utf8');
  await context.close();
  await browser.close();
}
