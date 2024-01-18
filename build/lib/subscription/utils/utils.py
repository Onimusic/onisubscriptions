import os
import json

from typing import Optional
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from onipkg_contrib.log_helper import log_error
from subscription.utils.api_helpers import get_partner_from_request


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

    def owner_artist(self) -> Optional['Artist']:
        """
        Implementação default da property. Os modelos que devem ser filtrados por artista devem dar override.
        Retorna o artista dono daquele objeto, ou None (se no objeto não houver referencia pro modelo Artista)
        """
        return None

    def get_partner_from_user_and_artist(self, request):
        """
        Retorna o objeto do parceiro do usuário em um artista.
        """
        if artist := self.owner_artist():
            try:
                # Essa query garante que o usuário é parceiro do cliente dono do artista em questao
                partner = get_partner_from_request(request)
                # Agora temos que ver se esse tal parceiro é global, ou se tem fk no artista
                if artist.id not in partner.related_artists():
                    return None
                # Se chegar até aqui é pq o parceiro existe e tem acesso ao artista
                return partner
            except ObjectDoesNotExist as e:
                log_error(e)
                return None
        return None

    @classmethod
    def get_queryset(cls, request, *args, **kwargs):
        """
        Implementação default do método. Os modelos que devem ser filtrados por artista devem dar override.
        """
        return cls.objects.all()  # todo mudar pra filter(deleted=False) para garantir o soft_delete

    @staticmethod
    def get_user_artists_ids(request):
        """
        Pega a lista de ids de artista disponíveis para o usuário presente na requisição
        """
        # Pra evitar import circular, não podemos fazer Partner.objects direto. Tem que fazer essa gambi pra não
        # ter que importar esse modelo.
        partner_artists = get_partner_from_request(request).related_artists()
        # se tiver current artist, filtra só por ele
        if current_artist := request.current_artist:
            return list(filter(lambda artist_id: artist_id == int(current_artist), partner_artists))
        else:
            return partner_artists
