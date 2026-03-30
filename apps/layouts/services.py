from .models import Layouts


def crear_layout(grid_rows: int, grid_cols: int, version: int, estatus: str, id_lugar, id_dueno, fecha_creacion, fecha_actualizacion):
    return Layouts.objects.create(
        grid_rows=grid_rows,
        grid_cols=grid_cols,
        version=version,
        estatus=estatus,
        id_lugar_id=id_lugar.pk,
        id_dueno_id=id_dueno.pk,
        fecha_creacion=fecha_creacion,
        fecha_actualizacion=fecha_actualizacion
    )


def actualizar_layout(layout: Layouts, grid_rows: int, grid_cols: int, version: int, estatus: str, id_lugar, id_dueno) -> Layouts:
    layout.grid_rows = grid_rows
    layout.grid_cols = grid_cols
    layout.version = version
    layout.estatus = estatus
    layout.id_lugar = id_lugar
    layout.id_dueno = id_dueno
    layout.save(update_fields=['grid_rows', 'grid_cols', 'version', 'estatus', 'id_lugar', 'id_dueno', 'fecha_actualizacion'])
    return layout


def desactivar_layout(layout: Layouts) -> Layouts:
    layout.estatus = 'BORRADOR'
    layout.save(update_fields=['estatus', 'fecha_actualizacion'])
    return layout


def activar_layout(layout: Layouts) -> Layouts:
    layout.estatus = 'PUBLICADO'
    layout.save(update_fields=['estatus', 'fecha_actualizacion'])
    return layout
