from rest_framework import status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _


def get_profile_from_request(request) -> 'UserProfile':
    """
    Pega o perfil do usuário com base na request. Supõe-se que a request já passou pelo Middleware
    Args:
        request: Requisição HTTP

    Returns:
        Objeto do tipo Profile ligado ao usuário da requisição
    """
    from django.apps import apps
    return apps.get_model('core', 'SystemUser').objects.get(id=request.user.id).profile


def get_custom_action_not_allowed_http_code_and_message() -> dict:
    """ Retorna o código HTTP e mensagem customizados pra quando o cliente tem acesso à feature mas o perfil não tem
    permissão pra realizar a ação
    """
    return {'message': _('Você não tem permissão para fazer isso!'), 'code': 408}


def get_custom_feature_blocked_http_code_and_message() -> dict:
    """ Retorna o código HTTP e mensagem customizados pra quando o cliente não tem acesso à feature
    """
    return {'message': _('O conteúdo desejado não está incluso no seu plano atual.'), 'code': 407}


def get_custom_feature_limit_reached_http_code_and_message() -> dict:
    """ Retorna o código HTTP e mensagem customizados pra quando o cliente não tem acesso à feature
    """
    return {'message': _('Você atingiu a cota máxima dessa funcionalidade para o seu plano atual.'), 'code': 407}


def get_default_response_for_rest_api(http_status: int, data: dict = None, header: dict = None) -> Response:
    """
    Retorna a response padrão para requisicoes do Django Rest
    """
    if data is None:
        data = {}
    return Response(data, status=http_status, headers=header)


def get_default_200_response_for_rest_api(data: dict = None) -> Response:
    if data is None:
        data = {'msg': _('Sucesso')}
    return get_default_response_for_rest_api(status.HTTP_200_OK, data)


def get_default_201_response_for_rest_api(data: dict = None) -> Response:
    if data is None:
        data = {'msg': _('Sucesso')}
    return get_default_response_for_rest_api(status.HTTP_201_CREATED, data)


def get_default_400_response_for_rest_api(data: dict = None) -> Response:
    if data is None:
        data = {'msg': _('Ocorreu um erro. Por favor, contacte o suporte.')}
    return get_default_response_for_rest_api(status.HTTP_400_BAD_REQUEST, data)


def get_default_401_response_for_rest_api(data: dict = None) -> Response:
    if data is None:
        data = {'msg': _('Você não tem permissão para acessar esse conteúdo.')}
    return get_default_response_for_rest_api(status.HTTP_401_UNAUTHORIZED, data)


def get_default_403_response_for_rest_api(data: dict = None) -> Response:
    if data is None:
        data = {'msg': _('Você não tem permissão para acessar esse conteúdo.')}
    return get_default_response_for_rest_api(status.HTTP_403_FORBIDDEN, data)


def get_default_404_response_for_rest_api(data: dict = None) -> Response:
    if data is None:
        data = {'msg': _('Conteúdo não encontrado.')}
    return get_default_response_for_rest_api(status.HTTP_404_NOT_FOUND, data)
