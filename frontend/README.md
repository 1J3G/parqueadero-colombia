# Frontend

The user interface is an Angular standalone application. Start the FastAPI backend and configure its MySQL database before using features that require persisted data.

## Development

```powershell
npm ci
npm start
```

Open `http://localhost:4200`. The development proxy forwards `/api` requests to `http://localhost:8000`.

## Build and tests

```powershell
npm run build
npm test
```

## Main screens

- **Caja**: open and close cash shifts.
- **Clientes y contratos**: register customers and monthly contracts; Administrators can change plates and cancel contracts.
- **Entradas y salidas**: register vehicle movements and novelties. When a plate is already inside, the screen shows its occupied cell, hides cell selection and entry submission, and keeps exit available. After a successful exit, a valid contract can re-enter using another compatible free cell.
- **Celdas**: view all cells, their state and the plate occupying each occupied cell; Administrators can mark non-occupied cells as in maintenance or free.
- **Pagos**: register monthly payments and receipts; Administrators can void payments.
- **Usuarios**: create and list Operario and Administrador accounts (Administrator only).
- **Auditoría de contratos**: review contract cancellations (Administrator only).
