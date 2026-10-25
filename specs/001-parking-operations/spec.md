# Especificación: Gestión de operaciones del parqueadero

**Feature Branch**: `001-parking-operations`

**Creada**: 2026-10-24

**Estado**: Draft

**Entrada**: Requisitos funcionales y de negocio para el Sistema de Parqueadero "Autos Colombia".

**Constitución**: Los requisitos siguen las reglas RN-01 a RN-18 de la constitución del proyecto. No se incluyen capacidades no documentadas.

## Clarifications

### Session 2026-10-24

- Q: ¿Qué debe ocurrir cuando un vehículo intenta ingresar con un contrato en estado Cancelado? → A: Permitir una excepción únicamente con autorización de Administrador y registro de novedad, igual que para contratos Vencidos o Pendientes de Pago.
- Q: Cuando se paga o renueva una mensualidad, ¿desde qué fecha deben contarse los meses pagados para calcular el nuevo vencimiento? → A: Si el contrato aún está vigente, desde su vencimiento actual; si ya venció o es nuevo, desde la fecha del pago.
- Q: ¿Puede un pago de mensualidad reactivar un contrato que está Cancelado, o debe crearse un contrato nuevo? → A: No se reactiva; debe crearse un contrato nuevo.
- Q: ¿Cómo debe obtenerse el valor neto de la mensualidad antes de calcular el IVA del comprobante fiscal? → A: El negocio fija la tarifa fuera del sistema y proporciona el valor neto al registrar el pago.
- Q: ¿Cómo debe manejarse el cierre de caja? → A: El titular puede cerrar su caja y un Administrador puede cerrar cualquier caja abierta. Se registra la fecha y hora exactas del servidor, sin arqueo ni monto final.
- Q: ¿Cómo se alcanza el estado Vencido y quién puede cancelar un contrato? → A: Al detectar que la fecha del servidor supera el vencimiento de un contrato Activo, el sistema persiste el estado Vencido. Solo un Administrador puede cancelar un contrato y debe proporcionar una justificación obligatoria.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acceso autenticado y consulta de disponibilidad (Priority: P1)

Un operario o administrador inicia sesión con su documento de identidad y contraseña. Con una sesión activa puede consultar la disponibilidad de celdas; un operario solo puede procesar transacciones cuando tiene una caja abierta a su nombre. El titular de la caja puede cerrarla y un administrador puede cerrar cualquier caja abierta.

**Why this priority**: La autenticación y el ciclo de apertura/cierre de caja controlan el acceso del operario a las operaciones del sistema.

**Independent Test**: Intentar consultar disponibilidad y procesar operaciones con sesión activa e inactiva, y con caja abierta y cerrada para el operario; cerrar una caja y comprobar que deja de habilitar transacciones y permite una nueva apertura.

**Acceptance Scenarios**:

1. **Given** credenciales válidas de un operario o administrador, **When** inicia sesión, **Then** el sistema permite consultar la disponibilidad mientras la sesión permanezca activa.
2. **Given** una sesión inactiva, **When** el usuario intenta consultar disponibilidad, registrar una entrada o salida, o procesar un pago, **Then** el sistema rechaza la operación.
3. **Given** un operario sin caja abierta a su nombre, **When** intenta procesar una transacción, **Then** el sistema la rechaza.
4. **Given** credenciales inválidas, **When** el usuario intenta iniciar sesión, **Then** no obtiene una sesión autenticada.
5. **Given** una caja abierta, **When** su titular la cierra, **Then** se registra la fecha y hora del servidor y la caja deja de habilitar transacciones; el cierre no registra un monto final.
6. **Given** una caja abierta, **When** un Administrador la cierra, **Then** se registra la fecha y hora del servidor y la caja deja de habilitar transacciones.
7. **Given** una caja cerrada, **When** el titular abre una nueva caja con base de efectivo, **Then** la nueva apertura queda disponible para sus transacciones.

