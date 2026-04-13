# Concurrency & Security Review

**Date:** 2026-04-10
**Reviewer:** QA + Concurrency agent
**Files reviewed:**
- `apps/asientos/services.py`
- `apps/asientos/views.py`
- `apps/asientos/urls.py`
- `apps/common/permissions.py`
- `apps/ordenes/views.py`
- `apps/ordenes/purchase.py`
- `apps/ordenes/payment.py`
- `config/urls.py`

---

## 1. Race Condition Vectors

### 1.1 Double-hold window (TOCTOU) — MEDIUM risk

**Location:** `apps/asientos/services.py` — `retener_asientos()`

**Description:**
`_liberar_expirados()` is called *before* `select_for_update()` locks the rows.
The sequence is:

```
1. UPDATE ... SET estado='disponible' WHERE retenido_hasta < now   ← not locked
2. SELECT ... FOR UPDATE WHERE id_grid_cell IN (...)               ← locked
```

Between steps 1 and 2, another transaction could read the newly-released rows as `disponible` and begin its own hold. Under SQLite this is serialised and invisible. Under PostgreSQL with `READ COMMITTED` isolation (the default), a concurrent transaction that started between step 1 and step 2 will see the rows as `disponible` and will race to acquire the lock.

**Actual impact:** The lock in step 2 ensures that only one transaction proceeds to `update()` at a time, so the final committed state is always consistent. However, two concurrent requests *can both pass the availability check* inside `_liberar_expirados` if they read the snapshot before either commits. The subsequent `select_for_update` then serialises the actual write, so only one wins. This is correct — but the expiry-release path happens outside the lock.

**Recommended fix:**
Move `_liberar_expirados` *inside* the locked query, or combine it with the `select_for_update` using a conditional update-and-read pattern. Alternatively, exclude expired rows from the lock-check instead of pre-releasing them:

```python
# Inside retener_asientos, replace the two-step pattern with:
estados = list(
    EstadoAsientoEvento.objects.select_for_update().filter(
        id_evento=id_evento,
        id_grid_cell__in=ids_grid_cell,
    )
)
ahora = timezone.now()
for estado in estados:
    # Treat expired holds as effectively DISPONIBLE
    effectively_available = (
        estado.estado == EstadoAsientoEvento.DISPONIBLE
        or (
            estado.estado == EstadoAsientoEvento.RETENIDO
            and estado.retenido_hasta
            and estado.retenido_hasta < ahora
        )
    )
    if not effectively_available:
        raise SeatUnavailableError(...)
```

This makes the expiry decision under the lock, eliminating the TOCTOU gap.

---

### 1.2 Dual select_for_update in ejecutar_compra + confirmar_compra — LOW risk

**Location:** `apps/ordenes/purchase.py` — `ejecutar_compra()`, and `apps/asientos/services.py` — `confirmar_compra()`

**Description:**
`ejecutar_compra` is `@transaction.atomic` and immediately issues a `select_for_update` on the seat rows (step 1). Later, inside the same transaction, it calls `confirmar_compra()`, which is *also* `@transaction.atomic` and issues its own `select_for_update` on the same rows.

Because both functions are inside the same atomic block (Django uses `SAVEPOINT` for nested atomics), the second lock acquisition is redundant but not harmful — PostgreSQL will grant it immediately to the same transaction. Under SQLite the locking model is coarser and behaves identically.

**Recommended fix:**
Extract a `_confirmar_compra_inner(estados)` variant that accepts already-locked estado rows and skips the re-query. Call that from `ejecutar_compra` to avoid the redundant round-trip. The public `confirmar_compra()` can remain unchanged for callers that do their own locking.

---

### 1.3 Duplicate submission (idempotency) — MEDIUM risk

**Location:** `apps/ordenes/purchase.py` — `ejecutar_compra()`

**Description:**
No idempotency key or duplicate-submission guard exists. If a client double-submits (network retry, button double-click, browser back-navigation), and both requests reach the server before the first transaction commits:

- The first request passes the seat-held check and proceeds to payment.
- The second request *also* passes the seat-held check (seats are still `RETENIDO`, not yet `VENDIDO`).
- Whichever request reaches `select_for_update` second blocks until the first commits.
- After the first commits (seats become `VENDIDO`), the second fails at the `select_for_update` check in `ejecutar_compra` (it filters `estado=RETENIDO`, which no longer matches) → raises `SeatUnavailableError`. ✓

**Conclusion:** The current design handles double-submission correctly at the seat-state level. However, if a duplicate slips in between the order-creation (`crear_orden`) and the seat-confirmation step (`confirmar_compra`), the payment gateway (`procesar_pago`) would be charged twice. The mock gateway has no de-duplication logic.

**Recommended fix:**
Pass an idempotency key (e.g., `f"{usuario.pk}:{id_evento}:{sorted(ids_grid_cell)}"`) to the payment gateway. Store it on the `Ordenes` row and check for duplicates before charging.

---

