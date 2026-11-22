# Plan de pruebas resumido - Gestión de pagos

**Hoja de cálculo:** [plan de pruebas y evidencia](./plan-pruebas-gestion-pagos.xlsx)
**Imagen-resumen de resultados:** [evidencia de ejecución](./evidencia-pruebas-pagos.png) (generada desde la salida del test runner; no es una captura del navegador).

**Captura real del navegador:** [comprobante fiscal generado por el flujo E2E](./evidencia-e2e-pago.png).

| Campo | Detalle |
|---|---|
| Módulo | Apertura y cierre de caja, pagos y comprobantes |
| Prioridad | P1 |
| Fuente funcional | User Story 4 y requisitos de [spec.md](../specs/001-parking-operations/spec.md) |
| Estado | Ejecución automatizada parcial; resultados y brechas al final del documento |

## Objetivo y alcance

Verificar que un Operario pueda cobrar mensualidades solo con sesión activa y caja abierta; que el pago active o renueve correctamente el contrato y genere un comprobante fiscal; y que solo un Administrador pueda anular pagos con credenciales, justificación y auditoría.

Incluye apertura y cierre de caja, métodos de pago, referencias de transferencias, cálculo de vigencias, emisión de comprobantes, autorización de anulaciones, mensajes de la interfaz e integridad transaccional. Clientes, vehículos, contratos y usuarios se preparan como datos de prueba; su administración no forma parte de este plan.

## Estrategia y entorno

- **API y lógica:** pruebas unitarias con `python -m unittest`; pruebas de rutas con `TestClient` y una base MySQL aislada para verificar persistencia real.
- **Interfaz:** pruebas del proyecto con `npm test` y flujo E2E automatizado en Chromium con Playwright.
- **Datos:** el E2E crea un Operario, cliente, vehículo y contrato con identificadores únicos en la base `_test`; el flujo abre y cierra su propia caja. No usa cuentas personales ni datos de producción.
- **Infraestructura:** el plan general requiere MySQL local para aprobar pruebas de persistencia. Docker no está disponible en el entorno verificado; comprobar que MySQL local esté activo antes de la ejecución.
- **Navegador:** Node.js, Playwright y Chromium están disponibles. `npm run test:e2e` inicia el backend en el puerto 8011 y Angular en 4201 con un proxy dedicado; el fixture rechaza bases cuyo nombre no termine en `_test`.
- **Pruebas existentes:** [test_payments.py](../backend/tests/test_payments.py) cubre tres escenarios de cálculo de vigencia con dependencias simuladas. No se encontró una prueba específica del componente de pagos.
- **Pruebas de integración añadidas:** tres pruebas nuevas usan TestClient y MySQL real para pago en efectivo, transferencia y anulación. Exigen que el nombre de la base termine en `_test`.

### Comandos de referencia

- Backend: desde `backend`, ejecutar `python -m unittest discover -s tests -v`.
- Frontend: desde `frontend`, ejecutar `npm test`.
- E2E de navegador: desde `frontend`, ejecutar `npm run test:e2e`.

## Casos de prueba

