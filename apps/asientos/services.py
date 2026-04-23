from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Asientos, EstadoAsientoEvento
from apps.auditoria_logs.services import registrar_auditoria


class SeatUnavailableError(Exception):
    pass


def _safe_number(value, fallback=0):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return fallback
    return n if n == n else fallback


def _to_grid_index(value, spacing=32):
    return max(0, int(round(_safe_number(value, 0) / spacing)))


def _build_cells_from_layout_snapshot(layout):
    layout_data = getattr(layout, 'layout_data', None) or {}
    sections = layout_data.get('sections') or []
    elements = layout_data.get('elements') or []
    zones = layout_data.get('zones') or []

    from apps.zonas.models import Zonas

    backend_zones = list(Zonas.objects.filter(id_layout=layout.id_layout).values('id_zona', 'nombre'))
    backend_by_name = {
        str(z['nombre']).strip().lower(): z['id_zona']
        for z in backend_zones
        if z.get('nombre')
    }

    zone_local_to_backend = {}
    for zone in zones:
        local_id = zone.get('id')
        backend_id = zone.get('idBackend', zone.get('id_zona'))
        if backend_id is None and zone.get('nombre'):
            backend_id = backend_by_name.get(str(zone['nombre']).strip().lower())
        if local_id is not None:
            zone_local_to_backend[str(local_id)] = backend_id

    def resolve_zone_backend_id(section_zone_id):
        if section_zone_id is None:
            return None
        if str(section_zone_id) in zone_local_to_backend:
            return zone_local_to_backend[str(section_zone_id)]
        try:
            return int(section_zone_id)
        except (TypeError, ValueError):
            return None

    cells = []
    seen = set()

    for section in sections:
        start_row = _to_grid_index(section.get('y', 0))
        start_col = _to_grid_index(section.get('x', 0))
        zone_id = resolve_zone_backend_id(section.get('zoneId'))

        for row_idx, row in enumerate(section.get('rows') or []):
            for seat_idx, _seat in enumerate(row.get('seats') or []):
                key = ('ZONA DE ASIENTOS', start_row + row_idx, start_col + seat_idx, zone_id)
                if key in seen:
                    continue
                seen.add(key)
                cells.append({
                    'tipo': 'ZONA DE ASIENTOS',
                    'row': start_row + row_idx,
                    'col': start_col + seat_idx,
                    'id_zona': zone_id,
                })

    for element in elements:
        element_type = str(element.get('type', '')).strip().lower()
        tipo = 'PASILLO' if element_type == 'aisle' else 'ESCENARIO'
        start_row = _to_grid_index(element.get('y', 0))
        start_col = _to_grid_index(element.get('x', 0))
        width = max(1, int(round(_safe_number(element.get('width', 32), 32) / 32)))
        height = max(1, int(round(_safe_number(element.get('height', 32), 32) / 32)))

        for r in range(height):
            for c in range(width):
                key = (tipo, start_row + r, start_col + c, None)
                if key in seen:
                    continue
                seen.add(key)
                cells.append({
                    'tipo': tipo,
                    'row': start_row + r,
                    'col': start_col + c,
                    'id_zona': None,
                })

    return cells


def _resolve_layout_snapshot_seat_positions(layout):
    """Extrae lista de posiciones de asientos desde layout_data sin depender de grid_cells.
    Retorna: [(row, col, zone_id, seat_label), ...]
    """
    layout_data = getattr(layout, 'layout_data', None) or {}
    sections = layout_data.get('sections') or []
    zones = layout_data.get('zones') or []

    from apps.zonas.models import Zonas

    backend_zones = list(Zonas.objects.filter(id_layout=layout.id_layout).values('id_zona', 'nombre'))
    backend_by_name = {
        str(z['nombre']).strip().lower(): z['id_zona']
        for z in backend_zones
        if z.get('nombre')
    }

    zone_local_to_backend = {}
    for zone in zones:
        local_id = zone.get('id')
        backend_id = zone.get('idBackend', zone.get('id_zona'))
        if backend_id is None and zone.get('nombre'):
            backend_id = backend_by_name.get(str(zone['nombre']).strip().lower())
        if local_id is not None:
            zone_local_to_backend[str(local_id)] = backend_id

    def resolve_zone_backend_id(section_zone_id):
        if section_zone_id is None:
            return None
        if str(section_zone_id) in zone_local_to_backend:
            return zone_local_to_backend[str(section_zone_id)]
        try:
            return int(section_zone_id)
        except (TypeError, ValueError):
            return None

    positions = []
    for section in sections:
        start_row = _to_grid_index(section.get('y', 0))
        start_col = _to_grid_index(section.get('x', 0))
        zone_id = resolve_zone_backend_id(section.get('zoneId'))

        for row_idx, row in enumerate(section.get('rows') or []):
            row_label = row.get('label') or chr(65 + row_idx)  # A, B, C...
            for seat_idx, seat in enumerate(row.get('seats') or []):
                seat_label = seat.get('label') or str(seat_idx + 1)  # 1, 2, 3...
                positions.append((
                    start_row + row_idx,
                    start_col + seat_idx,
                    zone_id,
                    f"{row_label}{seat_label}",
                ))

    return positions


