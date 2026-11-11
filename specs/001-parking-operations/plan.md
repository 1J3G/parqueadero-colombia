# Implementation Plan: Gestión de operaciones del parqueadero

**Branch**: `new-funct` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification for Sistema de Parqueadero "Autos Colombia".

## Summary

Implementar los 32 requisitos funcionales definidos mediante Angular Standalone, una API Python con FastAPI y MySQL local. La estructura de la aplicación se limita a `/frontend`, `/backend` y `/db`; las transacciones de ingreso, salida, caja y pago mantienen las reglas de integridad del dominio. Se agregan consulta/mantenimiento de celdas, administración de usuarios, auditoría de cancelaciones y confirmaciones. El cierre de caja registra hora de servidor sin arqueo; la tarifa neta se recibe al registrar el pago. La especificación también declara ocho requisitos no funcionales: varios dependen de infraestructura y validación de operación que aún no están disponibles en el repositorio y quedan explícitamente pendientes.

## Technical Context

**Language/Version**: TypeScript para Angular; Python para FastAPI. Las versiones no están fijadas por la constitución.

**Primary Dependencies**: Angular Standalone; FastAPI y Pydantic; `mysql-connector-python` como acceso MySQL directo, sin ORM ni capa arquitectónica adicional.

**Storage**: MySQL local; esquema relacional y scripts SQL bajo `/db`.

**Testing**: Pruebas unitarias backend y frontend, compilación Angular y validación de aceptación de API, interfaz y persistencia con datos de prueba aislados. Las pruebas MySQL reales, carga, concurrencia de persistencia, recuperación, disponibilidad y usabilidad requieren entornos/evidencia adicionales y no se consideran aprobadas por pasar las pruebas unitarias.

**Target Platform**: Aplicación web SPA en navegador y backend Python conectado a la instancia MySQL local.

**Project Type**: Aplicación web Angular + API FastAPI.

**Performance Goals**: RNF-001 exige que el percentil 95 de consultas de disponibilidad sea menor de 2 segundos con hasta 50 usuarios concurrentes. No hay resultados de carga medidos; el objetivo permanece pendiente de validación.

**Constraints**: Reglas RN-01 a RN-20 y REQ-001 a REQ-032; estructura plana `/frontend`, `/backend`, `/db`; consultas MySQL parametrizadas; no incorporar funcionalidades no especificadas.

**Scale/Scope**: Operación de parqueadero con operarios, administradores, clientes, contratos, vehículos, celdas, tránsitos, novedades, cajas, pagos, comprobantes y auditoría. El único perfil de concurrencia especificado es hasta 50 usuarios para la prueba de disponibilidad; el volumen persistido no está definido.

**Access control**: Las nuevas rutas de administración de usuarios, mantenimiento de celdas y consulta de cancelaciones requieren autorización de Administrador en el servidor, además de la protección de navegación en Angular.

## Constitution Check

| Principio / regla | Resultado | Aplicación en el plan |
|---|---|---|
| Reglas de dominio como fuente de verdad y cero código sombra | PASS | Cada paso está enlazado a REQ; no se agregan reportes, inventario, descuentos ni administración de tarifas. |
| Simplicidad, estructura plana y estilo funcional | PASS | Solo `/frontend`, `/backend` y `/db`; funciones y módulos por dominio, sin Clean Architecture ni ORM. |
| Validación, acceso y errores | PASS | Sesión activa, rol Administrador y caja abierta se validan antes de operaciones; mensajes de usuario y estados HTTP semánticos. |
| Desarrollo guiado por especificación | PASS | Los pasos y tareas implementan requisitos existentes y las aclaraciones registradas en `spec.md`. |
| Dominio RN-01 a RN-20 | PASS | Unicidad, estados, acceso excepcional, Anti-Passback, inmutabilidad, celdas, ciclo de caja, comprobantes, anulaciones y permisos administrativos quedan cubiertos. |
| Stack objetivo | PASS | Angular Standalone, Python/FastAPI y MySQL local. FastAPI fue confirmado por el usuario; versiones no especificadas permanecen sin fijar. |
| RNF-001, RNF-004, RNF-005, RNF-006 y RNF-008 | PENDING | No hay pruebas de carga/concurrencia, infraestructura de disponibilidad, procedimiento de backup/restauración ni medición de usabilidad. RNF-006 tampoco tiene garantía de idempotencia para reintentos de pago; se conserva como brecha, no como logro. |