| ID | Escenario y pasos resumidos | Resultado esperado | Trazabilidad |
|---|---|---|---|
| PGP-01 | Intentar pagar sin sesión; luego con sesión de Operario pero sin caja abierta. | Ambas solicitudes se rechazan; no se crean pago, comprobante ni cambios de vigencia. | REQ-001, REQ-002, REQ-003, REQ-019, RNF-003 |
| PGP-02 | Abrir caja con base de efectivo y registrar un pago en efectivo con valor neto y meses válidos. | Pago asociado a la caja y al Operario; contrato Activo; comprobante consecutivo con neto, IVA del 19 %, total e identificación del cliente; confirmación visible. | REQ-019, REQ-020, REQ-023, REQ-027, REQ-032 |
| PGP-03 | Registrar pagos válidos por transferencia con referencia y por tarjeta. | Cada método admitido queda registrado; transferencia conserva su referencia. Comprobar consecutivo y montos del comprobante para cada método. | REQ-021, REQ-022, REQ-023 |
| PGP-04 | Intentar una transferencia sin referencia y pagos con valor neto no positivo o meses menores que uno. | Solicitudes rechazadas; no se persisten pagos, recibos ni actualizaciones del contrato; no aparece confirmación de éxito. | REQ-022, REQ-032, RNF-006 |
| PGP-05 | Renovar un contrato Activo y vigente; preparar además contratos Activos con vencimientos distintos para el mismo cliente y vehículo y contratos de otros clientes o vehículos. | La renovación conserva su fecha de inicio y calcula el período usando el vencimiento vigente más lejano del mismo cliente y vehículo; ignora los demás. Verificar límites de fin de mes. | REQ-005, REQ-020 |
| PGP-06 | Pagar un contrato nuevo o Vencido sin otro período vigente; probar también un período futuro y un contrato Cancelado. | Sin vencimiento base, el período empieza en la fecha del pago. Si hay vencimiento base vigente, inicia al día siguiente. Un contrato Cancelado no se reactiva y requiere uno nuevo; la vigencia futura no habilita entradas antes de su inicio. | REQ-006, REQ-008, REQ-020 |
| PGP-07 | Como Operario, intentar anular o eliminar un pago; como Administrador, probar contraseña incorrecta, justificación vacía, anulación válida y repetición de una anulación. | El Operario no puede anular. Fallos de credenciales o justificación no cambian el pago ni crean auditoría. La anulación válida guarda Administrador, fecha y justificación; no puede repetirse. | REQ-024, REQ-025, RNF-003, RNF-007 |
| PGP-08 | Cerrar caja por su titular y por un Administrador; intentar cerrar una caja ajena como Operario y pagar con una caja cerrada. | Solo titular o Administrador pueden cerrar; se registra hora del servidor, no se pide monto final y la caja cerrada no admite pagos. | REQ-003, REQ-028, RNF-003 |
| PGP-09 | Completar un pago correctamente y repetir el flujo provocando un error de API. | La interfaz confirma solo el registro exitoso; ante error muestra el error y no una confirmación de creación. | REQ-032 |
| PGP-10 | Ejecutar pagos concurrentes que programen vigencias para el mismo vehículo y verificar pagos, contratos y comprobantes en la base. | El cálculo de vigencias se serializa y cada operación queda completa o se revierte, sin comprobantes duplicados ni escrituras parciales. La política de idempotencia debe aclararse antes de fijar el resultado para solicitudes duplicadas. | RNF-006 |

## Criterios de aprobación

1. Todos los casos PGP-01 a PGP-09 pasan en la API y en la interfaz donde corresponda; PGP-10 no se marca aprobado hasta definir cómo identificar y tratar una solicitud duplicada.
2. Ninguna solicitud rechazada deja pagos, cambios de contrato, comprobantes o auditorías parciales.
3. Los montos, fechas de vigencia, permisos, referencias y datos de auditoría coinciden con la especificación.
4. Las pruebas de persistencia usan MySQL aislado. Si MySQL no está disponible, esa cobertura se marca **No verificada**, no aprobada.
5. Se conservan como evidencia el comando, código de salida, resumen de pruebas y registros de errores relevantes.

## Riesgos y decisiones pendientes

- **Método de tarjeta:** `spec.md` define “Tarjeta de Crédito/Débito”, mientras que la interfaz y el backend aceptan “Tarjeta Crédito/Débito”. Alinear el contrato antes de cerrar PGP-03.
- **Duplicidad de pagos:** el plan general identifica pendiente la idempotencia de pagos. Definir qué solicitudes concurrentes o repetidas deben considerarse duplicadas antes de aceptar PGP-10.
- **Anulación y vigencia contractual:** la especificación no define si anular un pago revierte o conserva la vigencia del contrato. No se debe afirmar un resultado para ese efecto hasta aclarar el requisito.
- **Playwright:** el flujo cubre pago exitoso, comprobante fiscal y bloqueo de pagos después de cerrar caja. La cobertura de errores de interfaz, métodos de tarjeta y concurrencia sigue pendiente.

