# Backend local setup

The application uses a local MySQL database. It does not create the database or run migrations when the API starts.

1. Create the schema with a MySQL account allowed to create the database:

   ```powershell
   Get-Content ..\db\schema.sql | mysql -u root -p
   ```

   If `autos_colombia` already has the earlier schema, apply the contract lifecycle migration once:

   ```powershell
   Get-Content ..\db\migrations\001_contract_status_lifecycle.sql | mysql -u root -p
   ```

   Do not run this migration on a new database created from the updated `schema.sql`.

2. Create a MySQL application account with access to `autos_colombia`, then copy `.env.example` to `.env` and set its credentials. Do not commit `.env`.
3. Install dependencies and seed the initial Administrator and Operario accounts. The seed prompts for each identity document and password; it never stores plaintext passwords or overwrites an existing account:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m app.seed
   ```

4. Insert the parkadero's real cells into the `cells` table. The specification does not set capacity or cell labels, so the application does not invent default cells.
5. Start the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

Run the Angular application from `frontend` with `npm start`. Its development proxy forwards `/api` requests to the local API.

## Implemented API

- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- `POST /api/cash/open`, `GET /api/cash/current`, `GET /api/cash/open` (Administrador), `POST /api/cash/{id}/close`
- `GET /api/cells`
- `POST /api/customers`, `GET /api/customers`
- `POST /api/contracts`, `GET /api/contracts`, `PATCH /api/contracts/{id}/plate`, `POST /api/contracts/{id}/cancel` (Administrador; justification required)
- `POST /api/transits/entry`, `POST /api/transits/exit`
- `POST /api/payments`, `POST /api/payments/{id}/void`
- `GET /api/receipts/{payment_id}`