## Applied Guidelines

- Se revisaron las guías disponibles del repositorio de skills. Las guías detectadas son de migración Java/Spring y no aplican a este proyecto Angular/Python de reescritura.
- Se aplica el estilo funcional y estructura plana exigidos por la constitución; las consultas de escritura deben parametrizarse y las transiciones que cambian tránsito/celda o pago/contrato deben completarse como una unidad de negocio.

## Implementation Steps

### Phase 1: Setup and foundational persistence

#### Step 1.1: Inicializar Angular Standalone y FastAPI

- **Requirements**: REQ-001, REQ-002
- **Design inputs**: Constitución, sección Stack Tecnológico Objetivo; especificación, User Story 1.
- **Description**: Preparar los dos proyectos ejecutables, sus dependencias y puntos de entrada, respetando la estructura plana del repositorio. No se eligen versiones que la constitución no especifica.

#### Step 1.2: Crear persistencia relacional del dominio

- **Requirements**: REQ-004, REQ-005, REQ-006, REQ-011, REQ-014, REQ-015, REQ-019, REQ-023, REQ-025, REQ-027, REQ-028
- **Design inputs**: Especificación, Key Entities y reglas RN-01 a RN-20.
- **Description**: Definir el esquema SQL de usuarios/sesiones, clientes, vehículos, contratos, celdas, tránsitos, novedades, cajas, pagos, comprobantes y auditoría, con claves, restricciones y campos derivados únicamente de los requisitos. Añadir el acceso MySQL directo en el backend, sin ORM.

### Phase 2: User Story 1 — Autenticación y acceso operativo (P1)

#### Step 2.1: Autenticar usuarios por documento y contraseña

- **Requirements**: REQ-001
- **Design inputs**: Especificación, User Story 1 y REQ-001; Constitución RN-17.
- **Description**: Implementar autenticación para los roles Operario y Administrador. Almacenar/verificar credenciales de forma segura y devolver únicamente la identidad y rol necesarios.

#### Step 2.2: Exigir sesión activa en las operaciones protegidas

- **Requirements**: REQ-002
- **Design inputs**: Especificación, REQ-002; Constitución RN-17.
- **Description**: Establecer el control común de sesión activa para disponibilidad, entradas, salidas y pagos. Las solicitudes no autenticadas se rechazan con 401.

#### Step 2.3: Abrir y cerrar caja para proteger transacciones

- **Requirements**: REQ-003, REQ-019, REQ-028
- **Design inputs**: Especificación, REQ-003, REQ-019 y REQ-028; Constitución RN-13.
- **Description**: Registrar aperturas con base de efectivo y operario responsable; impedir transacciones del operario sin caja abierta; permitir que el titular o un Administrador cierre una caja abierta registrando la hora del servidor, sin monto final. Tras cerrar, el titular podrá abrir otra caja.

#### Step 2.4: Integrar inicio de sesión en la interfaz

- **Requirements**: REQ-001, REQ-002
- **Design inputs**: Especificación, User Story 1.
- **Description**: Permitir el inicio de sesión con documento y contraseña, conservar el estado de sesión que exponga el backend y restringir la navegación a las operaciones autenticadas.

### Phase 3: User Story 2 — Clientes, vehículos y contratos (P1)

#### Step 3.1: Registrar clientes, vehículos y contratos

- **Requirements**: REQ-004, REQ-005, REQ-026
- **Design inputs**: Especificación, User Story 2 y REQ-004, REQ-005, REQ-026; Constitución RN-01.
- **Description**: Aceptar documentos CC, CE o NIT sin duplicados y validar la placa según el formato colombiano indicado para carro o moto. Cada contrato referencia exactamente un vehículo; un vehículo puede estar asociado a varios contratos.
- **Data cardinality**: Un contrato referencia exactamente un vehículo; un vehículo puede estar asociado a varios contratos. No existe una regla que impida contratos vigentes concurrentes para el mismo vehículo.