### User Story 2 - Administrar clientes, contratos y vehículos (Priority: P1)

Un usuario registra clientes identificados de forma única, vincula cada contrato de mensualidad a un único vehículo y consulta el estado contractual. Solo un administrador puede autorizar cambiar la placa de un contrato existente.

**Why this priority**: Los contratos vinculan el derecho de acceso con un cliente y un vehículo específico.

**Independent Test**: Registrar un cliente, crear un contrato y comprobar unicidad, placa vinculada, estado inicial y permisos de modificación.

**Acceptance Scenarios**:

1. **Given** un cliente con documento CC, CE o NIT no registrado, **When** se registra, **Then** queda identificado por ese documento y no se permite otro registro con el mismo documento.
2. **Given** un contrato nuevo, **When** se crea sin un pago registrado, **Then** queda asociado a un único vehículo por su placa y su estado es Pendiente de Pago.
3. **Given** una placa de carro con formato ABC123 o de moto con formato ABC12D, **When** se asocia al contrato, **Then** el sistema la acepta; **Given** una placa que no cumple el formato correspondiente, **When** se intenta asociar, **Then** el sistema la rechaza.
4. **Given** un contrato existente, **When** un usuario que no es Administrador intenta cambiar su placa, **Then** el sistema deniega el cambio; si la autorización la realiza un Administrador, **Then** el cambio puede ser autorizado.
5. **Given** un contrato, **When** se consulta o actualiza su estado, **Then** solo puede ser Pendiente de Pago, Activo, Vencido o Cancelado.
6. **Given** un contrato Cancelado, **When** el cliente vuelve a contratar una mensualidad, **Then** se debe crear un contrato nuevo y no reactivar el contrato Cancelado.
7. **Given** un contrato Activo cuyo vencimiento ya pasó, **When** el sistema lo detecta durante una consulta u operación, **Then** persiste el estado Vencido; solo un Administrador puede cancelar un contrato y la cancelación requiere una justificación obligatoria.

### User Story 3 - Registrar entradas, salidas y novedades físicas (Priority: P1)

Un operario registra el tránsito de un vehículo, asigna una celda compatible y deja constancia de los daños preexistentes. El sistema impide tránsitos incompatibles con el estado del vehículo o del contrato, salvo acceso excepcional autorizado por un administrador.

**Why this priority**: Controlar la ocupación, el acceso contractual y el historial de tránsitos es el servicio central del parqueadero.

**Independent Test**: Ejecutar entradas y salidas válidas e inválidas con distintos estados de contrato, vehículo, celda y novedad.

**Acceptance Scenarios**:

1. **Given** un vehículo con contrato Activo cuya fecha actual no supera el vencimiento, estado Fuera del Parqueadero y una celda Disponible compatible, **When** el operario confirma la entrada, **Then** se registra el ingreso inmutable y la celda pasa a Ocupada de forma atómica.
2. **Given** un contrato Vencido, Pendiente de Pago o Cancelado, **When** se intenta una entrada sin autorización explícita de un Administrador y sin registrar una novedad de acceso excepcional, **Then** el ingreso se bloquea.
3. **Given** un contrato Cancelado, **When** un Administrador autoriza explícitamente el ingreso y se registra una novedad de acceso excepcional, **Then** el sistema puede permitir la entrada.
4. **Given** un vehículo Dentro del Parqueadero, **When** se intenta otra entrada, **Then** se bloquea por Anti-Passback.
5. **Given** un vehículo Fuera del Parqueadero, **When** se intenta registrar una salida, **Then** se bloquea por Anti-Passback.
6. **Given** un vehículo dentro del parqueadero, **When** se confirma su salida, **Then** el tránsito se registra de forma inmutable y la celda asociada queda Disponible inmediatamente.
7. **Given** una celda ocupada o incompatible, **When** se intenta asignarla a un vehículo, **Then** el sistema no confirma la entrada ni cambia su ocupación.
8. **Given** daños preexistentes detectados durante el ingreso, **When** se confirma la entrada, **Then** cada novedad física queda asociada al tránsito de entrada y clasificada como Leve, Moderada o Grave.
9. **Given** un tránsito registrado, **When** un usuario intenta editarlo o eliminarlo, **Then** el sistema rechaza la operación.

