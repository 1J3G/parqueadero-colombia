import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { expect, test } from '@playwright/test';

interface PaymentFixture {
  operatorDocument: string;
  operatorPassword: string;
  contractId: number;
}

const frontendRoot = resolve(__dirname, '..');
const backendRoot = resolve(frontendRoot, '../backend');
const fixtureScript = resolve(backendRoot, 'tests/create_e2e_payment_fixture.py');
const pythonExecutable = resolve(backendRoot, '.venv/Scripts/python.exe');
const screenshotPath = resolve(frontendRoot, '../docs/evidencia-e2e-pago.png');

test('operator opens cash and registers monthly payment with fiscal receipt', async ({ page }) => {
  test.setTimeout(120_000);
  if (!existsSync(pythonExecutable)) {
    throw new Error(`Backend virtual environment was not found at ${pythonExecutable}`);
  }

  const fixture = JSON.parse(
    execFileSync(pythonExecutable, [fixtureScript], {
      cwd: backendRoot,
      encoding: 'utf8',
      env: { ...process.env, PYTHONPATH: backendRoot },
    }),
  ) as PaymentFixture;

  await page.goto('/payments');
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel('Documento').fill(fixture.operatorDocument);
  await page.getByLabel('Contraseña').fill(fixture.operatorPassword);
  await page.getByRole('button', { name: 'Ingresar' }).click();

  await expect(page.getByRole('heading', { name: 'Apertura de caja' })).toBeVisible();
  await expect(page.getByText('Registre la base de efectivo antes de procesar transacciones.')).toBeVisible();
  await page.getByLabel('Base de efectivo (COP)').fill('50000');
  await page.getByRole('button', { name: 'Abrir caja' }).click();
  await expect(page.getByText(/Caja abierta/)).toBeVisible();

  await page.getByRole('link', { name: 'Pagos' }).click();
  await expect(page.getByRole('heading', { name: 'Pagos y comprobantes' })).toBeVisible();
  const contractSelect = page.getByLabel('Contrato');
  const contractOption = contractSelect.locator('option').filter({ hasText: `#${fixture.contractId} ·` });
  await expect(contractOption).toHaveCount(1);
  const contractLabel = await contractOption.textContent();
  if (!contractLabel) {
    throw new Error(`Contract ${fixture.contractId} was not available in the payment form.`);
  }
  await contractSelect.selectOption({ label: contractLabel });
  await page.getByLabel('Meses pagados').fill('1');
  await page.getByLabel('Valor neto fijado por el negocio (COP)').fill('100000');
  await page.getByLabel('Método de pago').selectOption({ label: 'Efectivo' });
  await page.getByRole('button', { name: 'Registrar pago' }).click();

  const receipt = page.locator('.receipt');
  await expect(receipt.getByRole('heading', { name: /Comprobante N.º \d+/ })).toBeVisible();
  await expect(receipt).toContainText('Cliente de prueba E2E');
  await expect(receipt).toContainText('$100,000.00');
  await expect(receipt).toContainText('IVA (19%)');
  await expect(receipt).toContainText('$19,000.00');
  await expect(receipt).toContainText('Total');
  await expect(receipt).toContainText('$119,000.00');
  await expect(page.getByRole('status')).toContainText('El registro se creó exitosamente.');

  mkdirSync(dirname(screenshotPath), { recursive: true });
  await page.screenshot({ path: screenshotPath, fullPage: true });

  await page.getByRole('link', { name: 'Caja' }).click();
  await page.getByRole('button', { name: 'Cerrar caja' }).click();
  await expect(page.getByText('Registre la base de efectivo antes de procesar transacciones.')).toBeVisible();
  await page.getByRole('link', { name: 'Pagos' }).click();
  await expect(page.getByText('Debe abrir una caja antes de registrar pagos.')).toBeVisible();
});