#### Step 3.2: Gestionar contratos y su ciclo de vida

- **Requirements**: REQ-006, REQ-020
- **Design inputs**: Especificación, REQ-006 y aclaraciones de renovación en `Clarifications`; Constitución RN-02 y RN-12.
- **Description**: Crear contratos Pendiente de Pago, mantener exclusivamente los cuatro estados documentados, persistir Vencido al detectar vencimiento, restringir cancelación a Administradores con justificación obligatoria, impedir reactivar un contrato Cancelado y persistir `starts_on`/`expires_on` para períodos secuenciales por cliente y vehículo. Añadir una migración aditiva para las bases existentes.

#### Step 3.3: Autorizar cambios de placa

- **Requirements**: REQ-007
- **Design inputs**: Especificación, REQ-007; Constitución RN-18.
- **Description**: Permitir el cambio de placa únicamente tras comprobar rol Administrador. El resto de roles recibe una denegación explícita.

### Phase 4: User Story 3 — Celdas, entradas, salidas y novedades (P1)

#### Step 4.1: Consultar disponibilidad, estado del vehículo y compatibilidad

- **Requirements**: REQ-002, REQ-009, REQ-015, REQ-016
- **Design inputs**: Especificación, REQ-002, REQ-009, REQ-015 y REQ-016; Constitución RN-05 y RN-09.
- **Description**: Exponer el estado de las celdas y el estado dentro/fuera de cada vehículo a usuarios autenticados; seleccionar únicamente celdas Libre compatibles y no ofrecer asignación cuando la placa ya tenga una entrada sin salida.

#### Step 4.2: Aplicar reglas de vigencia, ingreso, excepción y Anti-Passback

- **Requirements**: REQ-008, REQ-009, REQ-010, REQ-020
- **Design inputs**: Especificación, REQ-008 a REQ-010 y REQ-020, aclaración sobre Cancelado; Constitución RN-03, RN-05, RN-06 y RN-12.
- **Description**: Rechazar el ingreso si el contrato no satisface estado y fechas de inicio/vencimiento, salvo autorización explícita de Administrador más novedad para los estados Vencido, Pendiente de Pago o Cancelado. Bloquear en interfaz y API una segunda entrada para el mismo vehículo/placa aunque se use otro contrato, y rechazar salidas sin vehículo dentro.

#### Step 4.3: Persistir tránsitos y ocupación de celdas

- **Requirements**: REQ-009, REQ-011, REQ-012, REQ-017, REQ-018, RNF-006
- **Design inputs**: Especificación, REQ-011, REQ-012, REQ-017 y REQ-018; Constitución RN-07, RN-10 y RN-11.
- **Description**: Confirmar entrada, asignar celda y registrar tránsito de manera atómica, cambiando la celda de Libre a Ocupado. Registrar salida inmutable y liberar de inmediato la celda como Libre. Ninguna operación de edición o eliminación debe estar expuesta.
- **Concurrency**: Entrada y salida bloquean la fila del vehículo y consumen sus resultados de bloqueo antes de consultas posteriores; esto serializa las transiciones por placa y evita errores de resultado pendiente del conector.

#### Step 4.4: Registrar daños y accesos excepcionales

- **Requirements**: REQ-010, REQ-013, REQ-014
- **Design inputs**: Especificación, REQ-010, REQ-013 y REQ-014; Constitución RN-06 y RN-08.
- **Description**: Capturar golpes, rayones y fallas con severidad Leve, Moderada o Grave y asociación inmutable a la entrada. Guardar también la novedad requerida para cada acceso excepcional autorizado.

### Phase 5: User Story 4 — Caja, pagos, comprobantes y anulaciones (P1)

#### Step 5.1: Asociar los pagos al turno de caja

