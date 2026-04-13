from .models import GridCells
from apps.auditoria_logs.services import registrar_auditoria

def get_all_grid_cells():
    return GridCells.objects.all()


def get_grid_cells_por_layout(id_layout: int):
    return GridCells.objects.filter(id_layout=id_layout)

def crear_grid_cell(tipo: str, row: int, col: int, id_zona, id_layout, id_usuario=None, request=None) -> GridCells:
    grid_cell = GridCells.objects.create(
        tipo=tipo,
        row=row,
        col=col,
        id_zona_id=id_zona.pk if id_zona else None,
        id_layout_id=id_layout.pk,
    )
    if id_usuario:
        registrar_auditoria(
            entidad='grid_cells',
            accion='CREAR',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'tipo': grid_cell.tipo, 'row': grid_cell.row, 'col': grid_cell.col, 'id_zona': id_zona.nombre if id_zona else None, 'id_layout': id_layout.pk},
            ip=request,
        )
    return grid_cell

def bulk_crear_grid_cells(celdas: list, id_layout_obj, id_usuario=None, request=None) -> list:
    """Crea múltiples celdas en una sola operación de base de datos."""
    objetos = [
        GridCells(
            tipo=celda['tipo'],
            row=celda['row'],
            col=celda['col'],
            id_zona_id=celda.get('id_zona'),
            id_layout_id=id_layout_obj.pk,
        )
        for celda in celdas
    ]
    creados = GridCells.objects.bulk_create(objetos)
    if id_usuario:
        registrar_auditoria(
            entidad='grid_cells',
            accion='CREAR_BULK',
            id_usuario=id_usuario,
            valores_antes=None,
            valores_despues={'cantidad': len(creados), 'id_layout': id_layout_obj.pk},
            ip=request,
        )
    return creados

def eliminar_grid_cells_por_layout(id_layout: int, id_usuario=None, request=None) -> int:
    """Elimina todas las celdas de un layout en una sola operación."""
    qs = GridCells.objects.filter(id_layout=id_layout)
    cantidad = qs.count()
    if cantidad > 0:
        qs.delete()
        if id_usuario:
            registrar_auditoria(
                entidad='grid_cells',
                accion='ELIMINAR_BULK',
                id_usuario=id_usuario,
                valores_antes={'cantidad': cantidad, 'id_layout': id_layout},
                valores_despues=None,
                ip=request,
            )
    return cantidad

def actualizar_grid_cell(grid_cell: GridCells, tipo: str, row: int, col: int, id_zona, id_layout, id_usuario=None, request=None) -> GridCells:
    valores_antes = {'tipo': grid_cell.tipo, 'row': grid_cell.row, 'col': grid_cell.col, 'id_zona': getattr(grid_cell.id_zona, 'nombre', None), 'id_layout': grid_cell.id_layout_id}
    grid_cell.tipo = tipo
    grid_cell.row = row
    grid_cell.col = col
    grid_cell.id_zona_id = id_zona.pk if id_zona else None
    grid_cell.id_layout_id = id_layout.pk
    grid_cell.save(update_fields=['tipo', 'row', 'col', 'id_zona_id', 'id_layout_id'])
    if id_usuario:
        registrar_auditoria(
            entidad='grid_cells',
            accion='ACTUALIZAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues={'tipo': grid_cell.tipo, 'row': grid_cell.row, 'col': grid_cell.col, 'id_zona': id_zona.nombre if id_zona else None, 'id_layout': id_layout.pk},
            ip=request,
        )
    return grid_cell


def eliminar_grid_cell(grid_cell: GridCells, id_usuario=None, request=None) -> None:
    valores_antes = {'tipo': grid_cell.tipo, 'row': grid_cell.row, 'col': grid_cell.col, 'id_zona': getattr(grid_cell.id_zona, 'pk', None), 'id_layout': grid_cell.id_layout_id}
    if id_usuario:
        registrar_auditoria(
            entidad='grid_cells',
            accion='ELIMINAR',
            id_usuario=id_usuario,
            valores_antes=valores_antes,
            valores_despues=None,
            ip=request,
        )
    grid_cell.delete()