def ensure_layout_grid_cells_from_snapshot(layout_id):
    """Sincroniza grid_cells desde layout_data usando upsert (get_or_create).
    Preserva IDs existentes para mantener integridad de FK en EstadoAsientoEvento.
    """
    from apps.layouts.models import Layouts
    from apps.grid_cells.models import GridCells

    try:
        layout = Layouts.objects.get(pk=layout_id)
    except Layouts.DoesNotExist:
        return 0

    cells = _build_cells_from_layout_snapshot(layout)
    if not cells:
        return 0

    # Upsert: get_or_create preserva IDs existentes (no rompe FK de EstadoAsientoEvento)
    for cell in cells:
        GridCells.objects.get_or_create(
            tipo=cell['tipo'],
            row=cell['row'],
            col=cell['col'],
            id_zona_id=cell.get('id_zona'),
            id_layout_id=layout_id,
        )

    return len(cells)


def build_layout_seat_key(row, col, zone_id):
    zone = 0 if zone_id is None else int(zone_id)
    return f"{int(row)}:{int(col)}:{zone}"


def resolve_layout_seat_refs_to_grid_cells(id_evento, asientos_layout):
    """Resuelve referencias de asientos del layout directamente desde layout_data.
    Retorna IDs de grid_cells (reales si existen, creados si faltan).
    """
    from apps.eventos.models import Eventos
    from apps.layouts.models import Layouts
    from apps.grid_cells.models import GridCells

    evento = Eventos.objects.select_related('id_version').get(pk=id_evento)
    layout_id = evento.id_version_id
    layout = Layouts.objects.get(pk=layout_id)

    refs = asientos_layout or []
    if not isinstance(refs, list) or len(refs) == 0:
        raise SeatUnavailableError("Se requiere una lista no vacía de asientos del layout.")

    parsed = []
    for ref in refs:
        if not isinstance(ref, dict):
            raise SeatUnavailableError("Formato inválido en asientos_layout.")

        row = ref.get('row')
        col = ref.get('col')
        zone_id = ref.get('zone_id', ref.get('zoneId', ref.get('id_zona')))

        if row is None or col is None:
            raise SeatUnavailableError("Cada asiento del layout debe incluir row y col.")

        try:
            parsed.append((int(row), int(col), None if zone_id is None else int(zone_id)))
        except (TypeError, ValueError):
            raise SeatUnavailableError("row, col y zone_id deben ser números válidos.")

    snapshot_positions = _resolve_layout_snapshot_seat_positions(layout)
    snapshot_by_key = {(r, c, z): label for r, c, z, label in snapshot_positions}

    resolved_grid_cell_ids = []
    seen = set()

    for row, col, zone_id in parsed:
        key = (row, col, zone_id)
        if key not in snapshot_by_key:
            candidates = [pos for pos in snapshot_positions if pos[0] == row and pos[1] == col]
            if len(candidates) == 0:
                raise SeatUnavailableError(
                    f"El asiento (F{row+1}C{col+1}) no existe en el layout del evento."
                )
            if zone_id is None and len(candidates) == 1:
                row, col, zone_id, _ = candidates[0]
                key = (row, col, zone_id)
            else:
                raise SeatUnavailableError(
                    f"El asiento (F{row+1}C{col+1}) es ambiguo o no existe."
                )

        if key in seen:
            continue
        seen.add(key)

        grid_cell = GridCells.objects.filter(
            id_layout_id=layout_id,
            row=row,
            col=col,
            id_zona_id=zone_id,
            tipo='ZONA DE ASIENTOS',
        ).first()

        if grid_cell:
            resolved_grid_cell_ids.append(grid_cell.id_grid_cells)
        else:
            grid_cell = GridCells.objects.create(
                tipo='ZONA DE ASIENTOS',
                row=row,
                col=col,
                id_zona_id=zone_id,
                id_layout_id=layout_id,
            )
            resolved_grid_cell_ids.append(grid_cell.id_grid_cells)

    return resolved_grid_cell_ids

def create_asiento(data, id_usuario=None, request=None):
    asiento = Asientos.objects.create(
        grid_row=data.get('grid_row'),
        grid_col=data.get('grid_col'),
        numero_asiento=data.get('numero_asiento'),
        existe=data.get('existe'),
        id_zona=data.get('id_zona'),
        id_grid_cell=data.get('id_grid_cell'),
    )
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={
                'grid_row': asiento.grid_row,
                'grid_col': asiento.grid_col,
                'numero_asiento': asiento.numero_asiento,
                'existe': asiento.existe,
                'id_zona': asiento.id_zona.pk,
                'id_grid_cell': asiento.id_grid_cell_id,
            },
            ip=request,
        )
    return asiento

