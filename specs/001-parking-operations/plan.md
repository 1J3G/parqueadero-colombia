# Implementation Plan: Gestión de operaciones del parqueadero

**Branch**: `001-parking-operations` | **Date**: 2026-10-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification for Sistema de Parqueadero "Autos Colombia".

## Summary

Implementar el flujo de operaciones definido en los 27 requisitos mediante Angular Standalone, una API Python con FastAPI y MySQL local. La estructura se limita a `/frontend`, `/backend` y `/db`; la persistencia relacional y las transacciones de ingreso, salida y pago mantienen las reglas de integridad del dominio. La tarifa neta se recibe al registrar el pago y no se administra un catálogo de tarifas.

## Technical Context

**Language/Version**: TypeScript para Angular; Python para FastAPI. Las versiones no están fijadas por la constitución.

**Primary Dependencies**: Angular Standalone; FastAPI y Pydantic; `mysql-connector-python` como acceso MySQL directo, sin ORM ni capa arquitectónica adicional.

**Storage**: MySQL local; esquema relacional y scripts SQL bajo `/db`.

**Testing**: Validación de aceptación de API, interfaz y persistencia con datos de prueba aislados. El plan no desglosa tareas de pruebas automatizadas porque no fueron solicitadas explícitamente.

**Target Platform**: Aplicación web SPA en navegador y backend Python conectado a la instancia MySQL local.

**Project Type**: Aplicación web Angular + API FastAPI.

**Performance Goals**: La especificación no fija latencias, concurrencia ni disponibilidad; no se inventan objetivos numéricos.

**Constraints**: Reglas RN-01 a RN-18 y REQ-001 a REQ-027; estructura plana `/frontend`, `/backend`, `/db`; consultas MySQL parametrizadas; no incorporar funcionalidades no especificadas.

**Scale/Scope**: Operación de parqueadero con operarios, administradores, clientes, contratos, vehículos, celdas, tránsitos, novedades, cajas, pagos, comprobantes y auditoría. No hay volumen de datos especificado.

## Constitution Check

| Principio / regla | Resultado | Aplicación en el plan |
|---|---|---|
| Reglas de dominio como fuente de verdad y cero código sombra | PASS | Cada paso está enlazado a REQ; no se agregan reportes, inventario, descuentos ni administración de tarifas. |
| Simplicidad, estructura plana y estilo funcional | PASS | Solo `/frontend`, `/backend` y `/db`; funciones y módulos por dominio, sin Clean Architecture ni ORM. |
| Validación, acceso y errores | PASS | Sesión activa, rol Administrador y caja abierta se validan antes de operaciones; mensajes de usuario y estados HTTP semánticos. |
| Desarrollo guiado por especificación | PASS | Los pasos y tareas implementan requisitos existentes y las aclaraciones registradas en `spec.md`. |
| Dominio RN-01 a RN-18 | PASS | Unicidad, estados, acceso excepcional, Anti-Passback, inmutabilidad, celdas, caja, comprobantes y anulaciones quedan cubiertos. |
| Stack objetivo | PASS | Angular Standalone, Python/FastAPI y MySQL local. FastAPI fue confirmado por el usuario; versiones no especificadas permanecen sin fijar. |

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

- **Requirements**: REQ-004, REQ-005, REQ-006, REQ-011, REQ-014, REQ-015, REQ-019, REQ-023, REQ-025, REQ-027
- **Design inputs**: Especificación, Key Entities y reglas RN-01 a RN-18.
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

#### Step 2.3: Abrir caja y proteger transacciones del operario

- **Requirements**: REQ-003, REQ-019
- **Design inputs**: Especificación, REQ-003; Constitución RN-13.
- **Description**: Permitir registrar una apertura con base de efectivo y operario responsable; aplicar la condición de caja abierta a nombre del operario antes de aceptar sus transacciones. La apertura debe estar disponible antes de que el operario inicie los flujos de tránsito y recaudo.

#### Step 2.4: Integrar inicio de sesión en la interfaz

- **Requirements**: REQ-001, REQ-002
- **Design inputs**: Especificación, User Story 1.
- **Description**: Permitir el inicio de sesión con documento y contraseña, conservar el estado de sesión que exponga el backend y restringir la navegación a las operaciones autenticadas.