- **Requirements**: REQ-003, REQ-027, REQ-028
- **Design inputs**: Especificación, REQ-003, REQ-027 y REQ-028; Constitución RN-13.
- **Description**: Asociar cada pago al operario que abrió la caja vigente y hacer cumplir el control de caja ya establecido para todas las transacciones del operario; los pagos no pueden usar una caja cerrada.

#### Step 5.2: Registrar pagos y renovar contratos

- **Requirements**: REQ-020, REQ-021, REQ-022
- **Design inputs**: Especificación, REQ-020 a REQ-022 y aclaraciones de renovación; Constitución RN-12 y RN-15.
- **Description**: Registrar los tres métodos permitidos, exigir referencia para transferencia y, al confirmar un pago válido, bloquear el vehículo, obtener el vencimiento Activo más lejano del mismo cliente/vehículo y crear o extender un período no solapado. Mostrar ambas fechas y rechazar entradas antes del inicio.

#### Step 5.3: Emitir comprobante fiscal

- **Requirements**: REQ-023
- **Design inputs**: Especificación, REQ-023 y aclaración de tarifa externa; Constitución RN-14.
- **Description**: Emitir un comprobante numerado consecutivamente con tarifa neta proporcionada durante el pago, IVA del 19% y datos del cliente. No mantener tarifas en el sistema.

#### Step 5.4: Anular pagos con autorización y auditoría

- **Requirements**: REQ-024, REQ-025
- **Design inputs**: Especificación, REQ-024 y REQ-025; Constitución RN-16.
- **Description**: Denegar borrado/anulación por operarios. Para Administrador, solicitar credenciales de confirmación y justificación, conservar el pago y registrar la anulación en auditoría.

### Phase 6: User Stories 5–8 — Celdas, usuarios, auditoría y confirmaciones

#### Step 6.1: Consultar ocupación y administrar mantenimiento de celdas

- **Requirements**: REQ-029
- **Design inputs**: Estados de celda y permisos de Administrador acordados en `spec.md`.
- **Description**: Mostrar estados Libre, Ocupado y En mantenimiento junto con la placa del vehículo estacionado. Solo Administradores pueden cambiar mantenimiento de celdas no ocupadas; las entradas/salidas realizan las transiciones de ocupación.

#### Step 6.2: Crear y consultar cuentas de usuario

- **Requirements**: REQ-030
- **Design inputs**: `spec.md`, historias de usuario 6 y RNF-002/RNF-003.
- **Description**: Proveer consulta y alta de cuentas protegidas por rol Administrador. Guardar la contraseña inicial usando el hash de contraseñas existente y no incluir credenciales en las respuestas.

#### Step 6.3: Consultar auditoría de cancelaciones

- **Requirements**: REQ-031
- **Design inputs**: Campos de cancelación ya persistidos en `contracts` y criterios de aceptación de la historia 7.
- **Description**: Exponer una lista ordenada de cancelaciones con contrato, cliente, placa, Administrador, fecha y justificación; proteger el endpoint con autorización de servidor.

#### Step 6.4: Confirmar operaciones de creación

- **Requirements**: REQ-032
- **Design inputs**: Criterios de aceptación de la historia 8.
- **Description**: Mostrar un mensaje global de éxito ante una respuesta de creación HTTP 201 y no mostrarlo ante respuestas fallidas.

## Project Structure

```text
frontend/
└── src/app/
    ├── core/                  # Servicios de sesión y protección de navegación
    └── features/
        ├── auth/              # Inicio de sesión
        ├── cash/              # Apertura de caja
        ├── cells/             # Consulta de estados y mantenimiento
        ├── contracts/         # Clientes, vehículos, mensualidades y auditoría
        ├── parking/           # Disponibilidad, entradas, salidas y novedades
        ├── payments/          # Caja, pagos, comprobantes y anulaciones
        └── users/             # Administración de cuentas

backend/
└── app/
    ├── main.py                # Aplicación FastAPI y montaje de rutas
    ├── database.py            # Conexión/transacciones MySQL
    ├── auth.py                # Sesión y permisos
    ├── routes/                # Rutas por dominio
    │   └── users.py           # Administración de usuarios
    ├── contracts.py           # Reglas contractuales
    ├── vehicles.py            # Validaciones de vehículo/placa
    ├── cells.py               # Disponibilidad y compatibilidad
    ├── transits.py            # Entrada/salida e inmutabilidad
    ├── novelties.py           # Novedades físicas y excepcionales
    ├── cash.py                # Aperturas y turno del operario
    ├── payments.py            # Pagos y anulaciones
    └── receipts.py            # Comprobantes fiscales

db/
├── schema.sql                 # Esquema y restricciones relacionales
└── migrations/                # Cambios del esquema para bases existentes
```