### User Story 4 - Abrir caja, cobrar mensualidades y anular pagos autorizadamente (Priority: P1)

Un operario abre caja con una base de efectivo antes de procesar pagos. El pago activa o renueva el contrato y genera un comprobante fiscal; solo un administrador puede anularlo con credenciales de confirmación y justificación.

**Why this priority**: El recaudo debe habilitar la mensualidad y conservar evidencia fiscal y de auditoría.

**Independent Test**: Probar apertura de caja, pagos de cada método, activación contractual, comprobante y controles de anulación.

**Acceptance Scenarios**:

1. **Given** un operario sin caja abierta, **When** intenta cobrar una mensualidad, **Then** el sistema impide registrar el pago.
2. **Given** una caja abierta a nombre del operario y un contrato nuevo o renovable que no está Cancelado, **When** registra exitosamente un pago, **Then** el contrato pasa inmediatamente a Activo y su fecha de vencimiento se extiende de acuerdo con los meses pagados.
3. **Given** un contrato vigente, **When** se registra exitosamente una renovación, **Then** los meses pagados se cuentan desde su fecha de vencimiento actual.
4. **Given** un contrato vencido o nuevo, **When** se registra exitosamente un pago, **Then** los meses pagados se cuentan desde la fecha del pago.
5. **Given** un pago por transferencia bancaria sin código o número de referencia, **When** se intenta registrarlo, **Then** el sistema lo rechaza.
6. **Given** un pago registrado por Efectivo, Transferencia Bancaria o Tarjeta de Crédito/Débito y el valor neto de tarifa fijado fuera del sistema, **When** se confirma, **Then** queda asociado al operario que abrió la caja vigente y se genera un comprobante fiscal con numeración consecutiva única, ese valor neto, IVA del 19% y datos del cliente.
7. **Given** un pago registrado, **When** un operario intenta anularlo o eliminarlo, **Then** el sistema deniega la operación.
8. **Given** un pago registrado, **When** un Administrador confirma la anulación con sus credenciales y una justificación, **Then** el pago se anula y la justificación queda en la bitácora de auditoría.
9. **Given** un contrato Cancelado, **When** se intenta reactivarlo mediante el pago de una mensualidad, **Then** el sistema exige crear un contrato nuevo en lugar de reactivar el Cancelado.

### Edge Cases

- Un segundo ingreso para un vehículo ya dentro y una salida de un vehículo que está fuera deben rechazarse.
- Un contrato Activo cuya fecha de vencimiento ya pasó no satisface la condición de ingreso, aunque su estado todavía no se haya actualizado a Vencido.
- Si no existe una celda Disponible compatible, la entrada no se confirma y ninguna celda cambia de estado.
- Una transferencia sin referencia obligatoria no puede completar el registro del pago.
- Para contratos Vencidos, Pendientes de Pago o Cancelados, la autorización administrativa de acceso excepcional no reemplaza el registro obligatorio de la novedad de acceso.
- No se permite completar una operación de tránsito si no puede persistirse con la fecha y hora del servidor, el ID del operario y el ID de la celda.

## Requirements *(mandatory)*

### Functional Requirements

