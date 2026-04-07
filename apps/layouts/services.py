from django.utils import timezone
from .models import Layouts
from apps.auditoria_logs.services import registrar_auditoria

def crear_layout(
    grid_rows: int,
    grid_cols: int,
    version: int,
    estatus: str,
    id_lugar,
    id_dueno,
    request=None,
    fecha_creacion=None,
    fecha_actualizacion=None,
    layout_data=None,
):
    now = timezone.now()
    layout = Layouts.objects.create(
        grid_rows=grid_rows,
        grid_cols=grid_cols,
        version=version,
        estatus=estatus,
        id_lugar_id=id_lugar.pk,
        id_dueno_id=id_dueno.pk,
        fecha_creacion=fecha_creacion or now,
        fecha_actualizacion=fecha_actualizacion or now,
        layout_data=layout_data,
    )
    registrar_auditoria(
        entidad='layouts',
        accion='CREAR',
        id_usuario=id_dueno,
        valores_antes=None,
        valores_despues={
            'grid_rows': layout.grid_rows,
            'grid_cols': layout.grid_cols,
            'version': layout.version,
            'estatus': layout.estatus,
            'id_lugar': layout.id_lugar.pk,
            'id_dueno': layout.id_dueno.pk,
        },
        ip=request,
    )
    return layout


def actualizar_layout(layout: Layouts, request=None, **changes) -> Layouts:
    allowed = {
        "grid_rows",
        "grid_cols",
        "version",
        "estatus",
        "id_lugar",
        "id_dueno",
        "layout_data",
    }

    valores_antes = {
        'grid_rows': layout.grid_rows,
        'grid_cols': layout.grid_cols,
        'version': layout.version,
        'estatus': layout.estatus,
        'id_lugar': layout.id_lugar.pk,
        'id_dueno': layout.id_dueno.pk,
    }

    update_fields = []
    for key, value in changes.items():
        if key not in allowed:
            continue
        setattr(layout, key, value)
        update_fields.append(key)

    if not update_fields:
        return layout

    update_fields.append("fecha_actualizacion")
    layout.save(update_fields=update_fields)

    id_usuario = changes.get('id_dueno', getattr(request, 'user', None) if request else None)
    registrar_auditoria(
        entidad='layouts',
        accion='ACTUALIZAR',
        id_usuario=id_usuario,
        valores_antes=valores_antes,
        valores_despues={
            'grid_rows': layout.grid_rows,
            'grid_cols': layout.grid_cols,
            'version': layout.version,
            'estatus': layout.estatus,
            'id_lugar': layout.id_lugar.pk,
            'id_dueno': layout.id_dueno.pk,
        },
        ip=request,
    )

    return layout


def desactivar_layout(layout: Layouts, id_usuario, request=None) -> Layouts:
    valores_antes = {'estatus': layout.estatus, 'fecha_actualizacion': str(layout.fecha_actualizacion)}
    layout.estatus = 'BORRADOR'
    layout.save(update_fields=['estatus', 'fecha_actualizacion'])
    if id_usuario:
        registrar_auditoria(
            entidad='layouts',
            accion='DESACTIVAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'estatus': 'BORRADOR', 'fecha_actualizacion': str(layout.fecha_actualizacion)},
            ip=request,
        )
    return layout


def activar_layout(layout: Layouts, id_usuario, request=None) -> Layouts:
    valores_antes = {'estatus': layout.estatus, 'fecha_actualizacion': str(layout.fecha_actualizacion)}
    layout.estatus = 'PUBLICADO'
    layout.save(update_fields=['estatus', 'fecha_actualizacion'])
    if id_usuario:
        registrar_auditoria(
            entidad='layouts',
            accion='ACTIVAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'estatus': 'PUBLICADO', 'fecha_actualizacion': str(layout.fecha_actualizacion)},
            ip=request,
        )
    return layout
