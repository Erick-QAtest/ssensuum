"""Cliente mínimo de la API de Mercado Pago (Checkout Pro)."""
from datetime import datetime

import httpx

from ..config import settings
from ..domain.errors import PaymentGatewayError, PaymentsUnavailableError

API = "https://api.mercadopago.com"
TIMEOUT = 15


def _headers() -> dict:
    if not settings.mp_access_token:
        raise PaymentsUnavailableError("Los pagos en línea no están disponibles por ahora")
    return {"Authorization": f"Bearer {settings.mp_access_token}"}


def ensure_configured() -> None:
    _headers()


def is_sandbox() -> bool:
    return settings.mp_sandbox or settings.mp_access_token.startswith("TEST-")


def create_preference(
    *,
    reservation_id: str,
    title: str,
    amount: int,
    payer_name: str,
    payer_phone: str,
    expires_at: datetime,
) -> dict:
    base = settings.public_base_url.rstrip("/")
    return_url = f"{base}/reserva/{reservation_id}"
    body = {
        "items": [{"id": reservation_id, "title": title, "quantity": 1, "unit_price": float(amount), "currency_id": "MXN"}],
        "payer": {"name": payer_name, "phone": {"area_code": "52", "number": payer_phone}},
        "external_reference": reservation_id,
        "back_urls": {"success": return_url, "pending": return_url, "failure": return_url},
        # Solo aprobado o rechazado: sin pagos "pendientes" que dejen el horario en el aire.
        "binary_mode": True,
        # Sin OXXO ni transferencias: tardan horas y el horario solo se aparta unos minutos.
        "payment_methods": {"excluded_payment_types": [{"id": "ticket"}, {"id": "atm"}], "installments": 1},
        "expires": True,
        "expiration_date_to": expires_at.isoformat(timespec="milliseconds"),
        "statement_descriptor": "SSENSUUM",
    }
    # Mercado Pago solo acepta regreso automático y webhook con URLs públicas https.
    if base.startswith("https://"):
        body["auto_return"] = "approved"
        body["notification_url"] = f"{base}/api/payments/webhook"

    try:
        response = httpx.post(f"{API}/checkout/preferences", json=body, headers=_headers(), timeout=TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise PaymentGatewayError("No pudimos iniciar el pago. Intenta de nuevo en un momento.") from exc
    return response.json()


def get_payment(payment_id: str) -> dict:
    try:
        response = httpx.get(f"{API}/v1/payments/{payment_id}", headers=_headers(), timeout=TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise PaymentGatewayError("No pudimos consultar el pago") from exc
    return response.json()
