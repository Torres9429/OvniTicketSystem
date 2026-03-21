from .models import GridCells

def get_all_grid_cells():
    return GridCells.objects.all()

def get_grid_cells_por_layout(id_layout: int):
    return GridCells.objects.filter(id_layout=id_layout)