import threading
from datetime import timedelta
from unittest import skipIf

from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.roles.models import Roles
from apps.usuarios.models import Usuarios
from apps.lugares.models import Lugares
from apps.layouts.models import Layouts
from apps.zonas.models import Zonas
from apps.grid_cells.models import GridCells
from apps.eventos.models import Eventos
from apps.asientos.models import EstadoAsientoEvento
from apps.asientos.services import (
    retener_asientos,
    confirmar_compra,
    liberar_asientos_usuario,
    obtener_disponibilidad_evento,
    inicializar_estado_asientos,
    SeatUnavailableError,
)


def _make_usuario(rol, suffix=""):
    now = timezone.now()
    return Usuarios.objects.create(
        nombre=f"Test{suffix}",
        apellidos="User",
        correo=f"test{suffix}@example.com",
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
        nombre="Test Event",
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



class BaseAsientosTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.rol_cliente = Roles.objects.create(nombre="cliente")
        cls.rol_admin = Roles.objects.create(nombre="admin")

        cls.user_a = _make_usuario(cls.rol_cliente, suffix="_a")
        cls.user_b = _make_usuario(cls.rol_cliente, suffix="_b")

        now = timezone.now()
        cls.lugar = Lugares.objects.create(
            nombre="Venue Test",
            ciudad="CDMX",
            pais="Mexico",
            direccion="Calle 1",
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
            nombre="General",
            color="#FF0000",
            fecha_creacion=now,
            fecha_modificacion=now,
            id_layout=cls.layout,
        )

        cls.cell_1 = GridCells.objects.create(
            tipo="ZONA DE ASIENTOS",
            row=0,
            col=0,
            id_zona=cls.zona,
            id_layout=cls.layout,
        )
        cls.cell_2 = GridCells.objects.create(
            tipo="ZONA DE ASIENTOS",
            row=0,
            col=1,
            id_zona=cls.zona,
            id_layout=cls.layout,
        )

        cls.evento = _make_evento(cls.lugar, cls.layout, tiempo_espera=10)

    def setUp(self):
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


class TestRetenerAsientosSuccess(BaseAsientosTestCase):
    """Happy path: hold two available seats."""

    def test_retener_asientos_success(self):
        estados = retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.assertIsInstance(estados, dict)
        self.assertIn("retenido_hasta", estados)
        self.assertIn("ids_grid_cell", estados)
        self.assertEqual(len(estados["ids_grid_cell"]), 2)
        self.assertIsNotNone(estados["retenido_hasta"])
        from datetime import datetime
        parsed = datetime.fromisoformat(estados["retenido_hasta"])
        self.assertGreater(parsed, timezone.now() - timedelta(seconds=5))

        db_estados = EstadoAsientoEvento.objects.filter(id_evento=self.evento)
        for e in db_estados:
            self.assertEqual(e.estado, EstadoAsientoEvento.RETENIDO)
            self.assertEqual(e.retenido_por_id, self.user_a.pk)
            self.assertIsNotNone(e.retenido_hasta)
            expected_expiry = timezone.now() + timedelta(minutes=self.evento.tiempo_espera)
            delta = abs((e.retenido_hasta - expected_expiry).total_seconds())
            self.assertLess(delta, 5, "Hold expiry should be ~tiempo_espera minutes from now")


class TestRetenerAsientosAlreadyHeld(BaseAsientosTestCase):
    """user_b cannot hold seats already held by user_a."""

    def test_retener_asientos_already_held(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        with self.assertRaises(SeatUnavailableError):
            retener_asientos(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_b,
            )

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.retenido_por_id, self.user_a.pk)


class TestConfirmarCompraSuccess(BaseAsientosTestCase):

    def test_confirmar_compra_success(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        confirmar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.VENDIDO)


class TestConfirmarCompraExpired(BaseAsientosTestCase):

    def test_confirmar_compra_expired(self):
        ahora = timezone.now()
        EstadoAsientoEvento.objects.filter(id_evento=self.evento).update(
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=self.user_a,
            retenido_hasta=ahora - timedelta(seconds=1),
        )

        EstadoAsientoEvento.objects.filter(
            id_evento=self.evento,
            retenido_hasta__lt=timezone.now(),
        ).update(
            estado=EstadoAsientoEvento.DISPONIBLE,
            retenido_por=None,
            retenido_hasta=None,
        )

        with self.assertRaises(SeatUnavailableError):
            confirmar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
            )


class TestConfirmarCompraWrongUser(BaseAsientosTestCase):

    def test_confirmar_compra_wrong_user(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        with self.assertRaises(SeatUnavailableError):
            confirmar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_b,
            )

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.RETENIDO)
            self.assertEqual(e.retenido_por_id, self.user_a.pk)


