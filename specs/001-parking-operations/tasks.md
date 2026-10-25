# Tasks: Gestión de operaciones del parqueadero

**Input**: Diseño y requisitos de `specs/001-parking-operations/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md)

**Tests**: No se agregan tareas de pruebas automatizadas; la especificación no las solicita. Cada historia incluye criterios de prueba independiente para su aceptación.

**Organization**: Tareas agrupadas por las historias de usuario P1 de `spec.md`; cada tarea con referencia `[Plan:X.Y]` traza al plan de implementación.

## Formato y rutas

- Todas las tareas tienen casilla, identificador secuencial, etiqueta de historia cuando corresponde y ruta concreta.
- `[P]` indica tareas paralelizables sin dependencia de tareas pendientes que modifiquen los mismos archivos.
- Las rutas corresponden a la estructura plana `/frontend`, `/backend`, `/db` definida en la constitución.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar los proyectos Angular Standalone y FastAPI.

- [ ] T001 [P] [Plan:1.1] Crear `backend/requirements.txt` con FastAPI, servidor ASGI y `mysql-connector-python`, sin fijar versiones no especificadas.
- [ ] T002 [P] [Plan:1.1] Crear el proyecto Angular Standalone en `frontend/package.json`, `frontend/angular.json`, `frontend/src/main.ts` y `frontend/src/app/app.config.ts`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Proveer esquema, conexión de persistencia y manejo común de errores que requieren las historias.

- [ ] T003 [P] [Plan:1.2] Crear `db/schema.sql` con las entidades y restricciones requeridas para usuarios, clientes, vehículos, contratos, celdas, tránsitos, novedades, cajas, pagos, comprobantes y bitácora.
- [ ] T004 [P] [Plan:1.2] Crear `backend/app/database.py` para conexión MySQL local, configuración por entorno, consultas parametrizadas y transacciones.
- [ ] T005 [P] [Plan:1.1] Crear `backend/app/main.py` con el montaje de rutas y `backend/app/errors.py` para respuestas semánticas 400, 401, 403 y 409 sin exponer trazas.
- [ ] T006 [P] [Plan:2.2] Crear `frontend/src/app/core/api-error.interceptor.ts` para presentar mensajes comprensibles ante errores de autenticación, autorización, validación y conflicto del backend.

**Checkpoint**: Base de datos, conexión, aplicación API y manejo común de errores preparados; ninguna historia debe omitir las restricciones del esquema.

## Phase 3: User Story 1 — Acceso autenticado, consulta y caja (Priority: P1) 🎯 MVP

**Goal**: Permitir acceso autenticado por documento y contraseña; habilitar operaciones del operario solo después de abrir una caja a su nombre.

**Independent Test**: Iniciar sesión con credenciales válidas e inválidas; comprobar sesión requerida para disponibilidad y operaciones protegidas; intentar transacciones sin caja abierta y después de abrirla.

### Implementation

- [ ] T007 [US1] [Plan:2.1] Implementar búsqueda de usuario por documento, verificación de contraseña y determinación de rol en `backend/app/auth.py`.
- [ ] T008 [US1] [Plan:2.1,2.2] Crear rutas de inicio y cierre de sesión con identidad mínima necesaria en `backend/app/routes/auth.py`.
- [ ] T009 [US1] [Plan:2.2] Implementar la dependencia de sesión activa y aplicarla a disponibilidad, entradas, salidas y pagos en `backend/app/auth.py` y `backend/app/main.py`.
- [ ] T010 [US1] [Plan:2.4] Crear el formulario de inicio de sesión y servicio de sesión Angular en `frontend/src/app/features/auth/login.component.ts` y `frontend/src/app/core/auth.service.ts`.
- [ ] T011 [US1] [Plan:2.4] Proteger rutas de usuario sin sesión y dirigirlas al inicio de sesión en `frontend/src/app/core/auth.guard.ts` y `frontend/src/app/app.routes.ts`.
- [ ] T012 [US1] [Plan:2.3] Implementar apertura de caja con base de efectivo, operario responsable y comprobación de caja abierta para transacciones en `backend/app/cash.py` y `backend/app/routes/cash.py`.
- [ ] T013 [US1] [Plan:2.3] Crear la interfaz para abrir caja y registrar su base de efectivo en `frontend/src/app/features/cash/cash-open.component.ts`.

**Checkpoint**: El usuario puede iniciar sesión; las operaciones protegidas requieren una sesión activa, y el operario debe abrir caja a su nombre para procesar transacciones.

## Phase 4: User Story 2 — Clientes, vehículos y contratos (Priority: P1)

**Goal**: Registrar clientes y contratos vinculados a un vehículo, validar documentos/placas y restringir cambios de placa a Administradores.

**Independent Test**: Crear cliente y contrato, comprobar unicidad y estado inicial, validar placas válidas e inválidas, intentar cambiar la placa con roles Administrador y no Administrador, y comprobar que un contrato Cancelado no se reactiva por pago.

### Implementation

- [ ] T014 [P] [US2] [Plan:3.1] Implementar alta y consulta de clientes con documento CC, CE o NIT único en `backend/app/routes/customers.py`.
- [ ] T015 [P] [US2] [Plan:3.1] Implementar asociación vehículo-contrato y validación de placas ABC123 para carros y ABC12D para motos en `backend/app/vehicles.py` y `backend/app/routes/vehicles.py`.
- [ ] T016 [US2] [Plan:3.2] Implementar creación de contratos con estado inicial Pendiente de Pago y estados permitidos, manteniendo Cancelado como no reactivable, en `backend/app/contracts.py` y `backend/app/routes/contracts.py`.
- [ ] T017 [US2] [Plan:3.3] Restringir la autorización de cambio de placa al rol Administrador en `backend/app/contracts.py` y `backend/app/routes/contracts.py`.
- [ ] T018 [US2] [Plan:3.1,3.2,3.3] Crear las pantallas Angular de clientes, vehículos y contratos con validaciones de documento, placa, estado y acciones autorizadas en `frontend/src/app/features/contracts/`.

**Checkpoint**: Los contratos conservan los cuatro estados documentados y cada uno queda relacionado con un vehículo; solo un Administrador autoriza cambios de placa.

## Phase 5: User Story 3 — Celdas, entradas, salidas y novedades (Priority: P1)

**Goal**: Consultar disponibilidad y registrar tránsitos con celdas compatibles, aplicando vigencia, Anti-Passback, acceso excepcional, inmutabilidad y novedades.

**Independent Test**: Consultar celdas disponibles; probar entrada válida e inválida por vigencia, acceso excepcional y Anti-Passback; comprobar asignación/liberación de celda y vínculo inmutable de daños al tránsito.

### Implementation

- [ ] T019 [US3] [Plan:4.1] Implementar consulta de disponibilidad y compatibilidad Carro↔Carro/Discapacitado, Moto↔Moto y Camioneta↔Camioneta en `backend/app/cells.py` y `backend/app/routes/cells.py`.
- [ ] T020 [US3] [Plan:4.2] Implementar política de entrada según estado y vencimiento contractual, autorización explícita de Administrador para estados Vencido/Pendiente de Pago/Cancelado y Anti-Passback en `backend/app/transits.py`.
- [ ] T021 [US3] [Plan:4.2,4.3] Registrar entrada con fecha/hora del servidor, operario y celda; ocupar la celda compatible de forma atómica y rechazar asignaciones ocupadas en `backend/app/transits.py` y `backend/app/routes/transits.py`.
- [ ] T022 [US3] [Plan:4.3] Registrar salida inmutable con datos del tránsito y liberar inmediatamente la celda asociada en `backend/app/transits.py` y `backend/app/routes/transits.py`.
- [ ] T023 [US3] [Plan:4.4] Persistir novedades de acceso excepcional y daños preexistentes con severidad Leve/Moderada/Grave y vínculo inmutable al tránsito de entrada en `backend/app/novelties.py` y `backend/app/routes/transits.py`.
- [ ] T024 [US3] [Plan:4.1,4.2,4.4] Crear vistas Angular de disponibilidad, entrada y salida con selección de celda compatible y captura de novedades físicas en `frontend/src/app/features/parking/`.

**Checkpoint**: Cada tránsito confirmado respeta sesión, vigencia/excepción, Anti-Passback y compatibilidad; entrada/salida y estado de celda no dejan cambios parciales.

## Phase 6: User Story 4 — Pagos, comprobantes y anulaciones (Priority: P1)

**Goal**: Cobrar mensualidades desde caja abierta, actualizar el contrato, generar comprobantes y permitir anulaciones solo con autorización administrativa auditada.

**Independent Test**: Registrar pagos con cada método, rechazar transferencia sin referencia, comprobar activación y fecha de renovación, revisar comprobante fiscal, y probar anulación de pago como Operario y Administrador.

### Implementation

- [ ] T025 [US4] [Plan:5.1] Asociar cada pago al Operario que abrió la caja vigente y exigir caja abierta en `backend/app/payments.py` y `backend/app/routes/payments.py`.
- [ ] T026 [US4] [Plan:5.2] Implementar métodos Efectivo/Transferencia Bancaria/Tarjeta, referencia obligatoria para transferencia y activación/prórroga del contrato desde la fecha base definida en `backend/app/payments.py`.
- [ ] T027 [US4] [Plan:5.3] Generar comprobante de numeración consecutiva única con valor neto recibido al pago, IVA del 19% y datos del cliente en `backend/app/receipts.py`.
- [ ] T028 [US4] [Plan:5.4] Impedir anulaciones/eliminaciones por Operarios y permitir anulaciones de Administrador con credenciales de confirmación, justificación obligatoria y bitácora en `backend/app/payments.py` y `backend/app/routes/payments.py`.
- [ ] T029 [US4] [Plan:5.1,5.2,5.3] Crear interfaz Angular para cobro con método, referencia de transferencia y presentación del comprobante en `frontend/src/app/features/payments/`.
- [ ] T030 [US4] [Plan:5.4] Crear la acción de anulación exclusiva para Administrador con formulario de credenciales y justificación en `frontend/src/app/features/payments/`.

**Checkpoint**: El pago se asocia a la caja/operario correcto, activa el contrato no Cancelado, emite comprobante y solo se anula con confirmación administrativa auditada.

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: No se añaden tareas de pulido fuera del alcance. Los errores comunes se resuelven en Phase 2 y el resto de trabajo se mantiene dentro de las historias y requisitos especificados.

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: Sin dependencias; T001 y T002 pueden iniciarse en paralelo.
- **Phase 2 — Foundational**: Depende de Phase 1. T003, T004, T005 y T006 trabajan en archivos distintos y pueden paralelizarse.
- **Phase 3 — User Story 1**: Depende de Phase 2; autenticación y apertura de caja habilitan el acceso operativo.
- **Phase 4 — User Story 2**: Depende de Phase 2 y de la sesión/roles de US1 para autorizar el cambio de placa.
- **Phase 5 — User Story 3**: Depende de US1 para sesión activa y de US2 para clientes, vehículos y contratos.
- **Phase 6 — User Story 4**: Depende de US1 para sesión/caja y de US2 para contratos y clientes.
- **Phase 7 — Polish**: No tiene tareas adicionales fuera del alcance definido.

### User Story Dependencies

- **US1 (P1)**: Después de Phase 2; MVP recomendado porque establece sesión y apertura de caja.
- **US2 (P1)**: Después de US1 para permisos de Administrador; puede iniciar tareas de cliente/vehículo en paralelo con trabajo independiente una vez disponibles el esquema y la infraestructura.
- **US3 (P1)**: Después de US1 y US2; necesita sesión autenticada y contratos/vehículos existentes.
- **US4 (P1)**: Después de US1 y US2; necesita caja abierta y contrato/cliente existentes.

### Parallel Opportunities

- **Setup**: T001 y T002.
- **Foundational**: T003, T004, T005 y T006.
- **US2**: T014 y T015.
- **US3**: T019 puede desarrollarse en paralelo con el trabajo inicial de política de entrada T020, siempre que ambos respeten las interfaces de datos compartidas.
- **US4**: T027 y T028 pueden implementarse en paralelo una vez definidos los datos de pago en T026, porque afectan módulos distintos.

## Implementation Strategy

### MVP First

1. Completar Phase 1 y Phase 2 para preparar la SPA, API, persistencia y manejo de errores.
2. Completar US1 y verificar inicio de sesión, sesión activa y caja abierta.
3. Continuar con US2 para disponer de clientes/contratos; luego US3 y US4 conforme a sus dependencias.

### Incremental Delivery

1. Entregar US1 como base de acceso operativo.
2. Añadir US2 para registrar el vínculo cliente-vehículo-contrato.
3. Añadir US3 para operación física de entradas/salidas.
4. Añadir US4 para recaudo, comprobantes y auditoría.

### Scope Guard

- No se incluyen tareas de automatización de pruebas, métricas de rendimiento ni infraestructura no especificada.
- No crear catálogo de tarifas: el importe neto lo proporciona el negocio al cobrar.
- No habilitar edición/eliminación de tránsitos o eliminación de pagos.
