from django.core.management.base import BaseCommand
from apps.eventos.services import actualizar_estadisticas_eventos


class Command(BaseCommand):
    help = 'Actualiza las estadísticas de eventos (boletos vendidos, ingresos, ocupación)'

    def handle(self, *args, **options):
        self.stdout.write('Actualizando estadísticas de eventos...')
        
        resultado = actualizar_estadisticas_eventos()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Estadísticas actualizadas correctamente\n'
                f'  Eventos procesados: {resultado["actualizado"]}'
            )
        )