class TestLiberarExpirados(BaseAsientosTestCase):
    def test_liberar_expirados(self):
        past = timezone.now() - timedelta(hours=1)
        EstadoAsientoEvento.objects.filter(id_evento=self.evento).update(
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=self.user_a,
            retenido_hasta=past,
        )

        disponibilidad = list(obtener_disponibilidad_evento(self.evento.pk))

        for row in disponibilidad:
            self.assertEqual(row["estado"], EstadoAsientoEvento.DISPONIBLE)

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.DISPONIBLE)
            self.assertIsNone(e.retenido_por_id)
            self.assertIsNone(e.retenido_hasta)


class TestDuplicateConfirmation(BaseAsientosTestCase):

    def test_duplicate_confirmation(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        confirmar_compra(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        with self.assertRaises(SeatUnavailableError):
            confirmar_compra(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_a,
            )

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.VENDIDO)

class TestRetenerAsientosAPI(BaseAsientosTestCase):

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_retener_api_unauthenticated_returns_401(self):
        """Unauthenticated requests must be rejected."""
        response = self.client.post(
            "/api/asientos/retener/",
            data={"id_evento": self.evento.pk, "ids_grid_cell": self.both_cell_ids},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_retener_api_success_returns_200(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/asientos/retener/",
            data={"id_evento": self.evento.pk, "ids_grid_cell": self.both_cell_ids},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("retenido_hasta", response.data)
        self.assertIn("ids_grid_cell", response.data)
        self.assertIsNotNone(response.data["retenido_hasta"])
        self.assertIsInstance(response.data["ids_grid_cell"], list)
        self.assertEqual(len(response.data["ids_grid_cell"]), 2)

    def test_retener_api_conflict_returns_409(self):
        """Trying to hold seats already held returns 409 Conflict."""
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.client.force_authenticate(user=self.user_b)
        response = self.client.post(
            "/api/asientos/retener/",
            data={"id_evento": self.evento.pk, "ids_grid_cell": self.both_cell_ids},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_retener_api_missing_fields_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/asientos/retener/",
            data={}, 
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class TestConfirmarCompraAPI(BaseAsientosTestCase):
    """POST /api/asientos/confirmar/ HTTP layer tests."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_confirmar_api_unauthenticated_returns_401(self):
        response = self.client.post(
            "/api/asientos/confirmar/",
            data={"id_evento": self.evento.pk, "ids_grid_cell": self.both_cell_ids},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_confirmar_api_success_returns_200(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/asientos/confirmar/",
            data={"id_evento": self.evento.pk, "ids_grid_cell": self.both_cell_ids},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_confirmar_api_conflict_when_not_held(self):
        """Seats that are DISPONIBLE (not held) cannot be confirmed."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/asientos/confirmar/",
            data={"id_evento": self.evento.pk, "ids_grid_cell": self.both_cell_ids},
            format="json",
        )
        self.assertEqual(response.status_code, 409)


class TestLiberarAsientosAPI(BaseAsientosTestCase):
    """POST /api/asientos/liberar/ HTTP layer tests."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_liberar_api_unauthenticated_returns_401(self):
        response = self.client.post(
            "/api/asientos/liberar/",
            data={"id_evento": self.evento.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_liberar_api_releases_user_seats(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/asientos/liberar/",
            data={"id_evento": self.evento.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.DISPONIBLE)


class TestDisponibilidadAPI(BaseAsientosTestCase):
    """GET /api/asientos/disponibilidad/<id_evento>/ — no auth required."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_disponibilidad_returns_200_unauthenticated(self):
        response = self.client.get(
            f"/api/asientos/disponibilidad/{self.evento.pk}/",
        )
        self.assertEqual(response.status_code, 200)

    def test_disponibilidad_shows_correct_states(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=[self.cell_1.pk],
            usuario=self.user_a,
        )

        response = self.client.get(
            f"/api/asientos/disponibilidad/{self.evento.pk}/",
        )
        self.assertEqual(response.status_code, 200)
        cell_key = "id_grid_cell_id" if "id_grid_cell_id" in response.data[0] else "id_grid_cell"
        estados_map = {row[cell_key]: row["estado"] for row in response.data}
        self.assertEqual(estados_map[self.cell_1.pk], EstadoAsientoEvento.RETENIDO)
        self.assertEqual(estados_map[self.cell_2.pk], EstadoAsientoEvento.DISPONIBLE)

    def test_disponibilidad_404_for_nonexistent_event(self):
        response = self.client.get("/api/asientos/disponibilidad/999999/")
        self.assertEqual(response.status_code, 404)


class TestConcurrentHoldAttempts(TransactionTestCase):
    """
    Two threads simultaneously try to hold the same seats.
    Exactly one must succeed and one must raise SeatUnavailableError.

    Uses TransactionTestCase so data is committed and visible to threads.
    Skipped on SQLite (no real row locking).
    """

    def setUp(self):
        """Create all fixture data in a real committed transaction."""
        from apps.roles.models import Roles
        from apps.usuarios.models import Usuarios
        from apps.lugares.models import Lugares
        from apps.layouts.models import Layouts
        from apps.zonas.models import Zonas
        from apps.grid_cells.models import GridCells
        from apps.eventos.models import Eventos

        now = timezone.now()
        role = Roles.objects.create(nombre="cliente")
        self.user_a = Usuarios.objects.create(
            nombre="ConcA", correo="conca@test.com", contrasena="x",
            fecha_nacimiento="2000-01-01", estatus="activo",
            fecha_creacion=now, fecha_actualizacion=now, id_rol=role,
        )
        self.user_b = Usuarios.objects.create(
            nombre="ConcB", correo="concb@test.com", contrasena="x",
            fecha_nacimiento="2000-01-01", estatus="activo",
            fecha_creacion=now, fecha_actualizacion=now, id_rol=role,
        )
        lugar = Lugares.objects.create(
            nombre="ConcVenue", ciudad="X", pais="X", direccion="X",
            estatus="PUBLICADO", fecha_creacion=now, fecha_actualizacion=now,
            id_dueno=self.user_a,
        )
        layout = Layouts.objects.create(
            grid_rows=5, grid_cols=5, version=1, estatus="PUBLICADO",
            id_lugar=lugar, id_dueno=self.user_a,
        )
        zona = Zonas.objects.create(
            nombre="ConcZone", color="#fff",
            fecha_creacion=now, fecha_modificacion=now, id_layout=layout,
        )
        self.cell_a = GridCells.objects.create(tipo="ZONA DE ASIENTOS", row=0, col=0, id_zona=zona, id_layout=layout)
        self.cell_b = GridCells.objects.create(tipo="ZONA DE ASIENTOS", row=0, col=1, id_zona=zona, id_layout=layout)
        self.both_cell_ids = [self.cell_a.pk, self.cell_b.pk]
        self.evento = Eventos.objects.create(
            nombre="ConcEvt", fecha_inicio=now, fecha_fin=now + timedelta(days=1),
            tiempo_espera=15, estatus="PUBLICADO",
            fecha_creacion=now, fecha_actualizacion=now,
            id_lugar=lugar, id_version=layout,
        )
        from apps.asientos.services import inicializar_estado_asientos
        inicializar_estado_asientos(self.evento.pk, layout.pk)

    def test_only_one_concurrent_hold_succeeds(self):
        if connection.vendor == "sqlite":
            self.skipTest("SQLite does not support concurrent select_for_update")

        import django
        django.db.connections.close_all()

        results = []
        errors = []

        def attempt_hold(user):
            try:
                retener_asientos(
                    id_evento=self.evento.pk,
                    ids_grid_cell=self.both_cell_ids,
                    usuario=user,
                )
                results.append(user.pk)
            except SeatUnavailableError:
                errors.append(user.pk)
            except Exception as exc:
                errors.append(f"unexpected:{exc}")
            finally:
                django.db.connections.close_all()

        t1 = threading.Thread(target=attempt_hold, args=(self.user_a,))
        t2 = threading.Thread(target=attempt_hold, args=(self.user_b,))

        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        self.assertEqual(len(results), 1, f"Expected 1 success, got results={results} errors={errors}")
        self.assertEqual(len(errors), 1)

        held_by = set(
            EstadoAsientoEvento.objects.filter(
                id_evento=self.evento,
                estado=EstadoAsientoEvento.RETENIDO,
            ).values_list("retenido_por_id", flat=True)
        )
        self.assertEqual(len(held_by), 1)
        self.assertIn(list(held_by)[0], [self.user_a.pk, self.user_b.pk])


class TestRetenerAsientosExtendByOwner(BaseAsientosTestCase):
    """user_a holds cell_1, then extends to hold cell_1 + cell_2. Must succeed."""

    def test_extend_hold_adds_cells(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=[self.cell_1.pk],
            usuario=self.user_a,
        )

        result = retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result["ids_grid_cell"]), 2)
        self.assertIsNotNone(result["retenido_hasta"])

        for e in EstadoAsientoEvento.objects.filter(id_evento=self.evento):
            self.assertEqual(e.estado, EstadoAsientoEvento.RETENIDO)
            self.assertEqual(e.retenido_por_id, self.user_a.pk)
            self.assertIsNotNone(e.retenido_hasta)


class TestRetenerAsientosReduceByOwner(BaseAsientosTestCase):
    """user_a holds both cells, then reduces to cell_1 only. cell_2 must be released."""

    def test_reduce_hold_releases_deselected_cell(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        result = retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=[self.cell_1.pk],
            usuario=self.user_a,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["ids_grid_cell"], [self.cell_1.pk])

        estado_1 = EstadoAsientoEvento.objects.get(
            id_evento=self.evento, id_grid_cell=self.cell_1
        )
        self.assertEqual(estado_1.estado, EstadoAsientoEvento.RETENIDO)
        self.assertEqual(estado_1.retenido_por_id, self.user_a.pk)

        estado_2 = EstadoAsientoEvento.objects.get(
            id_evento=self.evento, id_grid_cell=self.cell_2
        )
        self.assertEqual(estado_2.estado, EstadoAsientoEvento.DISPONIBLE)
        self.assertIsNone(estado_2.retenido_por_id)
        self.assertIsNone(estado_2.retenido_hasta)


class TestRetenerAsientosOtherUserStillBlocks(BaseAsientosTestCase):
    """user_a holds cell_1. user_b tries cell_1 + cell_2. Must raise; neither cell changes owner."""

    def test_other_user_hold_raises_and_does_not_partially_commit(self):
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=[self.cell_1.pk],
            usuario=self.user_a,
        )

        with self.assertRaises(SeatUnavailableError):
            retener_asientos(
                id_evento=self.evento.pk,
                ids_grid_cell=self.both_cell_ids,
                usuario=self.user_b,
            )

        estado_1 = EstadoAsientoEvento.objects.get(
            id_evento=self.evento, id_grid_cell=self.cell_1
        )
        self.assertEqual(estado_1.estado, EstadoAsientoEvento.RETENIDO)
        self.assertEqual(estado_1.retenido_por_id, self.user_a.pk)

        estado_2 = EstadoAsientoEvento.objects.get(
            id_evento=self.evento, id_grid_cell=self.cell_2
        )
        self.assertEqual(estado_2.estado, EstadoAsientoEvento.DISPONIBLE)
        self.assertIsNone(estado_2.retenido_por_id)