**Structure Decision**: Se conserva la división plana definida por la constitución. Los módulos y rutas están agrupados por dominio, sin incorporar un cuarto proyecto ni capas de arquitectura no aprobadas.

## Testing Strategy

- **appType**: SPA Angular con API FastAPI y MySQL local.
- **Critical user journeys**:
  1. Iniciar sesión y rechazar operaciones con sesión inactiva; abrir y cerrar caja y comprobar que el cierre habilita una nueva apertura.
  2. Registrar cliente, vehículo y contrato con validación de documento/placa y cambio de placa reservado al Administrador.
  3. Consultar celdas y registrar entradas/salidas válidas, rechazando incompatibilidad, vigencia incorrecta y Anti-Passback.
  4. Registrar novedad física y acceso excepcional autorizado, dejando los tránsitos inmutables.
  5. Abrir caja, pagar mensualidad, emitir comprobante y restringir anulaciones a Administrador.
  6. Consultar estados de celdas, impedir mantenimiento en ocupadas y reservar la gestión al Administrador.
  7. Crear usuarios como Administrador y comprobar que las credenciales no se exponen.
  8. Consultar cancelaciones como Administrador y comprobar la denegación para Operario.
  9. Verificar mensajes de éxito para creaciones y ausencia del mensaje ante errores.
  10. Mantener un vehículo dentro, seleccionar su contrato (o un contrato asociado a la misma placa) y comprobar que la UI no ofrece otra celda y que la API rechaza una entrada repetida.
  11. Registrar la salida, confirmar que la celda anterior queda Libre y reingresar con el contrato Activo vigente en otra celda compatible.
- **primaryValidationStack**: Validación de rutas y flujos de Angular/FastAPI contra MySQL local.
- **fallbackMatrix**: `infra-tier`: MySQL local requerido; si no está disponible, las pruebas de persistencia no pueden considerarse aprobadas. `browser-tier`: navegador manual para aceptación visual; no se agrega automatización de navegador en este plan.
- **Environment requirements**: Python compatible con FastAPI, Node.js compatible con Angular y MySQL local.
- **knownGaps**: Los objetivos están definidos, pero la infraestructura y la evidencia de carga/disponibilidad no están disponibles en esta validación. La aceptación visual final es manual.
- **Test data strategy**: Usar registros de prueba separados por ejecución y documentos/placas no compartidos; limpiar solo datos de prueba, nunca registros de auditoría de producción.
- **Acceptance criteria**: Cada viaje crítico satisface sus escenarios Given-When-Then en la especificación; las operaciones inválidas son rechazadas y no dejan cambios parciales.
- **Validation review expectations**: Confirmar la correspondencia de cada requisito con implementación observable y verificar las restricciones de inmutabilidad, atomicidad, permisos y trazabilidad.
- **Current validation evidence (2026-10-31)**: 23 pruebas backend, 5 pruebas frontend, `compileall`, build Angular, validación YAML y `git diff --check` pasan. No se ejecutaron pruebas concurrentes ni integración autenticada con MySQL; no hay evidencia para RNF-001, RNF-004, RNF-005 ni RNF-008. RNF-006 requiere además decisión/implementación de idempotencia de pagos.

## Requirement Mapping