### Phase 3: User Story 2 — Clientes, vehículos y contratos (P1)

#### Step 3.1: Registrar clientes y vehículos únicos

- **Requirements**: REQ-004, REQ-005, REQ-026
- **Design inputs**: Especificación, User Story 2 y REQ-004, REQ-005, REQ-026; Constitución RN-01.
- **Description**: Aceptar documentos CC, CE o NIT sin duplicados y validar la placa según el formato colombiano indicado para carro o moto. Asociar un único vehículo a cada contrato.

#### Step 3.2: Gestionar contratos y su ciclo de vida

- **Requirements**: REQ-006, REQ-020
- **Design inputs**: Especificación, REQ-006 y aclaraciones de renovación en `Clarifications`; Constitución RN-02 y RN-12.
- **Description**: Crear contratos Pendiente de Pago, mantener exclusivamente los cuatro estados documentados, impedir reactivar un contrato Cancelado y calcular la nueva vigencia desde el vencimiento vigente o la fecha de pago según corresponda.

#### Step 3.3: Autorizar cambios de placa

- **Requirements**: REQ-007
- **Design inputs**: Especificación, REQ-007; Constitución RN-18.
- **Description**: Permitir el cambio de placa únicamente tras comprobar rol Administrador. El resto de roles recibe una denegación explícita.

### Phase 4: User Story 3 — Celdas, entradas, salidas y novedades (P1)

#### Step 4.1: Consultar disponibilidad y validar compatibilidad

- **Requirements**: REQ-002, REQ-015, REQ-016
- **Design inputs**: Especificación, REQ-002, REQ-015 y REQ-016; Constitución RN-09.
- **Description**: Exponer disponibilidad a usuarios autenticados y seleccionar solo celdas disponibles cuya categoría sea compatible: Carro↔Carro/Discapacitado, Moto↔Moto y Camioneta↔Camioneta.

#### Step 4.2: Aplicar reglas de ingreso, excepción y Anti-Passback

- **Requirements**: REQ-008, REQ-009, REQ-010
- **Design inputs**: Especificación, REQ-008 a REQ-010 y aclaración sobre Cancelado; Constitución RN-03, RN-05 y RN-06.
- **Description**: Rechazar el ingreso si el contrato no satisface estado y fecha de vigencia, salvo autorización explícita de Administrador más novedad para los estados Vencido, Pendiente de Pago o Cancelado. Rechazar entradas duplicadas y salidas sin vehículo dentro.

#### Step 4.3: Persistir tránsitos y ocupación de celdas

- **Requirements**: REQ-011, REQ-012, REQ-017, REQ-018
- **Design inputs**: Especificación, REQ-011, REQ-012, REQ-017 y REQ-018; Constitución RN-07, RN-10 y RN-11.
- **Description**: Confirmar entrada, asignar celda y registrar tránsito de manera atómica. Registrar salida inmutable y liberar de inmediato la celda. Ninguna operación de edición o eliminación debe estar expuesta.

#### Step 4.4: Registrar daños y accesos excepcionales

- **Requirements**: REQ-010, REQ-013, REQ-014
- **Design inputs**: Especificación, REQ-010, REQ-013 y REQ-014; Constitución RN-06 y RN-08.
- **Description**: Capturar golpes, rayones y fallas con severidad Leve, Moderada o Grave y asociación inmutable a la entrada. Guardar también la novedad requerida para cada acceso excepcional autorizado.

### Phase 5: User Story 4 — Caja, pagos, comprobantes y anulaciones (P1)

#### Step 5.1: Asociar los pagos al turno de caja

- **Requirements**: REQ-003, REQ-027
- **Design inputs**: Especificación, REQ-003 y REQ-027; Constitución RN-13.
- **Description**: Asociar cada pago al operario que abrió la caja vigente y hacer cumplir el control de caja ya establecido para todas las transacciones del operario.

#### Step 5.2: Registrar pagos y renovar contratos

- **Requirements**: REQ-020, REQ-021, REQ-022
- **Design inputs**: Especificación, REQ-020 a REQ-022 y aclaraciones de renovación; Constitución RN-12 y RN-15.
- **Description**: Registrar los tres métodos permitidos, exigir referencia para transferencia y, al confirmar un pago válido, activar/extender el contrato de acuerdo con la fecha base definida.

