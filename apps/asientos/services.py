from .models import Asientos
from apps.auditoria_logs.services import registrar_auditoria

def create_asiento(data, id_usuario=None, request=None):
    asiento = Asientos.objects.create(
        grid_row=data.get('grid_row'),
        grid_col=data.get('grid_col'),
        numero_asiento=data.get('numero_asiento'),
        existe=data.get('existe'),
        id_zona=data.get('id_zona')
    )
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk},
            ip=request,
        )
    return asiento

def update_asiento(asiento, data, id_usuario=None, request=None):
    valores_antes = {'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk}
    asiento.grid_row = data.get('grid_row', asiento.grid_row)
    asiento.grid_col = data.get('grid_col', asiento.grid_col)
    asiento.numero_asiento = data.get('numero_asiento', asiento.numero_asiento)
    asiento.existe = data.get('existe', asiento.existe)
    id_zona = data.get('id_zona', asiento.id_zona)
    asiento.id_zona_id = id_zona.pk
    asiento.save()
    if id_usuario:
        registrar_auditoria(
            entidad='asientos',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'grid_row': asiento.grid_row, 'grid_col': asiento.grid_col, 'numero_asiento': asiento.numero_asiento, 'existe': asiento.existe, 'id_zona': asiento.id_zona.pk},
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