- **REQ-001**: El sistema MUST autenticar a operarios y administradores mediante documento de identidad y contraseña.
- **REQ-002**: El sistema MUST exigir sesión activa para consultar disponibilidad de celdas, registrar entradas o salidas y procesar pagos.
- **REQ-003**: El sistema MUST impedir que un operario procese transacciones si no tiene una caja abierta a su nombre.
- **REQ-004**: El sistema MUST identificar de forma única a cada cliente por su documento CC, CE o NIT.
- **REQ-005**: El sistema MUST vincular cada contrato de mensualidad con un único vehículo por su placa.
- **REQ-006**: El sistema MUST aceptar exclusivamente los estados contractuales Pendiente de Pago, Activo, Vencido y Cancelado; asignar Pendiente de Pago por defecto al contrato nuevo sin pago; persistir Vencido cuando detecte que la fecha del servidor supera el vencimiento de un contrato Activo; permitir cancelar contratos únicamente a un Administrador con justificación obligatoria; y exigir un contrato nuevo para sustituir uno Cancelado.
- **REQ-007**: El sistema MUST permitir únicamente a un usuario con rol Administrador autorizar el cambio de placa de un contrato existente.
- **REQ-008**: El sistema MUST permitir la entrada automatizada solo si el contrato está Activo y la fecha actual es menor o igual a su fecha de vencimiento.
- **REQ-009**: El sistema MUST bloquear nuevas entradas para vehículos Dentro del Parqueadero y salidas para vehículos Fuera del Parqueadero.
- **REQ-010**: El sistema MUST bloquear la entrada de vehículos con contrato Vencido, Pendiente de Pago o Cancelado hasta que un Administrador otorgue autorización explícita y se registre una novedad de acceso excepcional.
- **REQ-011**: El sistema MUST persistir cada tránsito con fecha y hora exactas del servidor, ID del operario e ID de la celda asignada.
- **REQ-012**: El sistema MUST impedir la edición y eliminación de registros de tránsito.
- **REQ-013**: El sistema MUST permitir documentar durante el ingreso daños preexistentes descritos como golpes, rayones o fallas.
- **REQ-014**: El sistema MUST exigir para cada novedad física la clasificación Leve, Moderada o Grave y asociarla de forma inmutable al tránsito de entrada correspondiente.
- **REQ-015**: El sistema MUST manejar las categorías de celda Carro, Moto, Camioneta y Discapacitado como categorías fijas.
- **REQ-016**: El sistema MUST validar compatibilidad estricta antes de asignar una celda: Carro con celda Carro o Discapacitado; Moto con celda Moto; Camioneta con celda Camioneta.
- **REQ-017**: El sistema MUST cambiar de Disponible a Ocupada, de forma atómica al confirmar la entrada, la celda asignada y disponible.
- **REQ-018**: El sistema MUST cambiar automáticamente a Disponible la celda ocupada al procesar la salida de su vehículo.
- **REQ-019**: El sistema MUST exigir que el operario abra caja con una base de efectivo antes de permitirle cobrar mensualidades.
- **REQ-020**: El sistema MUST activar inmediatamente el contrato nuevo o renovable que no esté Cancelado cuando el pago se registre exitosamente y contar los meses pagados desde el vencimiento actual si el contrato aún está vigente, o desde la fecha del pago si el contrato está vencido o es nuevo.
- **REQ-021**: El sistema MUST registrar los métodos Efectivo, Transferencia Bancaria y Tarjeta de Crédito/Débito.
- **REQ-022**: El sistema MUST exigir el código o número de referencia para registrar un pago por transferencia bancaria.
- **REQ-023**: El sistema MUST generar por cada pago un comprobante fiscal con numeración consecutiva única, el valor neto de mensualidad proporcionado al registrar el pago, IVA del 19% y datos de identificación del cliente; el negocio fija esa tarifa fuera del sistema.
- **REQ-024**: El sistema MUST impedir que los operarios anulen o eliminen pagos.
- **REQ-025**: El sistema MUST permitir anular pagos únicamente a un Administrador, después de solicitar sus credenciales de confirmación y una justificación obligatoria, y registrar la justificación en la bitácora de auditoría.
- **REQ-026**: El sistema MUST validar las placas colombianas especificadas: ABC123 para carros y ABC12D para motos, y rechazar las que no correspondan al formato de su tipo de vehículo.
- **REQ-027**: El sistema MUST asociar cada pago recibido al operario que abrió la caja vigente.
- **REQ-028**: El sistema MUST permitir al titular cerrar su caja abierta y a un Administrador cerrar cualquier caja abierta; registrará la fecha y hora exactas del servidor, dejará la caja no disponible para nuevas transacciones y no solicitará ni registrará un monto final de cierre.

