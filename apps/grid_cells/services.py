from .models import GridCells


def get_all_grid_cells():
    return GridCells.objects.all()


def get_grid_cells_por_layout(id_layout: int):
    return GridCells.objects.filter(id_layout=id_layout)


def crear_grid_cell(tipo: str, row: int, col: int, id_zona, id_layout) -> GridCells:
    return GridCells.objects.create(
        tipo=tipo,
        row=row,
        col=col,
        id_zona_id=id_zona.pk,
        id_layout_id=id_layout.pk,
    )


def actualizar_grid_cell(grid_cell: GridCells, tipo: str, row: int, col: int, id_zona, id_layout) -> GridCells:
    grid_cell.tipo = tipo
    grid_cell.row = row
    grid_cell.col = col
    grid_cell.id_zona_id = id_zona.pk 
    grid_cell.id_layout_id = id_layout.pk
    grid_cell.save(update_fields=['tipo', 'row', 'col', 'id_zona_id', 'id_layout_id'])
    return grid_cell


def eliminar_grid_cell(grid_cell: GridCells) -> None:
    grid_cell.delete()