from .models import Layouts


def crear_layout(
    grid_rows: int,
    grid_cols: int,
    version: int,
    estatus: str,
    id_lugar,
    id_dueno,
    fecha_creacion=None,
    fecha_actualizacion=None,
    layout_data=None,
):
    data = {
        "grid_rows": grid_rows,
        "grid_cols": grid_cols,
        "version": version,
        "estatus": estatus,
        "id_lugar_id": id_lugar.pk,
        "id_dueno_id": id_dueno.pk,
    }
    if fecha_creacion is not None:
        data["fecha_creacion"] = fecha_creacion
    if layout_data is not None:
        data["layout_data"] = layout_data

    return Layouts.objects.create(**data)


def actualizar_layout(layout: Layouts, **changes) -> Layouts:
    allowed = {
        "grid_rows",
        "grid_cols",
        "version",
        "estatus",
        "id_lugar",
        "id_dueno",
        "layout_data",
    }

    update_fields = []
    for key, value in changes.items():
        if key not in allowed:
            continue
        setattr(layout, key, value)
        update_fields.append(key)

    if update_fields:
        update_fields.append("fecha_actualizacion")
        layout.save(update_fields=update_fields)

    return layout


def desactivar_layout(layout: Layouts) -> Layouts:
    layout.estatus = 'BORRADOR'
    layout.save(update_fields=['estatus', 'fecha_actualizacion'])
    return layout


def activar_layout(layout: Layouts) -> Layouts:
    layout.estatus = 'PUBLICADO'
    layout.save(update_fields=['estatus', 'fecha_actualizacion'])
    return layout
