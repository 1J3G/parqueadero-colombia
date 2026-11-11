<!--
Sync Impact Report
- Version change: 2.3.0 → 2.4.0
- Modified rules: RN-13 now defines who can close a cash opening, records the
  server closure timestamp, and excludes a final cash count.
- Version change: 2.4.0 → 2.5.0
- Modified rules: RN-02 now defines automatic persisted expiration and
  Administrator-only cancellation with mandatory justification.
- Version change: 2.5.0 → 2.6.0
- Modified rules: RN-10 and RN-11 define the Libre/Ocupado/En mantenimiento
  states and administrative maintenance transitions; RN-19 and RN-20 define
  Administrator-only user creation and cancellation-audit access.
- Version change: 2.6.0 → 2.6.1
- Modified rules: RN-05 explicitly prevents a vehicle/plate already inside
  from being assigned another cell or entering again.
- Version change: 2.6.1 → 2.6.2
- Modified rules: RN-04 clarifies that each contract references one vehicle,
  while the schema may retain multiple contracts for that vehicle.
- Version change: 2.6.2 → 2.7.0
- Modified rules: RN-03 requires entry to be within the persisted start/end
  dates; RN-12 sequences prepaid periods for the same customer and vehicle.
- Templates: No changes required.
- Follow-up TODOs: Ninguno.
-->
# Parqueadero Autos Colombia Constitution

## Migration Mode

**Modo**: REWRITE

**Justificación**: La constitución define una aplicación nueva para gestionar
mensualidades, vehículos, celdas, tránsitos y pagos, con el stack objetivo
especificado por el usuario.

## Core Principles

### I. Reglas de Dominio como Fuente de Verdad
Las reglas RN-01 a RN-20 de esta constitución son obligatorias para el diseño
de arquitectura, base de datos, lógica del backend, validaciones y casos de uso.
La especificación del producto (`spec.md`) debe documentar el comportamiento
que se construirá y no puede contradecir estas reglas. No se permite código
sombra ni funcionalidades especulativas.

**Razón**: Las reglas expresan las restricciones operativas, financieras y de
auditoría del parqueadero y prevalecen sobre supuestos de implementación.

### II. Simplicidad, Estructura Plana y Estilo Funcional
La estructura del proyecto se limita a `/frontend`, `/backend` y `/db`. No se
implementará Clean Architecture ni patrones complejos. Se priorizan funciones
puras, composición funcional, estado reactivo con RxJS o Signals e inyección
funcional con `inject()` en Angular. Las clases se limitan al cascarón sintáctico
obligatorio de Angular (`@Component`, `@Injectable`) y a estructuras de datos y
validación en Python (Pydantic o dataclasses).

La nomenclatura será `snake_case` en Python y MySQL, y `camelCase` o
`kebab-case` en Angular, según corresponda al elemento.

**Razón**: Una implementación sencilla y ajustada al alcance reduce complejidad
innecesaria sin apartarse de los requisitos documentados.

### III. Validación, Acceso y Manejo de Errores
La aplicación debe autenticar a los usuarios que la operan. Los permisos
administrativos requeridos por RN-06, RN-16, RN-19 y RN-20 se comprobarán antes de autorizar
esas operaciones. La interfaz nunca expondrá errores técnicos crudos ni
stack traces: los traducirá a mensajes comprensibles para el usuario. El backend
retornará códigos HTTP semánticos, incluyendo 400 para peticiones inválidas,
401 para falta de autenticación, 403 para falta de permiso y 409 para conflictos
de operación.

**Razón**: La autenticación y los permisos protegen operaciones sensibles;
mensajes claros y respuestas HTTP consistentes facilitan el uso y la integración.

### IV. Desarrollo Guiado por la Especificación
Antes de modificar código fuente, se requiere un requisito correspondiente en
`spec.md`. Si una instrucción contradice esta constitución, o se detecta una
falla lógica en los requisitos, el agente debe detenerse, explicar el conflicto
y solicitar que se actualice `spec.md` (y esta constitución cuando corresponda).
No agregará funciones “por si acaso”.

**Razón**: Mantener la especificación alineada con las reglas evita decisiones
de negocio implícitas o cambios de alcance no aprobados.

## Stack Tecnológico Objetivo

| Componente | Tecnología | Versión / notas |
|-----------|------------|-----------------|
| Frontend | Angular Standalone | Versión no especificada |
| Backend | Python / FastAPI | Versión no especificada |
| Base de datos | MySQL local | Versión no especificada |
| Control de versiones | Git / GitHub | — |