| REQ ID | Description | Plan Items | Implementation Evidence |
|--------|-------------|------------|------------------------|
| REQ-001 | Autenticar por documento y contraseña | 1.1, 2.1, 2.4 | `backend/app/auth.py`, `backend/app/routes/auth.py`, `frontend/src/app/features/auth/login.component.ts` |
| REQ-002 | Exigir sesión activa para disponibilidad y operaciones | 1.1, 2.2, 2.4, 4.1 | `backend/app/auth.py`, `backend/app/routes/cells.py`, `frontend/src/app/core/auth.guard.ts` |
| REQ-003 | Operario transacciona solo con caja abierta propia | 2.3, 5.1 | `backend/app/cash.py`, `backend/app/routes/cash.py` |
| REQ-004 | Unicidad de cliente por documento | 1.2, 3.1 | `db/schema.sql`, `backend/app/routes/customers.py` |
| REQ-005 | Un contrato vincula un vehículo por placa | 1.2, 3.1 | `db/schema.sql`, `backend/app/vehicles.py` |
| REQ-006 | Estados válidos, vencimiento automático y cancelación administrativa justificada | 1.2, 3.2 | `db/schema.sql`, `db/migrations/001_contract_status_lifecycle.sql`, `backend/app/contracts.py`, `backend/app/routes/contracts.py`, `frontend/src/app/features/contracts/` |
| REQ-007 | Cambio de placa autorizado por Administrador | 3.3 | `backend/app/contracts.py`, `backend/app/routes/contracts.py` |
| REQ-008 | Entrada activa dentro de las fechas de inicio y vencimiento | 4.2 | `backend/app/domain.py`, `backend/app/routes/transits.py`, `frontend/src/app/features/parking/` |
| REQ-009 | Anti-Passback por placa; bloquear mientras está dentro y permitir reingreso después de salida | 4.1, 4.2, 4.3 | `backend/app/routes/contracts.py`, `backend/app/routes/transits.py`, `frontend/src/app/features/parking/` |
| REQ-010 | Acceso excepcional a contratos no vigentes/cancelados | 4.2, 4.4 | `backend/app/domain.py`, `backend/app/routes/transits.py`, `backend/app/novelties.py` |
| REQ-011 | Tránsito con hora servidor, operario y celda | 1.2, 4.3 | `db/schema.sql`, `backend/app/routes/transits.py` |
| REQ-012 | Prohibir edición y eliminación de tránsitos | 4.3 | `backend/app/routes/transits.py` |
| REQ-013 | Documentar daños preexistentes | 4.4 | `backend/app/novelties.py`, `frontend/src/app/features/parking/` |
| REQ-014 | Severidad y vínculo inmutable de novedades físicas | 1.2, 4.4 | `db/schema.sql`, `backend/app/novelties.py` |
| REQ-015 | Categorías fijas de celdas | 1.2, 4.1 | `db/schema.sql`, `backend/app/cells.py` |
| REQ-016 | Compatibilidad estricta vehículo-celda | 4.1 | `backend/app/cells.py` |
| REQ-017 | Ocupar celda atómicamente al confirmar entrada | 4.2, 4.3 | `backend/app/routes/transits.py`, `backend/app/database.py` |
| REQ-018 | Liberar celda inmediatamente al procesar salida | 4.3 | `backend/app/routes/transits.py` |
| REQ-019 | Apertura de caja con base antes del cobro | 1.2, 2.3 | `db/schema.sql`, `backend/app/cash.py`, `frontend/src/app/features/cash/cash-open.component.ts` |
| REQ-020 | Secuenciar vigencias por cliente y vehículo | 3.2, 4.2, 5.2 | `db/schema.sql`, `db/migrations/003_contract_service_start.sql`, `backend/app/payments.py`, `backend/app/routes/contracts.py`, `backend/app/routes/transits.py`, `frontend/src/app/features/parking/`, `frontend/src/app/features/payments/` |
| REQ-021 | Registrar método de pago permitido | 5.2 | `backend/app/payments.py` |
| REQ-022 | Exigir referencia en transferencia | 5.2 | `backend/app/payments.py` |
| REQ-023 | Comprobante consecutivo con neto, IVA y cliente | 1.2, 5.3 | `db/schema.sql`, `backend/app/receipts.py` |
| REQ-024 | Impedir anulación/eliminación por operarios | 5.4 | `backend/app/payments.py`, `backend/app/routes/payments.py` |
| REQ-025 | Anulación de Administrador con credenciales y justificación auditada | 1.2, 5.4 | `db/schema.sql`, `backend/app/payments.py` |
| REQ-026 | Validar formatos colombianos de placas | 3.1 | `backend/app/vehicles.py` |
| REQ-027 | Asociar pago al operario de la caja abierta | 1.2, 5.1 | `db/schema.sql`, `backend/app/payments.py` |
| REQ-028 | Cerrar caja por titular o Administrador con hora del servidor y sin monto final | 1.2, 2.3, 5.1 | `db/schema.sql`, `backend/app/cash.py`, `backend/app/routes/cash.py`, `frontend/src/app/features/cash/cash-open.component.ts` |
| REQ-029 | Consultar estados de celdas y administrar mantenimiento solo para celdas no ocupadas | 6.1 | `db/schema.sql`, `db/migrations/002_cell_status_maintenance.sql`, `backend/app/routes/cells.py`, `frontend/src/app/features/cells/` |
| REQ-030 | Crear y consultar usuarios solo como Administrador, sin exponer hashes | 6.2 | `backend/app/routes/users.py`, `backend/app/auth.py`, `frontend/src/app/features/users/` |
| REQ-031 | Consultar la auditoría de cancelaciones solo como Administrador | 6.3 | `backend/app/routes/contracts.py`, `frontend/src/app/features/contracts/contract-audit.component.*` |
| REQ-032 | Confirmar visualmente creaciones exitosas | 6.4 | `frontend/src/app/core/api-success.service.ts`, `frontend/src/app/core/api-error.interceptor.ts`, `frontend/src/app/app.html` |

