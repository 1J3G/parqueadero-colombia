from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes import auth, cash, cells, contracts, customers, payments, receipts, transits

app = FastAPI(title="Autos Colombia", version="1.0.0")

app.include_router(auth.router)
app.include_router(cash.router)
app.include_router(cells.router)
app.include_router(customers.router)
app.include_router(contracts.router)
app.include_router(transits.router)
app.include_router(payments.router)
app.include_router(receipts.router)


@app.exception_handler(RequestValidationError)
async def invalid_request_handler(_request: Request, _error: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": "La solicitud contiene datos inválidos."})