## Reglas de Dominio

Estas reglas son la fuente única de verdad para el comportamiento del sistema.

### Módulo 1: Gestión de Usuarios y Contratos (Mensualidades)

- **RN-01 (Unicidad de usuario y vehículo)**: Cada cliente se identifica
  unívocamente por documento de identidad (CC, CE, NIT). Cada vehículo se
  vincula al usuario mediante una placa alfanumérica colombiana única:
  `ABC123` para carros o `ABC12D` para motos.
- **RN-02 (Ciclo de vida del contrato)**: Un contrato de mensualidad solo puede
  tener uno de estos cuatro estados mutuamente excluyentes: Pendiente de Pago,
  Activo, Vencido o Cancelado. Si se crea sin pago asentado, su estado inicial
  es Pendiente de Pago. Un contrato Cancelado no se reactiva; para contratar de
  nuevo se requiere crear otro contrato. Cuando la fecha del servidor supera
  el vencimiento de un contrato Activo, el sistema actualiza su estado a
  Vencido al detectarlo durante una consulta u operación. Solo un Administrador
  puede cancelar un contrato y debe proporcionar una justificación obligatoria.
- **RN-03 (Vigencia contractual)**: El ingreso automatizado solo se permite si
  el contrato asociado está Activo y la fecha del servidor es mayor o igual a
  su fecha de inicio (cuando exista) y menor o igual a su fecha de finalización.
- **RN-04 (Vehículo asociado a mensualidad)**: Cada contrato estándar da
  derecho de parqueo a un solo vehículo, identificado por una placa única. La
  asociación no implica que el vehículo solo pueda tener un contrato
  registrado: la base admite varios contratos para el mismo vehículo y todos
  comparten su estado de ocupación. No se permite el ingreso de un vehículo
  sustituto bajo el mismo contrato sin una modificación contractual previa de
  un Administrador. No se define una restricción de exclusividad entre
  contratos vigentes del mismo vehículo.

### Módulo 2: Entrada, Salida y Novedades de Vehículos

- **RN-05 (Anti-passback)**: Un vehículo cuya placa ya ocupa una celda dentro
  del parqueadero no puede seleccionar otra celda ni registrar otra entrada,
  incluso mediante otro contrato asociado al mismo vehículo. La interfaz
  muestra la celda ocupada y el backend rechaza cualquier repetición. Un
  vehículo cuyo estado sea Fuera del Parqueadero no puede registrar una salida.
- **RN-06 (Bloqueo contractual)**: Si al momento del ingreso el contrato está
  Vencido, Pendiente de Pago o Cancelado, se bloquea la apertura de talanquera
  o el registro. El acceso excepcional requiere autorización explícita de un
  rol Administrativo y la creación obligatoria de una novedad.
- **RN-07 (Inmutabilidad y auditoría de tránsitos)**: Cada entrada y salida se
  persiste de forma inmutable con timestamp del servidor, ID del operario en
  turno e ID de la celda asignada. Estos datos no pueden modificarse ni
  eliminarse mediante operaciones del sistema.
- **RN-08 (Novedades físicas obligatorias)**: Si al ingresar se detectan daños
  preexistentes (golpes, rayones o fallas visibles), deben registrarse antes
  de confirmar la entrada. Cada novedad se categoriza como Leve, Moderada o
  Grave y se asocia al registro de entrada.

### Módulo 3: Gestión de Celdas y Capacidad

- **RN-09 (Tipo y compatibilidad de celda)**: Cada celda tiene una categoría
  fija: Carro, Moto, Camioneta o Discapacitado. La asignación exige
  compatibilidad estricta: Carro con Carro, Moto con Moto, Camioneta con
  Camioneta y únicamente vehículos Carro con celdas Discapacitado.
- **RN-10 (Estados y ocupación de celdas)**: Cada celda tiene uno de estos
  estados: Libre, Ocupado o En mantenimiento. Una celda Ocupada no puede
  asignarse a otro vehículo ni cambiar manualmente de estado. Al confirmar una
  entrada, la celda asignada cambia atómicamente de Libre a Ocupado; las celdas
  En mantenimiento no están disponibles para entradas. Solo un Administrador
  puede cambiar una celda no ocupada entre Libre y En mantenimiento.
- **RN-11 (Liberación automatizada)**: Al confirmar la salida del vehículo, el
  estado de su celda asociada cambia de inmediato y automáticamente de
  Ocupado a Libre.

