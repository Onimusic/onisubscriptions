import os
import json

from django.db import models


def get_plans():
    """Carrega todos os planos do arquivo json e retorna um dicionário com os planos.
    """
    with open(os.path.join(os.path.dirname(__file__), 'subscriptions.json')) as f:
        plans = json.load(f)
    return plans


class BasePermissionClass(models.Model):
    """
    Classe que gerencia as permissões de acesso e de ações no sistema. É abstrata e deve ser herdada por todos os outros
    modelos do sistema.
    """

    class Meta:
        abstract = True

    def has_permission(self, permission_to_check):
        return False

    @classmethod
    def get_queryset(cls, request, *args, **kwargs):
        """
        Implementação default do método. Os modelos que devem ser filtrados com base no perfil devem dar override.
        """
        return cls.objects.all()  # todo mudar pra filter(deleted=False) para garantir o soft_delete