def update_asiento(asiento, data, id_usuario=None, request=None):
    valores_antes = {
        'grid_row': asiento.grid_row,
        'grid_col': asiento.grid_col,
        'numero_asiento': asiento.numero_asiento,
        'existe': asiento.existe,
        'id_zona': asiento.id_zona.pk,
        'id_grid_cell': asiento.id_grid_cell_id,
    }
    asiento.grid_row = data.get('grid_row', asiento.grid_row)
    asiento.grid_col = data.get('grid_col', asiento.grid_col)
    asiento.numero_asiento = data.get('numero_asiento', asiento.numero_asiento)
    asiento.existe = data.get('existe', asiento.existe)
    id_zona = data.get('id_zona', asiento.id_zona)
    asiento.id_zona_id = id_zona.pk
    asiento.id_grid_cell = data.get('id_grid_cell', asiento.id_grid_cell)
    asiento.save()
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={
                'grid_row': asiento.grid_row,
                'grid_col': asiento.grid_col,
                'numero_asiento': asiento.numero_asiento,
                'existe': asiento.existe,
                'id_zona': asiento.id_zona.pk,
                'id_grid_cell': asiento.id_grid_cell_id,
            },
            ip=request,
        )
    return asiento

def delete_asiento(asiento, id_usuario=None, request=None):
    valores_antes = {'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk}
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    asiento.delete()
    return True


def _liberar_expirados(id_evento):
    EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        estado=EstadoAsientoEvento.RETENIDO,
        retenido_hasta__lt=timezone.now(),
    ).update(
        estado=EstadoAsientoEvento.DISPONIBLE,
        retenido_por=None,
        retenido_hasta=None,
    )


def obtener_disponibilidad_evento(id_evento):
    _liberar_expirados(id_evento)
    return EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
    ).values(
        'id_grid_cell',
        'estado',
        'id_grid_cell__row',
        'id_grid_cell__col',
        'id_grid_cell__id_zona_id',
    )


def inicializar_estado_asientos(id_evento, id_layout):
    from apps.grid_cells.models import GridCells
    from apps.precio_zona_evento.services import sincronizar_precios_zona_evento
    from apps.eventos.models import Eventos

    # Sincroniza grid_cells desde layout_data (upsert)
    ensure_layout_grid_cells_from_snapshot(id_layout)

    # Crear estado para todas las grid_cells ZONA DE ASIENTOS que aún no tienen estado
    # ignore_conflicts=True: no sobreescribe estados existentes (retenido/vendido)
    # unique_together = ('id_grid_cell', 'id_evento') lo garantiza
    seat_cells = GridCells.objects.filter(
        id_layout=id_layout,
        tipo='ZONA DE ASIENTOS',
    )
    estados = [
        EstadoAsientoEvento(
            id_grid_cell=cell,
            id_evento_id=id_evento,
            estado=EstadoAsientoEvento.DISPONIBLE,
        )
        for cell in seat_cells
    ]
    EstadoAsientoEvento.objects.bulk_create(estados, ignore_conflicts=True)

    try:
        evento = Eventos.objects.get(pk=id_evento)
        sincronizar_precios_zona_evento(evento)
    except Eventos.DoesNotExist:
        pass


@transaction.atomic
def retener_asientos(id_evento, ids_grid_cell, usuario):
    from apps.eventos.models import Eventos

    evento = Eventos.objects.get(pk=id_evento)
    tiempo = evento.tiempo_espera 
    ahora = timezone.now()

    _liberar_expirados(id_evento)

    estados = list(
        EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_grid_cell,
        )
    )

    if len(estados) != len(ids_grid_cell):
        raise SeatUnavailableError("Algunos asientos no existen para este evento.")

    for estado in estados:
        is_available = estado.estado == EstadoAsientoEvento.DISPONIBLE
        is_held_by_user = (estado.estado == EstadoAsientoEvento.RETENIDO and 
                           estado.retenido_por_id == usuario.pk)
        
        if not (is_available or is_held_by_user):
            raise SeatUnavailableError(
                f"Asiento (grid_cell={estado.id_grid_cell_id}) no disponible."
            )

    ids_previamente_retenidos_por_usuario = [
        e.id_grid_cell_id
        for e in EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=usuario,
        )
        if e.id_grid_cell_id not in ids_grid_cell
    ]

    if ids_previamente_retenidos_por_usuario:
        EstadoAsientoEvento.objects.filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_previamente_retenidos_por_usuario,
        ).update(
            estado=EstadoAsientoEvento.DISPONIBLE,
            retenido_por=None,
            retenido_hasta=None,
        )

    nueva_expiracion = ahora + timedelta(minutes=tiempo)

    EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        id_grid_cell__in=ids_grid_cell,
    ).update(
        estado=EstadoAsientoEvento.RETENIDO,
        retenido_por=usuario,
        retenido_hasta=nueva_expiracion,
    )

    return {
        "retenido_hasta": nueva_expiracion.isoformat(),
        "ids_grid_cell": list(ids_grid_cell),
    }