#### Step 5.3: Emitir comprobante fiscal

- **Requirements**: REQ-023
- **Design inputs**: Especificación, REQ-023 y aclaración de tarifa externa; Constitución RN-14.
- **Description**: Emitir un comprobante numerado consecutivamente con tarifa neta proporcionada durante el pago, IVA del 19% y datos del cliente. No mantener tarifas en el sistema.

#### Step 5.4: Anular pagos con autorización y auditoría

- **Requirements**: REQ-024, REQ-025
- **Design inputs**: Especificación, REQ-024 y REQ-025; Constitución RN-16.
- **Description**: Denegar borrado/anulación por operarios. Para Administrador, solicitar credenciales de confirmación y justificación, conservar el pago y registrar la anulación en auditoría.

## Project Structure

```text
frontend/
└── src/app/
    ├── core/                  # Servicios de sesión y protección de navegación
    └── features/
        ├── auth/              # Inicio de sesión
        ├── cash/              # Apertura de caja
        ├── contracts/         # Clientes, vehículos y mensualidades
        ├── parking/           # Disponibilidad, entradas, salidas y novedades
        └── payments/          # Caja, pagos, comprobantes y anulaciones

backend/
└── app/
    ├── main.py                # Aplicación FastAPI y montaje de rutas
    ├── database.py            # Conexión/transacciones MySQL
    ├── auth.py                # Sesión y permisos
    ├── routes/                # Rutas por dominio
    ├── contracts.py           # Reglas contractuales
    ├── vehicles.py            # Validaciones de vehículo/placa
    ├── cells.py               # Disponibilidad y compatibilidad
    ├── transits.py            # Entrada/salida e inmutabilidad
    ├── novelties.py           # Novedades físicas y excepcionales
    ├── cash.py                # Aperturas y turno del operario
    ├── payments.py            # Pagos y anulaciones
    └── receipts.py            # Comprobantes fiscales

db/
└── schema.sql                 # Esquema y restricciones relacionales
```

**Structure Decision**: Se conserva la división plana definida por la constitución. Los módulos y rutas están agrupados por dominio, sin incorporar un cuarto proyecto ni capas de arquitectura no aprobadas.

## Testing Strategy

- **appType**: SPA Angular con API FastAPI y MySQL local.
- **Critical user journeys**:
  1. Iniciar sesión y rechazar operaciones con sesión inactiva.
  2. Registrar cliente, vehículo y contrato con validación de documento/placa y cambio de placa reservado al Administrador.
  3. Consultar celdas y registrar entradas/salidas válidas, rechazando incompatibilidad, vigencia incorrecta y Anti-Passback.
  4. Registrar novedad física y acceso excepcional autorizado, dejando los tránsitos inmutables.
  5. Abrir caja, pagar mensualidad, emitir comprobante y restringir anulaciones a Administrador.
- **primaryValidationStack**: Validación de rutas y flujos de Angular/FastAPI contra MySQL local.
- **fallbackMatrix**: `infra-tier`: MySQL local requerido; si no está disponible, las pruebas de persistencia no pueden considerarse aprobadas. `browser-tier`: navegador manual para aceptación visual; no se agrega automatización de navegador en este plan.
- **Environment requirements**: Python compatible con FastAPI, Node.js compatible con Angular y MySQL local.
- **knownGaps**: No se definieron objetivos de carga/disponibilidad ni volumen; la validación no cubrirá esos ejes. Sin automatización de navegador, la aceptación visual es manual.
- **Test data strategy**: Usar registros de prueba separados por ejecución y documentos/placas no compartidos; limpiar solo datos de prueba, nunca registros de auditoría de producción.
- **Acceptance criteria**: Cada viaje crítico satisface sus escenarios Given-When-Then en la especificación; las operaciones inválidas son rechazadas y no dejan cambios parciales.
- **Validation review expectations**: Confirmar la correspondencia de cada requisito con implementación observable y verificar las restricciones de inmutabilidad, atomicidad, permisos y trazabilidad.

## Requirement Mapping

