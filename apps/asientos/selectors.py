from .models import Asientos

def get_all_asientos():
    return Asientos.objects.select_related('id_zona').all()

def get_asiento_by_id(asiento_id):
    return Asientos.objects.select_related('id_zona').filter(id_asiento=asiento_id).first()