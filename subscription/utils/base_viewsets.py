from onipkg_contrib.log_helper import log_tests
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_helpers import get_profile_from_request, get_custom_feature_blocked_http_code_and_message, \
    get_custom_action_not_allowed_http_code_and_message


def default_list(viewset, request, *args, **kwargs):
    """
    Lógica de override do método list das viewsets de listagem de objetos.
    Realiza o filtro de acordo com o modelo dos objetos do atributo queryset da viewset passada como parâmetro.
    Utiliza o método get_queryset implementado no modelo pra pegar a queryset, e pagina os objetos normal, de acordo com
    o método list padrao do DRF.
    """
    queryset = viewset.filter_queryset(viewset.get_queryset().model.get_queryset(request, *args, **kwargs))
    # viewset.filter_queryset retorna uma queryset. queryset.model retorna o modelo dos seus objetos. model.get_queryset
    # retorna a queryset de objetos, filtrada de maneira correta pelo modelo.
    page = viewset.paginate_queryset(queryset)
    if page is not None:
        serializer = viewset.get_serializer(page, many=True)
        return viewset.get_paginated_response(serializer.data)

    serializer = viewset.get_serializer(queryset, many=True)
    return Response(serializer.data)


def default_retrieve(self, request, *args, **kwargs):
    """
    Override do método delete do mixin do DRF pra verificar se o perfil tem permissão de ver objetos
    """
    profile = get_profile_from_request(request)
    if not profile.can_read():
        self.permission_denied(
            request,
            **get_custom_action_not_allowed_http_code_and_message()
        )
    instance = self.get_object()
    serializer = self.get_serializer(instance)
    return Response(serializer.data)


def default_create(self, request, *args, **kwargs):
    """
    Override do método delete do mixin do DRF pra verificar se o perfil tem permissão de criar objetos
    """
    profile = get_profile_from_request(request)
    if not profile.can_create():
        self.permission_denied(
            request,
            **get_custom_action_not_allowed_http_code_and_message()
        )
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)
    headers = self.get_success_headers(serializer.data)
    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


def default_update(self, request, *args, **kwargs):
    """
    Override do método delete do mixin do DRF pra verificar se o perfil tem permissão de editar objetos
    """
    profile = get_profile_from_request(request)
    if not profile.can_update():
        self.permission_denied(
            request,
            **get_custom_action_not_allowed_http_code_and_message()
        )
    partial = kwargs.pop('partial', False)
    instance = self.get_object()
    serializer = self.get_serializer(instance, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    self.perform_update(serializer)

    if getattr(instance, '_prefetched_objects_cache', None):
        # If 'prefetch_related' has been applied to a queryset, we need to
        # forcibly invalidate the prefetch cache on the instance.
        instance._prefetched_objects_cache = {}

    return Response(serializer.data)


def default_delete(self, request, *args, **kwargs):
    """
    Override do método delete do mixin do DRF pra verificar se o perfil tem permissão de apagar objetos
    """
    profile = get_profile_from_request(request)
    if not profile.can_delete():
        self.permission_denied(
            request,
            **get_custom_action_not_allowed_http_code_and_message()
        )
    return self.destroy(request, *args, **kwargs)


class CustomApiViewFilterClass(APIView):
    """
    Override de APIView para verificação de acesso do Cliente a determinadas features
    """
    related_module = None  # Remover esse atributo permitirá que qualquer perfil acesse a feature

    def check_permissions(self, request):
        """
        Verifica se o Cliente tem acesso ao conteúdo desejado (se está no plano dele)
        """
        # Verifica se o cliente do usuário da request tem acesso à feature
        from django.core.exceptions import ObjectDoesNotExist
        try:
            profile = get_profile_from_request(request)
            if hasattr(self, 'related_module') and self.related_module not in profile.get_available_features():
                raise ObjectDoesNotExist
        except ObjectDoesNotExist:
            self.permission_denied(
                request,
                **get_custom_feature_blocked_http_code_and_message()
            )
        # Verificação padrão do DRF para permissões do Django
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request,
                    message=getattr(permission, 'message', None),
                    code=getattr(permission, 'code', None)
                )


class CustomListFilterClass(generics.ListAPIView, CustomApiViewFilterClass):
    """
    Override de ListAPIView para verificação de acesso do Cliente e permissão do Perfil
    """

    def list(self, request, *args, **kwargs):
        """
        Garante que serão listados apenas objetos do Cliente desejado
        """
        return default_list(self, request, *args, **kwargs)


class CustomListCreateFilterClass(generics.ListCreateAPIView, CustomApiViewFilterClass):
    """
    Override de ListCreateAPIView para verificação de acesso do Cliente e permissão do Perfil
    """

    def list(self, request, *args, **kwargs):
        """
        Garante que serão listados apenas objetos do Cliente desejado
        """
        return default_list(self, request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """ Verifica se o perfil logado tem permissão de criação
        """
        return default_create(self, request, *args, **kwargs)


class CustomRetrieveFilterClass(generics.RetrieveAPIView, CustomApiViewFilterClass):
    """
    Override de RetrieveAPIView para verificação de acesso do Cliente e permissão do Perfil
    """
    def retrieve(self, request, *args, **kwargs):
        return default_retrieve(self, request, *args, **kwargs)


class CustomUpdateFilterClass(generics.UpdateAPIView, CustomApiViewFilterClass):
    """
    Override de UpdateAPIView para verificação de acesso do Cliente e permissão do Perfil
    """

    def update(self, request, *args, **kwargs):
        return default_update(self, request, *args, **kwargs)


class CustomDestroyFilterClass(generics.DestroyAPIView, CustomApiViewFilterClass):
    """
    Override de DestroyAPIView para verificação de acesso do Cliente e permissão do Perfil
    """

    def delete(self, request, *args, **kwargs):
        return default_delete(self, request, *args, **kwargs)


class CustomRetrieveUpdateFilterClass(generics.RetrieveUpdateAPIView, CustomApiViewFilterClass):
    """
    Override de RetrieveUpdateAPIView para verificação de acesso do Cliente e permissão do Perfil
    """
    def retrieve(self, request, *args, **kwargs):
        return default_retrieve(self, request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return default_update(self, request, *args, **kwargs)


class CustomRetrieveDestroyFilterClass(generics.RetrieveDestroyAPIView, CustomApiViewFilterClass):
    """
    Override de RetrieveDestroyAPIView para verificação de acesso do Cliente e permissão do Perfil
    """

    def retrieve(self, request, *args, **kwargs):
        return default_retrieve(self, request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return default_delete(self, request, *args, **kwargs)


class CustomRetrieveUpdateDestroyFilterClass(generics.RetrieveUpdateDestroyAPIView, CustomApiViewFilterClass):
    """
    Override de RetrieveUpdateDestroyAPIView para verificação de acesso do Cliente e permissão do Perfil
    """

    def retrieve(self, request, *args, **kwargs):
        return default_retrieve(self, request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return default_update(self, request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return default_delete(self, request, *args, **kwargs)
