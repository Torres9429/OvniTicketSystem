from apps.roles.models import Roles


def get_all_roles():
    return Roles.objects.all()