### 1.4 Payment-before-commit gap — LOW risk

**Location:** `apps/ordenes/purchase.py` — `ejecutar_compra()`, steps 4–7

**Description:**
`procesar_pago()` (the external gateway call) is executed *inside* the `@transaction.atomic` block. If the DB commit fails after a successful payment (e.g., the process is killed), the payment is processed but no order is created, and the seats are not marked `VENDIDO`.

**Recommended fix:**
Move the gateway call *outside* the atomic block:
1. Validate seats (under lock) in a first atomic block.
2. Call `procesar_pago()` outside any transaction.
3. Create order + tickets + confirm seats in a second atomic block.
4. If step 3 fails after a successful payment, emit a reconciliation event to a queue.

---

### 1.5 Availability endpoint — no auth, no rate limiting

**Location:** `apps/asientos/views.py` — `DisponibilidadAsientosView`

**Description:**
`GET /api/asientos/disponibilidad/<id_evento>/` is `AllowAny`. Each call triggers `inicializar_estado_asientos` (a `bulk_create`) and `_liberar_expirados` (an `UPDATE`). Under high traffic, this endpoint can become a write-amplification vector and introduce lock contention on the `estado_asiento_evento` table.

**Recommended fix:**
- Cache the response with a short TTL (e.g., 5–10 seconds).
- Move `inicializar_estado_asientos` to the event publish workflow rather than lazy-initialising on every availability request.

---

## 2. select_for_update Usage

| Function | Uses select_for_update | Scope |
|---|---|---|
| `retener_asientos` | Yes | Correct — covers the read-check-write cycle |
| `confirmar_compra` | Yes | Correct — prevents concurrent confirmation |
| `liberar_asientos_usuario` | No | Acceptable — `UPDATE` on a single user's rows; contention is low |
| `_liberar_expirados` | No | Gap — see §1.1 |
| `ejecutar_compra` (step 1) | Yes | Correct — re-validates hold before payment |
| `obtener_disponibilidad_evento` | No | Acceptable for a read-only query |

**Assessment:** `select_for_update` is applied at the two highest-risk mutation points (`retener_asientos`, `confirmar_compra`). The main gap is that `_liberar_expirados` modifies rows it has not locked.

---

## 3. Transaction Boundary Correctness

### retener_asientos — CORRECT

```python
@transaction.atomic
def retener_asientos(...):
    _liberar_expirados(id_evento)       # UPDATE (unlocked) — gap §1.1
    estados = select_for_update(...)    # lock acquired
    # check availability
    .update(estado=RETENIDO, ...)       # write under lock
```

The atomic decorator ensures the lock and write are one unit. No partial state is possible once the transaction commits.

### confirmar_compra — CORRECT

```python
@transaction.atomic
def confirmar_compra(...):
    estados = select_for_update(..., estado=RETENIDO, retenido_por=usuario)
    if len(estados) != len(ids_grid_cell): raise SeatUnavailableError
    .update(estado=VENDIDO)
```

The filter `estado=RETENIDO, retenido_por=usuario` is the exact guard needed. If a concurrent transaction already confirmed or expired the hold, the count will not match and the error is raised.

### ejecutar_compra — MOSTLY CORRECT, one concern

```python
@transaction.atomic
def ejecutar_compra(...):
    # 1. select_for_update (re-validate hold)
    # 2. load evento + cells
    # 3. calculate total
    # 4. procesar_pago()            ← external I/O inside transaction (§1.4)
    # 5. crear_orden()
    # 6. Tickets.objects.create()
    # 7. confirmar_compra()         ← nested atomic (SAVEPOINT)
```

The nested `confirmar_compra` runs inside a SAVEPOINT. If it raises, the SAVEPOINT is rolled back but the outer transaction can still commit (unless the exception propagates, which it currently does). This is the correct Django behaviour — the exception will bubble up and the full outer atomic block will be rolled back too.

**The critical issue** is that `procesar_pago()` makes an external HTTP call inside the transaction (§1.4), holding the DB connection and seat locks for the full duration of the gateway round-trip. This blocks other transactions from acquiring the same seat locks during that window.

---

## 4. Duplicate Submission Prevention

| Vector | Prevented? | Mechanism |
|---|---|---|
| Double-click / UI double-submit | Yes | `select_for_update` in `ejecutar_compra` ensures the second request blocks and then fails the seat-state check after the first commits |
| Network retry after 5xx | Partial | If the first request succeeded but the client timed out, a retry will fail at the seat check (seats are VENDIDO). No order duplication occurs. |
| Concurrent requests from two devices | Yes | Same `select_for_update` serialisation |
| Payment gateway retry / webhook | Not applicable | Mock gateway has no webhook |

**Gap:** There is no HTTP-level idempotency key (e.g., an `X-Idempotency-Key` header) stored on the `Ordenes` table. For production payment integration, this is essential.

---

## 5. Route / Access Protection Audit

### Seat endpoints (`apps/asientos/urls.py`)

