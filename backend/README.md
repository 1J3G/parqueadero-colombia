# Backend local setup

The backend is a FastAPI application connected to a local MySQL database. It does not create the database or apply migrations when it starts.

## Database setup

From `backend`, create a new database with:

```powershell
Get-Content ..\db\schema.sql | mysql -u root -p
```

For an existing database created from an earlier schema, apply migrations in order. Apply only migrations that have not already been run:

```powershell
Get-Content ..\db\migrations\001_contract_status_lifecycle.sql | mysql -u root -p
Get-Content ..\db\migrations\002_cell_status_maintenance.sql | mysql -u root -p
Get-Content ..\db\migrations\003_contract_service_start.sql | mysql -u root -p
```

Do not run the migrations on a new database created from the current `schema.sql`.

Create a MySQL application account with access to `autos_colombia`, copy `.env.example` to `.env`, and set the connection values. Do not commit `.env`.

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m app.seed
uvicorn app.main:app --reload
```

`requirements.txt` contains runtime dependencies; `requirements-dev.txt` includes the additional test client needed for the backend suite.

The seed command creates the initial Administrator and Operario interactively. It hashes passwords and does not overwrite existing accounts. After the first setup, Administrators can create accounts from the application.

The API is available at `http://localhost:8000`; interactive API documentation is at `http://localhost:8000/docs`.

Add the parkadero's real cells to the `cells` table. The application does not invent default cells or capacity.

## Implemented API

- Authentication: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- Cash: `POST /api/cash/open`, `GET /api/cash/current`, `GET /api/cash/open` (Administrator), `POST /api/cash/{id}/close`
- Cells: `GET /api/cells`, `PATCH /api/cells/{id}/status` (Administrator; only non-occupied cells)
- Customers: `POST /api/customers`, `GET /api/customers`
- Contracts: `POST /api/contracts`, `GET /api/contracts`, `PATCH /api/contracts/{id}/plate` (Administrator), `POST /api/contracts/{id}/cancel` (Administrator), `GET /api/contracts/cancellations` (Administrator)
- Users: `GET /api/users`, `POST /api/users` (Administrator)
- Transits: `POST /api/transits/entry`, `POST /api/transits/exit`
- Payments: `POST /api/payments`, `POST /api/payments/{id}/void` (Administrator)
- Receipts: `GET /api/receipts/{payment_id}`

The contract listing includes each vehicle's current inside/outside state and occupied cell. A vehicle can be referenced by multiple contracts, but all share one occupancy state. Entry and exit lock that vehicle row and apply Anti-Passback across its contracts. After a successful exit, an Active contract within its start/end dates can register a new entry in another compatible free cell.

Payments sequence validity periods by customer and vehicle. If another contract for that same customer and vehicle is Active through November 30 and one month is paid on November 11, the new period starts December 1 and expires December 30. Payments lock the vehicle row while choosing the latest unexpired contract date; entry is rejected until the selected contract's `starts_on`. New installations get this field from `db/schema.sql`; existing installations apply migration `003_contract_service_start.sql` after migrations 001 and 002.

## Verification

From `backend`, run `python -m unittest discover -s tests -v` and `python -m compileall -q app tests`. These checks use mocks/unit tests; they do not replace authenticated integration testing against MySQL or the non-functional validation listed in the project plan.
