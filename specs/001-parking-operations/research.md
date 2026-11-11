# Research: Gestión de operaciones del parqueadero

**Fecha de actualización**: 2026-11-11
**Especificación**: [spec.md](./spec.md)

## Decisiones

### Framework Python del backend

- **Decisión**: FastAPI.
- **Rationale**: El usuario lo seleccionó al iniciar la planificación. Encaja con el stack Python definido en la constitución y permite mantener la API en módulos sencillos, con validación de datos.
- **Alternativas consideradas**: Flask; Django REST Framework; dejar la selección pendiente.

### Acceso a MySQL

- **Decisión**: Usar un conector MySQL DB-API y SQL parametrizado, sin ORM.
- **Rationale**: Minimiza dependencias y capas, de acuerdo con el principio constitucional de simplicidad. `mysql-connector-python` es la dependencia propuesta para el plan.
- **Alternativas consideradas**: ORM o capa de persistencia adicional; se descartan para no introducir complejidad no requerida.

### Framework y versiones

- **Decisión**: Mantener Angular Standalone y las versiones de Angular, Python y MySQL sin fijar en el plan.
- **Rationale**: La constitución nombra esas tecnologías, pero no establece versiones; el plan no añade restricciones de versión sin autorización.
- **Alternativas consideradas**: Fijar versiones específicas ahora; se deja para la configuración inicial del entorno según compatibilidad disponible.

## Decisiones de negocio ya resueltas en `spec.md`

- Contrato Cancelado: acceso excepcional solo con autorización administrativa y novedad; pago de mensualidad no reactiva ese contrato, se crea uno nuevo.
- Vigencias: el vencimiento base es el más lejano entre contratos Activos no vencidos del mismo cliente y vehículo (incluido el contrato pagado cuando corresponda). La renovación de un contrato ya vigente conserva su fecha de inicio; uno nuevo o vencido inicia al día siguiente al vencimiento base. Si no hay vencimiento vigente, inicia el día del pago. Los contratos Cancelados, vencidos, de otro cliente o de otro vehículo no afectan la secuencia.
- Período futuro: se persiste `starts_on` además de `expires_on`; un contrato pagado por anticipado no permite entradas hasta `starts_on`. Los pagos del mismo vehículo bloquean su fila antes de consultar vencimientos, serializando la asignación del siguiente período sin bloquear pagos de otros vehículos.
- Persistencia: `starts_on` se agrega mediante una migración aditiva; no se modifica la cardinalidad entre clientes, vehículos y contratos.
- Tarifa neta: provista al cobrar y fijada fuera del sistema; no habrá catálogo de tarifas.
- Estado de celdas: se usan Libre, Ocupado y En mantenimiento; entradas y salidas cambian automáticamente Libre/Ocupado y solo Administradores pueden cambiar mantenimiento sobre una celda no ocupada.
- Cuentas: un Administrador crea usuarios, define su contraseña inicial y el backend reutiliza el hash PBKDF2 del inicio de sesión; las respuestas de listado no incluyen hashes.
- Auditoría de cancelaciones: se reutilizan los campos `cancelled_by`, `cancelled_at` y `cancellation_justification` de `contracts`; se expone el historial solo a Administradores, sin crear una tabla redundante.
- Confirmaciones de creación: la interfaz presenta un mensaje global cuando una solicitud termina con HTTP 201; las respuestas de error siguen el canal de error existente.
- Anti-Passback por placa: contratos que apunten al mismo vehículo comparten el último estado de tránsito; mientras la última operación sea Entrada, se muestra la celda ocupada y no se ofrece otra asignación. La API serializa la validación bloqueando la fila del vehículo y rechaza nuevas entradas hasta su salida. No requiere migración de esquema.
- Reingreso después de salida: si el último tránsito del vehículo es Salida, el contrato vuelve a satisfacer Anti-Passback; con contrato Activo vigente se puede registrar una nueva entrada en otra celda Libre compatible. La API bloquea la fila del vehículo en entrada y salida y consume la fila devuelta por MySQL Connector antes de seguir con otras consultas.
- Cardinalidad contrato-vehículo: el DDL permite varios contratos asociados a un mismo vehículo, pero cada contrato apunta a un solo vehículo. No se implementó ni se exige exclusividad de contratos vigentes por vehículo; la ocupación física sigue siendo única por vehículo/placa.
- Requisitos no funcionales: el repositorio no contiene despliegue/monitorización ni automatización de backups. No hay evidencia de carga a 50 usuarios, restauración <= 4 h o usabilidad <= 3 min. RNF-006 requiere MySQL concurrente e idempotencia para evitar pagos duplicados ante reintentos; estos puntos se dejan como pendientes en el plan.
