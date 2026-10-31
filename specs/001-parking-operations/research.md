# Research: Gestión de operaciones del parqueadero

**Fecha**: 2026-10-30
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
- Renovación: meses contados desde vencimiento vigente; contrato vencido o nuevo, desde la fecha del pago.
- Tarifa neta: provista al cobrar y fijada fuera del sistema; no habrá catálogo de tarifas.
- Estado de celdas: se usan Libre, Ocupado y En mantenimiento; entradas y salidas cambian automáticamente Libre/Ocupado y solo Administradores pueden cambiar mantenimiento sobre una celda no ocupada.
- Cuentas: un Administrador crea usuarios, define su contraseña inicial y el backend reutiliza el hash PBKDF2 del inicio de sesión; las respuestas de listado no incluyen hashes.
- Auditoría de cancelaciones: se reutilizan los campos `cancelled_by`, `cancelled_at` y `cancellation_justification` de `contracts`; se expone el historial solo a Administradores, sin crear una tabla redundante.
- Confirmaciones de creación: la interfaz presenta un mensaje global cuando una solicitud termina con HTTP 201; las respuestas de error siguen el canal de error existente.
- Anti-Passback por placa: contratos que apunten al mismo vehículo comparten el último estado de tránsito; mientras la última operación sea Entrada, se muestra la celda ocupada y no se ofrece otra asignación. La API serializa la validación bloqueando la fila del vehículo y rechaza nuevas entradas hasta su salida. No requiere migración de esquema.
