import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException

CONTRACT_STATUSES = ("Pendiente de Pago", "Activo", "Vencido", "Cancelado")
CELL_CATEGORIES = ("Carro", "Moto", "Camioneta", "Discapacitado")
PAYMENT_METHODS = ("Efectivo", "Transferencia Bancaria", "Tarjeta Crédito/Débito")
NOVELTY_SEVERITIES = ("Leve", "Moderada", "Grave")

CAR_PLATE = re.compile(r"^[A-Z]{3}[0-9]{3}$")
MOTORCYCLE_PLATE = re.compile(r"^[A-Z]{3}[0-9]{2}[A-Z]$")


def validate_plate(plate: str, vehicle_type: str) -> str:
    normalized = plate.strip().upper()
    pattern = MOTORCYCLE_PLATE if vehicle_type == "Moto" else CAR_PLATE
    if vehicle_type not in ("Carro", "Moto", "Camioneta") or not pattern.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="La placa no corresponde al formato del tipo de vehículo.")
    return normalized


def compatible_cell(vehicle_type: str, category: str) -> bool:
    return (vehicle_type == "Carro" and category in ("Carro", "Discapacitado")) or vehicle_type == category


def require_entry_permission(
    status: str,
    starts_on: date | None,
    expires_on: date | None,
    today: date,
    exceptional: bool,
) -> None:
    if status == "Activo":
        if starts_on is not None and starts_on > today:
            raise HTTPException(status_code=409, detail="La vigencia del contrato aún no inicia.")
        if expires_on is not None and today <= expires_on:
            return
    if status in ("Pendiente de Pago", "Vencido", "Cancelado") and exceptional:
        return
    raise HTTPException(status_code=409, detail="El contrato no permite el ingreso sin autorización excepcional.")


def renewed_expiration(status: str, current_expiration: date | None, paid_months: int, payment_date: date) -> date:
    if status == "Cancelado":
        raise HTTPException(status_code=409, detail="Un contrato Cancelado no se puede reactivar; cree uno nuevo.")
    if paid_months < 1:
        raise HTTPException(status_code=400, detail="La cantidad de meses pagados debe ser mayor que cero.")
    base_date = current_expiration if current_expiration and current_expiration >= payment_date else payment_date
    month_index = base_date.month - 1 + paid_months
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    next_month = month % 12 + 1
    next_year = year + (month == 12)
    try:
        last_day = (date(next_year, next_month, 1) - date.resolution).day
        return date(year, month, min(base_date.day, last_day))
    except ValueError as error:
        raise HTTPException(status_code=400, detail="La vigencia solicitada excede el rango de fechas permitido.") from error


def calculate_tax(net_amount: Decimal) -> Decimal:
    return (net_amount * Decimal("0.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