### Key Entities *(include if feature involves data)*

- **Usuario**: Persona operaria o administradora identificada por documento, con credenciales y rol; una sesión activa habilita operaciones específicas.
- **Cliente**: Persona identificada de forma única por CC, CE o NIT.
- **Vehículo**: Vehículo identificado por placa y tipo, asociado de forma exclusiva a un contrato.
- **Contrato de mensualidad**: Relación entre un cliente y un único vehículo, con estado y fecha de vencimiento.
- **Caja**: Apertura realizada por un operario con base de efectivo, asociada a su turno y cerrada por el titular o un Administrador con fecha y hora del servidor.
- **Tránsito**: Registro inmutable de entrada o salida que identifica fecha y hora del servidor, operario y celda.
- **Novedad**: Descripción de acceso excepcional o daño preexistente; la novedad física incluye severidad y queda vinculada al tránsito de entrada.
- **Celda**: Espacio con categoría fija y estado Disponible u Ocupada.
- **Pago**: Recaudo de mensualidad con método, operario/caja y, para transferencia, referencia; su anulación requiere autorización y justificación.
- **Comprobante fiscal**: Documento consecutivo asociado a un pago, con valores neto e IVA y datos del cliente.
- **Bitácora de auditoría**: Registro de justificación de anulaciones de pago autorizadas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los intentos de consulta de disponibilidad, entrada, salida y pago sin sesión activa son rechazados.
- **SC-002**: El 100% de los intentos de transacción realizados por operarios sin caja abierta a su nombre son rechazados.
- **SC-003**: El 100% de las entradas confirmadas cumplen las reglas de estado y vigencia del contrato, Anti-Passback y compatibilidad de celda, o cuentan con la autorización excepcional y novedad requeridas.
- **SC-004**: El 100% de las entradas confirmadas dejan una celda compatible Ocupada, y el 100% de las salidas confirmadas liberan inmediatamente la celda asociada.
- **SC-005**: El 100% de los tránsitos conservan fecha y hora del servidor, ID del operario e ID de la celda y no admiten edición o eliminación.
- **SC-006**: El 100% de los pagos exitosos generan un comprobante con numeración consecutiva única, valor neto, IVA del 19% y datos del cliente.
- **SC-007**: El 100% de las anulaciones de pago registradas tienen autorización de Administrador, credenciales de confirmación y justificación de auditoría.
- **SC-008**: El 100% de los pagos recibidos quedan asociados al operario que abrió la caja vigente.
- **SC-009**: El 100% de los cierres de caja quedan registrados con hora del servidor y no habilitan transacciones posteriores; el titular puede abrir una caja nueva.

## Assumptions

- La fecha y hora actual usadas para validar la vigencia contractual corresponden a la fecha del servidor.
- Los tipos de vehículo usados para compatibilidad de celdas son Carro, Moto y Camioneta; las celdas Discapacitado solo admiten vehículos Carro.
- La categoría y severidad de novedades de daños físicos no se aplican automáticamente a las novedades de acceso excepcional, porque son registros con propósitos distintos en los requisitos entregados.
- El negocio fija la tarifa de la mensualidad fuera del sistema y proporciona su valor neto al registrar el pago; el sistema no mantiene tarifas. Los meses pagados se cuentan desde el vencimiento actual para un contrato vigente y desde la fecha del pago para uno vencido o nuevo.
- Un contrato Cancelado no se reactiva por pago; se requiere crear un contrato nuevo para volver a contratar la mensualidad.
- El cierre de caja registra únicamente la fecha y hora del servidor; no realiza arqueo ni exige monto final. El titular puede cerrar su caja y un Administrador puede cerrar cualquier caja abierta.