### Módulo 4: Gestión de Pagos

- **RN-12 (Activación por pago)**: El registro exitoso del pago de una
  mensualidad nueva o renovación, siempre que el contrato no esté Cancelado,
  cambia el contrato a Activo y persiste el inicio y vencimiento de su período.
  La fecha de vencimiento base es la más lejana entre los vencimientos de
  contratos Activos no vencidos del mismo cliente y vehículo, incluido el
  contrato pagado si cumple esas condiciones. Una renovación del mismo período conserva su fecha de inicio; un
  contrato nuevo o vencido se programa para el día siguiente al vencimiento
  base. Si no existe uno, inicia el día del pago. Un período con
  fecha de inicio futura no habilita entradas antes de esa fecha. Los pagos
  concurrentes del mismo vehículo serializan el cálculo de vencimientos.
- **RN-13 (Integridad de recaudo y ciclo de caja)**: Un operario solo puede
  procesar transacciones si tiene una caja abierta a su nombre. Todo pago
  recibido se asocia al ID del operario que abrió el turno de caja vigente. No
  se registran pagos hasta que el operario realice explícitamente la Apertura
  de Caja con su base de efectivo. El titular puede cerrar su caja y un
  Administrador puede cerrar cualquier caja abierta. El cierre registra la
  fecha y hora del servidor, deja la caja fuera de uso para nuevas transacciones
  y no solicita ni registra un monto final.
- **RN-14 (Comprobante tributario)**: Cada pago de mensualidad procesado emite
  obligatoriamente un comprobante fiscal o documento equivalente con
  numeración consecutiva, valor neto, IVA vigente (19%) y datos de
  identificación del usuario.
- **RN-15 (Métodos de pago)**: Se registrará explícitamente el método utilizado:
  Efectivo, Transferencia Bancaria o Tarjeta de Crédito/Débito. Para una
  transferencia se exige el código de referencia o número de aprobación.
- **RN-16 (Restricción de anulaciones)**: El operario de turno no puede borrar
  ni anular pagos registrados. Una corrección por error humano requiere la
  contraseña de un perfil Administrador y genera un registro histórico de
  auditoría con la justificación del reajuste.

### Módulo 5: Autenticación y Autorización

- **RN-17 (Autenticación y sesión activa)**: Operarios y administradores se
  autentican con su documento de identidad y contraseña. Solo usuarios con
  sesión activa pueden consultar disponibilidad de celdas, registrar entradas
  o salidas y procesar pagos.
- **RN-18 (Cambio de vehículo contractual)**: Solo un usuario con rol
  Administrador puede autorizar la modificación de la placa asociada a un
  contrato existente.
- **RN-19 (Administración de usuarios)**: Solo un Administrador puede crear
  usuarios con documento único y rol Operario o Administrador. Las contraseñas
  se almacenan como hash y nunca se exponen en consultas.
- **RN-20 (Auditoría de cancelaciones)**: Solo un Administrador puede consultar
  el historial de cancelaciones de contratos, que debe mostrar contrato,
  cliente, placa, Administrador que canceló, fecha y justificación.

## Manejo de Errores y Validaciones

- La interfaz no mostrará errores técnicos crudos ni trazas; los presentará
  mediante mensajes amigables, por ejemplo: “La celda se encuentra ocupada”.
- El backend utilizará códigos HTTP semánticos: 400 para petición inválida,
  401 para falta de autenticación, 403 para operación no autorizada y 409 para
  conflicto.

## Gobernanza

Esta constitución y `spec.md` rigen las decisiones del proyecto. Toda propuesta
de modificación debe describir el cambio y su impacto, actualizar los
requisitos afectados y ser aprobada por el responsable del proyecto antes de
implementarse. Los cambios incompatibles deben documentar su impacto antes de
la aprobación.

La versión sigue semver:

- **MAJOR**: eliminación o redefinición incompatible de principios o reglas.
- **MINOR**: incorporación de un principio o sección, o ampliación material
  de la guía.
- **PATCH**: aclaraciones y correcciones que no cambian el significado.

Cada revisión de especificación, plan o implementación debe comprobar su
conformidad con las reglas RN-01 a RN-20, el stack, las restricciones de
estructura y el proceso de desarrollo guiado por especificación.

**Versión**: 2.7.0 | **Ratificada**: 2025-10-24 | **Última enmienda**: 2026-11-11