### Non-Functional Requirement Mapping and Status

| Requirement | Plan items | Evidence/status |
|---|---|---|
| RNF-001 — P95 < 2 s at up to 50 concurrent users | 7.1 | Pending measured load test; no performance result is claimed. |
| RNF-002 — Password hashing | 2.1, 6.2 | Implemented with the existing password-hashing helper; covered by backend tests. |
| RNF-003 — Server-side authorization | 2.2, 6.2, 6.3 | Implemented with authenticated dependencies and Administrator checks on API routes. |
| RNF-004 — Monthly availability >= 99.5% | 7.2 | Pending deployment/monitoring target and operational evidence. |
| RNF-005 — Daily backups and restore <= 4 hours | 7.2 | Pending backup/restore procedure and rehearsal; no backup job is included. |
| RNF-006 — Atomicity and duplicate prevention | 4.3, 5.1, 7.1 | Transactions and vehicle locks cover transit transitions; MySQL concurrency verification and payment idempotency remain pending. |
| RNF-007 — Auditable, immutable sensitive events | 4.4, 3.2, 5.4 | Transit/novelty triggers and application audit records exist; authenticated MySQL integration is not yet verified. |
| RNF-008 — Routine movement in <= 3 minutes | 7.3 | Pending timed usability acceptance with an operator. |

### Phase 7: Non-functional Validation and Operational Readiness

#### Step 7.1: Measure performance and transactional concurrency

- **Requirements**: RNF-001, RNF-006
- **Description**: Use an isolated MySQL environment to measure availability-query P95 with 50 concurrent users and exercise concurrent entry/exit/payment requests. Add payment idempotency only after the request identity/retry policy is defined.

#### Step 7.2: Define availability and backup operations

- **Requirements**: RNF-004, RNF-005
- **Description**: Select the deployment/monitoring environment, define availability measurement and scheduled backup, then rehearse restoration within four hours. Infrastructure choices and evidence are not present in the repository.

#### Step 7.3: Validate operational usability

- **Requirements**: RNF-008
- **Description**: Run a timed acceptance with a trained operator for routine entry and exit, document results and address any measured failure.
