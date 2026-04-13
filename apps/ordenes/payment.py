"""
Mock payment module for OvniTicket.
Replace the body of `procesar_pago` with a real gateway (e.g. Stripe) later.
The interface is intentionally stateless — no models, no DB writes.
"""

import uuid
import logging

logger = logging.getLogger(__name__)

_FAILURE_TOKEN = "fail"
_CANCEL_TOKEN = "cancel"


def procesar_pago(monto: float, metodo_pago: str, token: str | None = None) -> dict:
    """
    Simulate a payment gateway call.

    Parameters
    ----------
    monto : float
        Amount to charge, in the event's currency.
    metodo_pago : str
        Payment method identifier (e.g. 'mock', 'card', 'oxxo').
    token : str | None
        Opaque gateway token.  Pass ``'fail'`` to simulate a decline;
        pass ``'cancel'`` to simulate a user cancellation.

    Returns
    -------
    dict
        ``{ 'success': bool, 'transaction_id': str, 'error': str | None }``
    """
    logger.debug(
        "procesar_pago called — monto=%.2f metodo=%s token=%s",
        monto,
        metodo_pago,
        token,
    )

    if token == _CANCEL_TOKEN:
        logger.info("Mock payment: cancellation requested by token")
        return {
            "success": False,
            "transaction_id": "",
            "error": "Pago cancelado por el usuario.",
        }

    if token == _FAILURE_TOKEN:
        logger.info("Mock payment: decline triggered by token")
        return {
            "success": False,
            "transaction_id": "",
            "error": "Pago rechazado por el procesador (mock decline).",
        }

    # Happy path — generate a fake transaction ID.
    transaction_id = f"mock-{uuid.uuid4().hex[:16]}"
    logger.info("Mock payment: success — transaction_id=%s", transaction_id)
    return {
        "success": True,
        "transaction_id": transaction_id,
        "error": None,
    }