class TestHoldStatusAPI(BaseAsientosTestCase):
    """GET /api/asientos/hold-status/<id_evento>/ — authentication + response shape."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f"/api/asientos/hold-status/{self.evento.pk}/"

    def test_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_no_hold_returns_empty_response(self):
        """Authenticated user with no active hold gets an empty payload."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["tiene_retencion"])
        self.assertIsNone(response.data["retenido_hasta"])
        self.assertEqual(response.data["ids_grid_cell"], [])

    def test_active_hold_returns_cells_and_expiry(self):
        """After holding seats, hold-status reflects them."""
        retener_asientos(
            id_evento=self.evento.pk,
            ids_grid_cell=self.both_cell_ids,
            usuario=self.user_a,
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["tiene_retencion"])
        self.assertIsNotNone(response.data["retenido_hasta"])
        returned_cells = set(response.data["ids_grid_cell"])
        self.assertEqual(returned_cells, set(self.both_cell_ids))
        from datetime import datetime
        parsed = datetime.fromisoformat(response.data["retenido_hasta"])
        self.assertGreater(parsed, timezone.now() - timedelta(seconds=5))

    def test_expired_hold_auto_released_returns_empty(self):
        """Hold with a past expiry is auto-released by _liberar_expirados on GET."""
        past = timezone.now() - timedelta(hours=1)
        EstadoAsientoEvento.objects.filter(id_evento=self.evento).update(
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=self.user_a,
            retenido_hasta=past,
        )

        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["tiene_retencion"])
        self.assertIsNone(response.data["retenido_hasta"])
        self.assertEqual(response.data["ids_grid_cell"], [])


class TestRetenerAsientosAPIResponseShape(BaseAsientosTestCase):
    """POST /api/asientos/retener/ must return retenido_hasta and ids_grid_cell."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_retener_response_has_retenido_hasta_and_ids_grid_cell(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/asientos/retener/",
            data={"id_evento": self.evento.pk, "ids_grid_cell": self.both_cell_ids},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.assertIn("retenido_hasta", response.data)
        self.assertIn("ids_grid_cell", response.data)
        self.assertIsNotNone(response.data["retenido_hasta"])
        self.assertIsInstance(response.data["ids_grid_cell"], list)
        self.assertEqual(len(response.data["ids_grid_cell"]), 2)

        from datetime import datetime
        parsed = datetime.fromisoformat(response.data["retenido_hasta"])
        self.assertGreater(parsed, timezone.now() - timedelta(seconds=5))
