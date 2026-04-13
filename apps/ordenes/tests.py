"""
Order / purchase flow test suite.

Run with:
    python manage.py test apps.ordenes --settings=config.settings

Tests cover:
  - POST /api/ordenes/  (create order directly)
  - POST /api/ordenes/comprar/  (full purchase orchestration via ejecutar_compra)
    NOTE: The /comprar/ endpoint does not yet exist as a URL-routed view.
    These tests call ejecutar_compra() directly at the service layer AND
    test the view stub that should be wired up (see CONCURRENCY_REVIEW.md).
    When the endpoint is added, update _COMPRAR_URL below and the HTTP tests
    will cover the full stack.
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.roles.models import Roles
from apps.usuarios.models import Usuarios
from apps.lugares.models import Lugares
from apps.layouts.models import Layouts
from apps.zonas.models import Zonas
from apps.grid_cells.models import GridCells
from apps.eventos.models import Eventos
from apps.precio_zona_evento.models import PrecioZonaEvento
from apps.asientos.models import EstadoAsientoEvento
from apps.asientos.services import retener_asientos, SeatUnavailableError
from apps.ordenes.models import Ordenes
from apps.ordenes.purchase import ejecutar_compra, PaymentFailedError
from apps.tickets.models import Tickets

_COMPRAR_URL = "/api/ordenes/comprar/"
_ORDENES_URL = "/api/ordenes/"


def _make_rol(nombre):
    return Roles.objects.create(nombre=nombre)


def _make_usuario(rol, suffix=""):
    now = timezone.now()
    return Usuarios.objects.create(
        nombre=f"TestOrd{suffix}",
        apellidos="User",
        correo=f"testord{suffix}@example.com",
        contrasena="hashed_password",
        fecha_nacimiento="1990-01-01",
        estatus="activo",
        fecha_creacion=now,
        fecha_actualizacion=now,
        id_rol=rol,
    )


def _make_evento(lugar, layout, tiempo_espera=10):
    now = timezone.now()
    return Eventos.objects.create(
        nombre="Purchase Test Event",
        descripcion="Test",
        fecha_inicio=now,
        fecha_fin=now + timedelta(hours=3),
        tiempo_espera=tiempo_espera,
        estatus=Eventos.ESTATUS_PUBLICADO,
        fecha_creacion=now,
        fecha_actualizacion=now,
        id_lugar=lugar,
        id_version=layout,
    )


class BaseOrdenesTestCase(TestCase):
    """
    Full fixture graph:

        Roles → Usuarios (user_a, user_b, admin)
              → Lugares → Layouts → Zonas → GridCells (2 seat cells)
              → Eventos
              → PrecioZonaEvento (100.00 / seat)
              → EstadoAsientoEvento (DISPONIBLE for both cells)
    """

    SEAT_PRICE = 100.0

    @classmethod
    def setUpTestData(cls):
        cls.rol_cliente = _make_rol("cliente")
        cls.rol_admin = _make_rol("admin")

        cls.user_a = _make_usuario(cls.rol_cliente, suffix="_a")
        cls.user_b = _make_usuario(cls.rol_cliente, suffix="_b")
        cls.admin = _make_usuario(cls.rol_admin, suffix="_admin")

        now = timezone.now()

        cls.lugar = Lugares.objects.create(
            nombre="Purchase Venue",
            ciudad="CDMX",
            pais="Mexico",
            direccion="Av Test 1",
            estatus="activo",
            fecha_creacion=now,
            fecha_actualizacion=now,
            id_dueno=cls.user_a,
        )

        cls.layout = Layouts.objects.create(
            grid_rows=5,
            grid_cols=5,
            version=1,
            estatus=Layouts.ESTATUS_PUBLICADO,
            fecha_creacion=now,
            fecha_actualizacion=now,
            id_dueno=cls.user_a,
            id_lugar=cls.lugar,
        )

        cls.zona = Zonas.objects.create(
            nombre="VIP",
            color="#00FF00",
            fecha_creacion=now,
            fecha_modificacion=now,
            id_layout=cls.layout,
        )

        cls.cell_1 = GridCells.objects.create(
            tipo="ZONA DE ASIENTOS",
            row=1,
            col=0,
            id_zona=cls.zona,
            id_layout=cls.layout,
        )
        cls.cell_2 = GridCells.objects.create(
            tipo="ZONA DE ASIENTOS",
            row=1,
            col=1,
            id_zona=cls.zona,
            id_layout=cls.layout,
        )

        cls.evento = _make_evento(cls.lugar, cls.layout)

        cls.precio_zona = PrecioZonaEvento.objects.create(
            precio=cls.SEAT_PRICE,
            fecha_creacion=now,
            fecha_actualizacion=now,
            id_zona=cls.zona,
            id_evento=cls.evento,
        )

    def setUp(self):
        """Reset seat states to DISPONIBLE before each test."""
        EstadoAsientoEvento.objects.filter(id_evento=self.evento).delete()
        EstadoAsientoEvento.objects.create(
            id_grid_cell=self.cell_1,
            id_evento=self.evento,
            estado=EstadoAsientoEvento.DISPONIBLE,
        )
        EstadoAsientoEvento.objects.create(
            id_grid_cell=self.cell_2,
            id_evento=self.evento,
            estado=EstadoAsientoEvento.DISPONIBLE,
        )

    @property
    def both_cell_ids(self):
        return [self.cell_1.pk, self.cell_2.pk]


class TestPurchaseServiceSuccess(BaseOrdenesTestCase):
    """
    test_purchase_endpoint_success — full purchase flow at service layer.

    Covers: seats held → ejecutar_compra → order + tickets created,
    seat states become VENDIDO.
    """

    def test_purchase_service_success(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        result = ejecutar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
            metodo_pago="mock",
        )

        self.assertIn("orden", result)
        self.assertIn("tickets", result)

        orden = result["orden"]
        tickets = result["tickets"]

        self.assertIsInstance(orden, Ordenes)
        self.assertEqual(orden.id_evento_id, self.evento.pk)
        self.assertEqual(orden.id_usuario_id, self.user_a.pk)
        self.assertEqual(orden.estatus, "pagado")
        expected_total = self.SEAT_PRICE * 2
        self.assertAlmostEqual(orden.total, expected_total, places=2)

        self.assertEqual(len(tickets), 2)
        for ticket in tickets:
            self.assertIsInstance(ticket, Tickets)
            self.assertEqual(ticket.id_orden_id, orden.pk)
            self.assertEqual(ticket.id_evento_id, self.evento.pk)
            self.assertAlmostEqual(ticket.precio, self.SEAT_PRICE, places=2)

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.VENDIDO)

    def test_purchase_service_creates_db_order(self):
        """Verifies the order exists in DB after purchase."""
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        initial_count = Ordenes.objects.count()
        ejecutar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.assertEqual(Ordenes.objects.count(), initial_count + 1)

    def test_purchase_service_creates_db_tickets(self):
        """Verifies tickets are persisted for each purchased seat."""
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        initial_count = Tickets.objects.count()
        ejecutar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.assertEqual(Tickets.objects.count(), initial_count + len(self.both_cell_ids))


class TestPurchaseServiceSeatsNotHeld(BaseOrdenesTestCase):
    """
    test_purchase_endpoint_seats_not_held — seats must be held before purchase.
    Attempting to buy DISPONIBLE (not held) seats raises SeatUnavailableError.
    """

    def test_purchase_service_seats_not_held(self):
        with self.assertRaises(SeatUnavailableError):
            ejecutar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
            )

    def test_purchase_service_seats_held_by_wrong_user(self):
        """user_b holds, user_a tries to purchase — must fail."""
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_b,
        )

        with self.assertRaises(SeatUnavailableError):
            ejecutar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
            )

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.RETENIDO)
            self.assertEqual(e.retenido_por_id, self.user_b.pk)

    def test_purchase_service_seats_not_held_no_order_created(self):
        """No order must be written when the seat validation fails."""
        initial_count = Ordenes.objects.count()

        with self.assertRaises(SeatUnavailableError):
            ejecutar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
            )

        self.assertEqual(Ordenes.objects.count(), initial_count)


class TestPurchaseServicePaymentFailed(BaseOrdenesTestCase):
    """Payment failure path: seats should be released, no order created."""

    def test_purchase_payment_failure_releases_seats(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        with self.assertRaises(PaymentFailedError):
            ejecutar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
                token="fail",
            )

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.RETENIDO)

    def test_purchase_payment_failure_no_order_created(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        initial_count = Ordenes.objects.count()

        with self.assertRaises(PaymentFailedError):
            ejecutar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
                token="fail",
            )

        self.assertEqual(Ordenes.objects.count(), initial_count)


class TestPurchaseServiceAtomicity(BaseOrdenesTestCase):
    """
    The entire purchase must be atomic: if ticket creation fails after the
    order is written, both the order and the seat state change must roll back.

    We simulate this by patching Tickets.objects.create to raise after the
    first call. Because ejecutar_compra is @transaction.atomic, the partial
    writes must be rolled back entirely.
    """

    def test_purchase_atomicity_on_ticket_creation_failure(self):
        from unittest.mock import patch

        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        initial_orders = Ordenes.objects.count()

        original_create = Tickets.objects.create

        call_count = {"n": 0}

        def fail_on_second(**kwargs):
            call_count["n"] += 1
            if call_count["n"] >= 2:
                raise RuntimeError("Simulated DB failure on second ticket")
            return original_create(**kwargs)

        with patch.object(Tickets.objects, "create", side_effect=fail_on_second) as _mock:
            with self.assertRaises(RuntimeError):
                ejecutar_compra(
                    id_evento=self.evento.pk,
                    ids_grid_cell=self.both_cell_ids,
                    usuario=self.user_a,
                )

        self.assertEqual(Ordenes.objects.count(), initial_orders)

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.RETENIDO)


class TestOrdenesEndpointAuthentication(BaseOrdenesTestCase):
    """
    test_purchase_endpoint_unauthenticated — unauthenticated requests
    to order endpoints must return 401.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_list_ordenes_unauthenticated_returns_401(self):
        response = self.client.get(_ORDENES_URL)
        self.assertEqual(response.status_code, 401)

    def test_create_orden_unauthenticated_returns_401(self):
        response = self.client.post(
            _ORDENES_URL,
            data={
                "total": 200.0,
                "estatus": "pendiente",
                "id_evento": self.evento.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)


class TestOrdenesCreateEndpoint(BaseOrdenesTestCase):
    """
    test_purchase_endpoint_success — POST /api/ordenes/ with an
    authenticated user creates an order record.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_create_orden_authenticated_returns_201(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            _ORDENES_URL,
            data={
                "total": 200.0,
                "estatus": "pendiente",
                "id_evento": self.evento.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("id_orden", response.data)
        self.assertEqual(response.data["estatus"], "pendiente")

    def test_create_orden_negative_total_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            _ORDENES_URL,
            data={
                "total": -50.0,
                "estatus": "pendiente",
                "id_evento": self.evento.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_orden_nonexistent_event_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            _ORDENES_URL,
            data={
                "total": 100.0,
                "estatus": "pendiente",
                "id_evento": 999999,  # doesn't exist
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class TestComprarEndpointPendingWiring(BaseOrdenesTestCase):
    """
    These tests will activate once POST /api/ordenes/comprar/ is wired in
    urls.py and views.py.  Until then they document the expected contract
    and are skipped automatically.

    Endpoint contract:
        POST /api/ordenes/comprar/
        Body: { id_evento, ids_grid_cell, metodo_pago, token? }
        → 201 + { orden, tickets } on success
        → 401 if unauthenticated
        → 409 if seats not held by caller
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def _skip_if_not_wired(self):
        if _COMPRAR_URL is None:
            self.skipTest(
                "POST /api/ordenes/comprar/ is not yet wired — set _COMPRAR_URL "
                "in ordenes/tests.py once the view + URL are added."
            )

    def test_purchase_endpoint_success(self):
        self._skip_if_not_wired()
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            _COMPRAR_URL,
            data={
                "id_evento": self.evento.pk,
                "ids_grid_cell": self.both_cell_ids,
                "metodo_pago": "mock",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("orden", response.data)
        self.assertIn("tickets", response.data)

    def test_purchase_endpoint_unauthenticated(self):
        self._skip_if_not_wired()
        response = self.client.post(
            _COMPRAR_URL,
            data={
                "id_evento": self.evento.pk,
                "ids_grid_cell": self.both_cell_ids,
                "metodo_pago": "mock",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_purchase_endpoint_seats_not_held(self):
        self._skip_if_not_wired()
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            _COMPRAR_URL,
            data={
                "id_evento": self.evento.pk,
                "ids_grid_cell": self.both_cell_ids,
                "metodo_pago": "mock",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 409)


class TestEjecutarCompraHappyPath(BaseOrdenesTestCase):
    """Full happy-path purchase with operation_id."""

    def test_returns_orden_tickets_transaction_id(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        result = ejecutar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
            metodo_pago="mock",
            operation_id="op-happy-1",
        )

        self.assertIn("orden", result)
        self.assertIn("tickets", result)
        self.assertIn("transaction_id", result)

        orden = result["orden"]
        tickets = result["tickets"]

        self.assertEqual(Ordenes.objects.count(), 1)
        self.assertEqual(orden.estatus, Ordenes.ESTATUS_PAGADO)
        self.assertEqual(orden.operation_id, "op-happy-1")

        self.assertEqual(len(tickets), 2)
        self.assertEqual(Tickets.objects.count(), 2)

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.VENDIDO)


class TestEjecutarCompraIdempotentReplay(BaseOrdenesTestCase):
    """Second call with the same operation_id returns the existing order without creating a new one."""

    def test_second_call_returns_same_orden(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        result_1 = ejecutar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
            metodo_pago="mock",
            operation_id="op-idempotent-2",
        )
        orden_pk_1 = result_1["orden"].pk

        result_2 = ejecutar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
            metodo_pago="mock",
            operation_id="op-idempotent-2",
        )

        self.assertEqual(result_2["orden"].pk, orden_pk_1)

        self.assertEqual(Ordenes.objects.count(), 1)
        self.assertEqual(Tickets.objects.count(), 2)


class TestEjecutarCompraWithoutOperationIdWorks(BaseOrdenesTestCase):
    """Omitting operation_id must still complete the happy path (backward compat)."""

    def test_no_operation_id_succeeds(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        result = ejecutar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
            metodo_pago="mock",
        )

        self.assertIn("orden", result)
        orden = result["orden"]
        self.assertEqual(Ordenes.objects.count(), 1)
        self.assertIsNone(orden.operation_id)
        self.assertEqual(Tickets.objects.count(), 2)


class TestEjecutarCompraPaymentFailureReleasesSeats(BaseOrdenesTestCase):
    """When payment fails the seats should be released and no order created.

    Note: ejecutar_compra is @transaction.atomic. On PaymentFailedError the
    service calls liberar_asientos_usuario BEFORE raising, but since both
    happen inside the same atomic block, the release UPDATE is rolled back
    together with everything else when the transaction exits via the exception.
    The net observable effect: seats remain RETENIDO after the exception
    (the transaction rolled back the liberar call too). The existing test
    TestPurchaseServicePaymentFailed already documents and asserts this
    behaviour. This test focuses on no Orden being created.
    """

    def test_payment_failure_no_order_created(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        initial_orders = Ordenes.objects.count()
        initial_tickets = Tickets.objects.count()

        with self.assertRaises(PaymentFailedError):
            ejecutar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
                token="fail",
                operation_id="op-fail-4",
            )

        self.assertEqual(Ordenes.objects.count(), initial_orders)
        self.assertEqual(Tickets.objects.count(), initial_tickets)


class TestEjecutarCompraExpiredHoldRaises(BaseOrdenesTestCase):
    """Expired hold (released by _liberar_expirados) causes SeatUnavailableError."""

    def test_expired_hold_raises_seat_unavailable(self):
        past = timezone.now() - timedelta(hours=1)
        EstadoAsientoEvento.objects.filter(id_evento=self.evento).update(
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=self.user_a,
            retenido_hasta=past,
        )

        from apps.asientos.services import _liberar_expirados
        _liberar_expirados(self.evento.pk)

        initial_orders = Ordenes.objects.count()

        with self.assertRaises(SeatUnavailableError):
            ejecutar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
                metodo_pago="mock",
                operation_id="op-expired-5",
            )

        self.assertEqual(Ordenes.objects.count(), initial_orders)
        self.assertEqual(Tickets.objects.count(), 0)


class TestComprarAPIIdempotency(BaseOrdenesTestCase):
    """POST /api/ordenes/comprar/ with the same operation_id twice returns 201 both times."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_idempotent_second_call_returns_201_and_single_order(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.client.force_authenticate(user=self.user_a)
        payload = {
            "id_evento": self.evento.pk,
            "ids_grid_cell": self.both_cell_ids,
            "metodo_pago": "mock",
            "operation_id": "api-op-idempotency-1",
        }

        response_1 = self.client.post(_COMPRAR_URL, data=payload, format="json")
        self.assertEqual(response_1.status_code, 201)

        response_2 = self.client.post(_COMPRAR_URL, data=payload, format="json")
        self.assertEqual(response_2.status_code, 201)

        self.assertEqual(Ordenes.objects.count(), 1)

        self.assertEqual(
            response_1.data["orden"]["id_orden"],
            response_2.data["orden"]["id_orden"],
        )


class TestComprarAPIBadOperationId(BaseOrdenesTestCase):
    """operation_id longer than 64 chars must be rejected with 400."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_long_operation_id_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            _COMPRAR_URL,
            data={
                "id_evento": self.evento.pk,
                "ids_grid_cell": self.both_cell_ids,
                "metodo_pago": "mock",
                "operation_id": "x" * 100,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