| Endpoint | Method | Permission | Assessment |
|---|---|---|---|
| `/api/asientos/disponibilidad/<id>/` | GET | `AllowAny` | Intentional (public availability). See §1.5 for write-amplification risk. |
| `/api/asientos/retener/` | POST | `IsAuthenticated` | Correct. |
| `/api/asientos/liberar/` | POST | `IsAuthenticated` | Correct. |
| `/api/asientos/confirmar/` | POST | `IsAuthenticated` | Correct. |
| `/api/asientos/` (CRUD list/retrieve) | GET | `IsAuthenticated` | Correct. |
| `/api/asientos/` (CRUD create/update/delete) | POST/PUT/DELETE | `IsOrganizador` | Correct. |

**Gap:** `liberar_asientos_usuario` releases *all* seats held by the authenticated user for an event. There is no check that the seats belong to the user performing the request beyond the `retenido_por=request.user` filter in the service. This is correct but should be documented as the authorisation model.

### Order endpoints (`apps/ordenes/urls.py`)

| Endpoint | Method | Permission | Assessment |
|---|---|---|---|
| `/api/ordenes/` | GET (list) | `IsAuthenticated` | **GAP**: Returns ALL orders for any authenticated user. Should be scoped to the requesting user unless the caller is admin. |
| `/api/ordenes/<pk>/` | GET (retrieve) | `IsAuthenticated` | **GAP**: Any authenticated user can retrieve any order by PK. Should check `id_usuario == request.user`. |
| `/api/ordenes/` | POST (create) | `IsAuthenticated` | Acceptable — creates for `id_usuario=request.user` via service. |
| `/api/ordenes/<pk>/` | PUT/PATCH | `IsAdmin` | Correct. |
| `/api/ordenes/<pk>/` | DELETE | `IsAdmin` | Correct. |

### IsOrganizador permission

**Location:** `apps/common/permissions.py`

```python
class IsOrganizador(BasePermission):
    def has_permission(self, request, view):
        rol = request.user.id_rol.nombre.lower()
        return rol in ("admin", "organizador", "cliente")
```

**Issue:** Every authenticated `cliente` has the same write permissions as an `organizador` on the `Asientos` CRUD endpoints (create/update/delete physical seat definitions). This appears to be an over-broad permission grant. If clients should only be able to *hold/release/confirm* seats — not edit the physical layout — `IsOrganizador` should be renamed and restricted to `("admin", "organizador")`.

### Missing /comprar/ endpoint

**Location:** `apps/ordenes/purchase.py` — `ejecutar_compra()` exists but is not wired to any URL or view.

**Impact:** The full purchase orchestration flow (hold → pay → order + tickets → confirm) has no HTTP entry point. Clients must call `POST /api/asientos/retener/` followed by `POST /api/asientos/confirmar/` separately, which does not create an order or tickets. The actual business flow is incomplete.

**Required work:**
1. Add `ComprarView(APIView)` in `apps/ordenes/views.py` that calls `ejecutar_compra` and returns `{ orden, tickets }`.
2. Register `path('ordenes/comprar/', ComprarView.as_view(), name='ordenes-comprar')` in `apps/ordenes/urls.py` *before* the router URLs.
3. Permission: `IsAuthenticated`.
4. Catch `SeatUnavailableError` → 409, `PaymentFailedError` → 402.

---

## 6. Summary of Issues by Priority

| Priority | Issue | Location | Fix |
|---|---|---|---|
| **HIGH** | `/api/ordenes/comprar/` does not exist — purchase orchestration has no HTTP entry point | `apps/ordenes/views.py`, `apps/ordenes/urls.py` | Wire `ejecutar_compra` into a view |
| **HIGH** | All authenticated users can list and retrieve any order (IDOR) | `apps/ordenes/views.py` `list`, `retrieve` | Scope queryset to `id_usuario=request.user` for non-admins |
| **MEDIUM** | `_liberar_expirados` runs before the `select_for_update` lock (TOCTOU gap) | `apps/asientos/services.py` `retener_asientos` | Inline expiry check under the lock |
| **MEDIUM** | Payment gateway call inside `@transaction.atomic` holds seat locks for the gateway round-trip | `apps/ordenes/purchase.py` | Move payment call outside the transaction |
| **MEDIUM** | No idempotency key on orders | `apps/ordenes/models.py`, `purchase.py` | Add `idempotency_key` field + pre-charge check |
| **MEDIUM** | `IsOrganizador` grants write access to seat layout for `cliente` role | `apps/common/permissions.py` | Restrict to `("admin", "organizador")` |
| **LOW** | `DisponibilidadAsientosView` is `AllowAny` with lazy `bulk_create` on every request | `apps/asientos/views.py` | Cache response, move init to publish workflow |
| **LOW** | Redundant nested `select_for_update` in `ejecutar_compra` → `confirmar_compra` | `apps/ordenes/purchase.py` | Pass pre-locked estado rows to inner function |
