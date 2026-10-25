# Research: Gestión de operaciones del parqueadero

**Fecha**: 2026-10-24
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
