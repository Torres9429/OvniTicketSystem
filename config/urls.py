from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.roles.urls')),
    path('api/', include('apps.usuarios.urls')),
    path('api/', include('apps.eventos.urls')),
    path('api/', include('apps.grid_cells.urls')),
    path('api/', include('apps.ordenes.urls')),
    path('api/', include('apps.tickets.urls')),
]
