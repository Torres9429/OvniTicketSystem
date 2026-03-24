from .models import Asientos

def create_asiento(data):
    return Asientos.objects.create(
        grid_row=data.get('grid_row'),
        grid_col=data.get('grid_col'),
        numero_asiento=data.get('numero_asiento'),
        existe=data.get('existe'),
        id_zona_id=data.get('id_zona')
    )

def update_asiento(asiento, data):
    asiento.grid_row = data.get('grid_row', asiento.grid_row)
    asiento.grid_col = data.get('grid_col', asiento.grid_col)
    asiento.numero_asiento = data.get('numero_asiento', asiento.numero_asiento)
    asiento.existe = data.get('existe', asiento.existe)
    asiento.id_zona_id = data.get('id_zona', asiento.id_zona_id)
    asiento.save()
    return asiento

def delete_asiento(asiento):
    asiento.delete()
    return True