@transaction.atomic
def confirmar_compra(id_evento, ids_grid_cell, usuario):
    estados = list(
        EstadoAsientoEvento.objects.select_for_update().filter(
            id_evento=id_evento,
            id_grid_cell__in=ids_grid_cell,
            estado=EstadoAsientoEvento.RETENIDO,
            retenido_por=usuario,
        )
    )

    if len(estados) != len(ids_grid_cell):
        raise SeatUnavailableError("Algunos asientos ya no están retenidos por este usuario.")

    EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        id_grid_cell__in=ids_grid_cell,
    ).update(estado=EstadoAsientoEvento.VENDIDO)

    return estados


def liberar_asientos_usuario(id_evento, usuario):
    return EstadoAsientoEvento.objects.filter(
        id_evento=id_evento,
        retenido_por=usuario,
        estado=EstadoAsientoEvento.RETENIDO,
    ).update(
        estado=EstadoAsientoEvento.DISPONIBLE,
        retenido_por=None,
        retenido_hasta=None,
    )


def obtener_recomendacion_asientos(id_evento, id_layout, cantidad=3):
    """
    Recomienda 2-3 asientos continuos más cercanos al escenario.
    Excluye asientos vendidos o retenidos.

    Returns: list of grid_cell ids
    """
    from apps.grid_cells.models import GridCells
    from apps.eventos.models import Eventos
    from apps.layouts.models import Layouts
    from django.db.models import Q, Prefetch

    try:
        evento = Eventos.objects.get(pk=id_evento)
        layout = Layouts.objects.get(pk=id_layout)
    except (Eventos.DoesNotExist, Layouts.DoesNotExist):
        return []

    # Inicializar estado de asientos si es necesario
    inicializar_estado_asientos(id_evento, id_layout)

    # Encontrar el escenario (elemento tipo 'ESCENARIO')
    stage_cells = list(GridCells.objects.filter(
        id_layout=id_layout,
        tipo='ESCENARIO'
    ).values_list('row', 'col'))

    if not stage_cells:
        # Si no hay escenario, retornar asientos cercanos al inicio
        stage_cells = [(0, 0)]

    # Calcular distancia mínima desde el escenario
    def distance_to_stage(row, col):
        return min(
            abs(row - sr) + abs(col - sc)
            for sr, sc in stage_cells
        )

    # Obtener IDs de asientos NO disponibles (vendidos o retenidos)
    unavailable_ids = set(
        EstadoAsientoEvento.objects.filter(
            id_evento=id_evento,
            estado__in=[EstadoAsientoEvento.VENDIDO, EstadoAsientoEvento.RETENIDO]
        ).values_list('id_grid_cell_id', flat=True)
    )

    # Obtener asientos de tipo 'ZONA DE ASIENTOS' que NO están en unavailable
    available_seats = list(
        GridCells.objects.filter(
            id_layout=id_layout,
            tipo='ZONA DE ASIENTOS'
        ).exclude(
            id_grid_cells__in=unavailable_ids
        ).values(
            'id_grid_cells', 'row', 'col'
        ).order_by('row', 'col')
    )

    if not available_seats:
        return []

    # Agrupar asientos por fila
    seats_by_row = {}
    for seat in available_seats:
        row = seat['row']
        if row not in seats_by_row:
            seats_by_row[row] = []
        seats_by_row[row].append(seat)

    # Buscar bloques continuos de 2-3 asientos
    best_block = None
    best_distance = float('inf')

    for row, row_seats in seats_by_row.items():
        row_seats = sorted(row_seats, key=lambda s: s['col'])

        # Buscar bloques de cantidad (3) y cantidad-1 (2) asientos
        for block_size in [cantidad, cantidad - 1]:
            for i in range(len(row_seats) - block_size + 1):
                # Verificar si los asientos son continuos
                block = row_seats[i:i + block_size]
                cols = [s['col'] for s in block]

                is_continuous = all(
                    cols[j] == cols[0] + j for j in range(len(cols))
                )

                if is_continuous:
                    # Calcular distancia desde el escenario al primer asiento del bloque
                    dist = distance_to_stage(row, block[0]['col'])

                    if dist < best_distance:
                        best_distance = dist
                        best_block = block

    if best_block:
        return [seat['id_grid_cells'] for seat in best_block]

    return []