## Evidencia de ejecución

**Fecha:** 2026-11-22

| Validación | Comando o comprobación | Resultado |
|---|---|---|
| Integración de pagos contra MySQL | `python -m unittest discover -s tests -p "test_payment_*_integration.py" -v` desde `backend` | PASS, código 0; 3 pruebas: pago efectivo y comprobante persistido, transferencia requerida/registrada y anulación con auditoría/permisos. |
| Suite completa de backend | `python -m unittest discover -s tests -v` desde `backend` | PASS, código 0; 29 pruebas. |
| Compilación Python | `python -m compileall -q app tests` desde `backend` | PASS, código 0. |
| Suite de frontend | `npm test -- --watch=false` desde `frontend` | PASS, código 0; 3 archivos y 6 pruebas. No hay un archivo de pruebas dedicado al componente de pagos. |
| Conexión MySQL de pruebas | Consulta de solo lectura mediante la conexión del backend | PASS; base `autos_colombia_test` y tablas requeridas presentes. |
| Inicio del backend | Uvicorn y consulta a `/openapi.json` en puerto local alternativo | PASS; HTTP 200 y dos rutas de pagos expuestas. |
| Navegador E2E | `npm run test:e2e` desde `frontend` | PASS, código 0; 1 prueba Chromium: login, apertura de caja, registro del pago, comprobante fiscal, cierre de caja y bloqueo posterior. |
| Captura E2E | Captura de pantalla de Playwright | [Comprobante fiscal real](./evidencia-e2e-pago.png), con neto COP 100.000, IVA COP 19.000 y total COP 119.000. |
| Docker | `docker info` | No disponible; no se usó infraestructura Docker. |

### Cobertura de casos

| Caso | Resultado |
|---|---|
| PGP-01 | Parcial: el navegador redirige una sesión no autenticada y bloquea pagos sin caja abierta; no se verificó la ausencia de escrituras en base para esos intentos. |
| PGP-02 | PASS: pago efectivo, asociación a caja/operario, activación contractual y comprobante persistido; flujo visible confirmado en navegador. |
| PGP-03 | Parcial: transferencia válida y referencia persistida; no se probó tarjeta. |
| PGP-04 | Parcial: transferencia sin referencia rechazada sin crear pago; montos inválidos no se verificaron en integración. |
| PGP-05 | Parcial: renovación y vencimiento base verificados en pruebas unitarias; faltan límites de fin de mes en integración. |
| PGP-06 | Parcial: inicio sin período vigente y bloqueo de reactivación de Cancelado cubiertos por pruebas existentes; el flujo de inicio futuro no se verificó aquí. |
| PGP-07 | Parcial: Operario denegado, contraseña incorrecta, anulación válida, auditoría y repetición cubiertos; justificación vacía no se probó en integración. |
| PGP-08 | Parcial: el E2E abre y cierra caja del Operario y confirma que no se puede pagar después; faltan permisos de cierre cruzados y Administrador. |
| PGP-09 | Parcial: E2E confirma pago exitoso y mensaje de creación; falta provocar un error de API desde la interfaz. |
| PGP-10 | No ejecutado; no hay evidencia de concurrencia ni idempotencia. |

**Veredicto:** PASS para las pruebas automatizadas ejecutadas; cobertura total del plan **parcial**. No se afirma que PGP-01 a PGP-10 estén todos aprobados.

**Datos de prueba:** Las pruebas de integración crean registros con identificadores únicos únicamente en `autos_colombia_test`. Los pagos quedan conservados porque el esquema de base de datos prohíbe eliminarlos; por integridad, también se conservan sus registros relacionados.
El E2E también conserva sus datos sintéticos en esa base por la misma restricción. No se guardan las credenciales temporales en el repositorio ni en la evidencia.