| REQ ID | Description | Plan Items | Implementation Evidence |
|--------|-------------|------------|------------------------|
| REQ-001 | Autenticar por documento y contraseña | 1.1, 2.1, 2.4 | `backend/app/auth.py`, `backend/app/routes/auth.py`, `frontend/src/app/features/auth/login.component.ts` |
| REQ-002 | Exigir sesión activa para disponibilidad y operaciones | 1.1, 2.2, 2.4, 4.1 | `backend/app/auth.py`, `backend/app/routes/cells.py`, `frontend/src/app/core/auth.guard.ts` |
| REQ-003 | Operario transacciona solo con caja abierta propia | 2.3, 5.1 | `backend/app/cash.py`, `backend/app/routes/cash.py` |
| REQ-004 | Unicidad de cliente por documento | 1.2, 3.1 | `db/schema.sql`, `backend/app/routes/customers.py` |
| REQ-005 | Un contrato vincula un vehículo por placa | 1.2, 3.1 | `db/schema.sql`, `backend/app/vehicles.py` |
| REQ-006 | Estados válidos y estado inicial del contrato | 1.2, 3.2 | `db/schema.sql`, `backend/app/contracts.py` |
| REQ-007 | Cambio de placa autorizado por Administrador | 3.3 | `backend/app/contracts.py`, `backend/app/routes/contracts.py` |
| REQ-008 | Entrada activa y dentro de vigencia | 4.2 | `backend/app/transits.py` |
| REQ-009 | Anti-Passback para entradas y salidas | 4.2 | `backend/app/transits.py` |
| REQ-010 | Acceso excepcional a contratos no vigentes/cancelados | 4.2, 4.4 | `backend/app/transits.py`, `backend/app/novelties.py` |
| REQ-011 | Tránsito con hora servidor, operario y celda | 1.2, 4.3 | `db/schema.sql`, `backend/app/transits.py` |
| REQ-012 | Prohibir edición y eliminación de tránsitos | 4.3 | `backend/app/routes/transits.py` |
| REQ-013 | Documentar daños preexistentes | 4.4 | `backend/app/novelties.py`, `frontend/src/app/features/parking/` |
| REQ-014 | Severidad y vínculo inmutable de novedades físicas | 1.2, 4.4 | `db/schema.sql`, `backend/app/novelties.py` |
| REQ-015 | Categorías fijas de celdas | 1.2, 4.1 | `db/schema.sql`, `backend/app/cells.py` |
| REQ-016 | Compatibilidad estricta vehículo-celda | 4.1 | `backend/app/cells.py` |
| REQ-017 | Ocupar celda atómicamente al confirmar entrada | 4.2, 4.3 | `backend/app/transits.py`, `backend/app/database.py` |
| REQ-018 | Liberar celda inmediatamente al procesar salida | 4.3 | `backend/app/transits.py`, `backend/app/routes/transits.py` |
| REQ-019 | Apertura de caja con base antes del cobro | 1.2, 2.3 | `db/schema.sql`, `backend/app/cash.py`, `frontend/src/app/features/cash/cash-open.component.ts` |
| REQ-020 | Activar contrato y extender vigencia según meses pagados | 3.2, 5.2 | `backend/app/contracts.py`, `backend/app/payments.py` |
| REQ-021 | Registrar método de pago permitido | 5.2 | `backend/app/payments.py` |
| REQ-022 | Exigir referencia en transferencia | 5.2 | `backend/app/payments.py` |
| REQ-023 | Comprobante consecutivo con neto, IVA y cliente | 1.2, 5.3 | `db/schema.sql`, `backend/app/receipts.py` |
| REQ-024 | Impedir anulación/eliminación por operarios | 5.4 | `backend/app/payments.py`, `backend/app/routes/payments.py` |
| REQ-025 | Anulación de Administrador con credenciales y justificación auditada | 1.2, 5.4 | `db/schema.sql`, `backend/app/payments.py` |
| REQ-026 | Validar formatos colombianos de placas | 3.1 | `backend/app/vehicles.py` |
| REQ-027 | Asociar pago al operario de la caja abierta | 1.2, 5.1 | `db/schema.sql`, `backend/app/payments.py` |
