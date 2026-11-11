# Autos Colombia — Parqueadero

Aplicación web para la operación de un parqueadero: usuarios, clientes, contratos, celdas, entradas/salidas, caja, pagos y auditoría.

## Tecnologías

- Frontend: Angular standalone.
- Backend: FastAPI y Python.
- Persistencia: MySQL local.

## Iniciar el proyecto

1. Configura MySQL y el backend siguiendo [backend/README.md](./backend/README.md). Crea las cuentas iniciales con `python -m app.seed` y deja el backend activo en `http://localhost:8000`.
2. En otra terminal, inicia el frontend siguiendo [frontend/README.md](./frontend/README.md). La aplicación estará en `http://localhost:4200`.
3. Registra las celdas reales del parqueadero en la tabla `cells`; no se generan celdas por defecto.

En **Entradas y salidas**, una placa que ya esté dentro muestra su celda ocupada y no permite asignar otra ni registrar un segundo ingreso. Después de confirmar su salida, el contrato Activo y vigente puede reingresar en otra celda compatible que esté Libre.

Al pagar por adelantado otro contrato de la misma placa y cliente, el período nuevo se programa para el día siguiente al vencimiento vigente más lejano. El sistema muestra su inicio y vencimiento, y no permite usar ese contrato antes de su fecha de inicio.

## Documentación

- [Modelo de datos](./docs/modelos-de-datos.md)
- [Especificación funcional](./specs/001-parking-operations/spec.md)
- [Plan de implementación](./specs/001-parking-operations/plan.md)
- [Tareas de implementación](./specs/001-parking-operations/tasks.md)
- [Constitución del proyecto](./.specify/memory/constitution.md)
- Los diagramas PlantUML están en [docs/](./docs/).
