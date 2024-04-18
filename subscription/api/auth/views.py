from typing import Tuple

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import transaction
from onipkg_contrib.log_helper import log_error, log_tests
from rest_framework import generics
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import ModifiedTokenObtainPairSerializer, ModifiedTokenRefreshSerializer, ProfileSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenViewBase, TokenObtainPairView

from ...models import SystemUser, UserProfile, Customer
from ...utils.api_helpers import get_default_200_response_for_rest_api, get_default_400_response_for_rest_api, \
    get_default_404_response_for_rest_api, get_default_403_response_for_rest_api, get_profile_from_request, \
    get_custom_action_not_allowed_http_code_and_message
from ...utils.base_viewsets import CustomListCreateFilterClass, CustomRetrieveUpdateDestroyFilterClass, \
    CustomListFilterClass, CustomRetrieveFilterClass, CustomRetrieveUpdateFilterClass


class ModifiedObtainTokenPairView(TokenObtainPairView):
    """
    Obtém token de acesso para um usuário.
    Viewset aberta (não realiza verificação de acesso por Cliente ou Perfil)
    """
    permission_classes = (AllowAny,)
    serializer_class = ModifiedTokenObtainPairSerializer


class ModifiedTokenRefreshView(TokenViewBase):
    """
    Refresha um token de acesso para um usuário
    Viewset aberta (não realiza verificação de acesso por Cliente ou Perfil)
    """
    permission_classes = (AllowAny,)
    serializer_class = ModifiedTokenRefreshSerializer


class RegisterView(APIView):
    """
    View para cadastro de novos usuários
    Viewset aberta (não realiza verificação de acesso por Cliente ou Perfil)
    """
    permission_classes = [AllowAny]

    @staticmethod
    def create_user(data: dict):
        """
        Cria o novo usuário no BD

        Args:
            data: dados necessários pra criação do objeto

        Returns:
            Objeto CustomUser criado
        """
        user = SystemUser.new_user(data)
        return user

    @staticmethod
    def send_welcome_mail(recipient_email: str, recipient_name: str) -> None:
        """
        Envia o email de boas vindas pro usuário recém-cadastrado

        Args:
            recipient_email: endereco de email do recipiente
            recipient_name: nome do recipiente

        Returns:
            None
        """
        mail = EmailMessage('Seja bem-vindo(a)!', f'Olá, {recipient_name}! Bem-vindo(a) ao nosso sistema!',
                            to=[recipient_email])
        mail.send()

    def post(self, request):
        """
        Cria um novo usuário no sistema e envia um email de boas vindas

        Args:
            request: HttpRequest

        Returns: Response correspondente ao resultado da operação
        """
        # Fazemos um .copy() no request.POST pra evitar erro de "This QueryDict instance is immutable" no algoritmo
        data = request.POST.copy()
        try:
            # Cria o usuário no BD
            user = self.create_user(data)

            # Se chegou até aqui, deu tudo certo. Enviaremos um email de boas vindas e retornaremos 200
            self.send_welcome_mail(user.email, user.first_name)
            return get_default_200_response_for_rest_api({'user_id': user.id})
        except Exception as e:
            log_error(e)
            return get_default_400_response_for_rest_api()


class CompleteSignupView(APIView):
    """
    View para completar o cadastro de usuários que estejam com cadastro incompleto.
    Viewset semi-aberta (não realiza o filtro padrão por Cliente/Perfil, mas verifica se o usuário está autenticado).
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    @transaction.atomic
    def complete_signup(data: dict, user: SystemUser) -> Tuple[UserProfile, Customer]:
        """
        Completa o cadastro do usuário, criando cliente e perfil do usuário.
        1o passo: Criar o cliente.
                - São necessários o user (owner) e o nome
        2o passo: Criar perfil.
            - São necessários o objeto usuário e o objeto cliente.

        Args:
            data: dados necessários para a criacao dos objetos
            user: usuário previamente criado

        Returns:
            UserProfile e Customer criados
        """
        manager = Customer.new_customer(
            {'name': data.get('client_name'), 'owner': user})
        profile = UserProfile.new_profile(
            {'user': user, 'client_id':manager.id}
        )
        return profile, manager

    def post(self, request):
        data = request.POST.copy()
        try:
            user = SystemUser.objects.get(id=request.user.id)
            self.complete_signup(data, user)
        except Exception as e:
            log_error(e)
            return get_default_404_response_for_rest_api()
        return get_default_200_response_for_rest_api()


class UserRegistrationValidator(APIView):
    """
    Validador de dados de usuário para o momento de cadastro no cliente
    Viewset aberta (não realiza verificação de acesso por Cliente ou Perfil)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.POST
        email = data.get('email')
        try:  # Se já existir usuário com o email informado, dá pau
            SystemUser.objects.get(email=email)
            return get_default_400_response_for_rest_api(
                {'errors': {'email': _('Usuário com esse endereço de email já existe')}})
        except SystemUser.DoesNotExist:
            try:  # Valida o email caso seja inédito
                from django.core.validators import validate_email
                validate_email(email)
            except ValidationError as e:
                return get_default_400_response_for_rest_api({'errors': {'email': e}})
        try:  # Valida a senha
            validate_password(data.get('password'))
            return get_default_200_response_for_rest_api()
        except ValidationError as e:
            return get_default_400_response_for_rest_api({'errors': {'password': e}})


class ChangePasswordView(APIView):
    """
    View para mudar a senha de um usuário logado.
    Viewset fechada (um usuário só pode mudar a senha de si mesmo, então ele tem que estar logado)
    """
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        # Inicializa variáveis necessárias pro algoritmo
        user = SystemUser.objects.get(id=request.user.id)
        new_password = request.POST.get('new_password')

        # Verifica a senha antiga do usuário pra assegurar a segurança da operação
        if not user.check_password(request.POST.get('old_password')):
            return get_default_403_response_for_rest_api({'msg': _('Senha incorreta')})

        # Verifica se a senha que o usuário deseja inserir é válida
        try:
            validate_password(new_password)
        except ValidationError:
            return get_default_403_response_for_rest_api(
                {'msg': _('A senha informada não atende aos requisitos mínimos')})

        # Atualiza a senha e salva o usuário (o set_password NAO salva no BD automáticamente)
        user.set_password(new_password)
        user.save()
        return get_default_200_response_for_rest_api()


class GetProfileView(generics.ListAPIView):
    """
    Lista os perfis que tem fk em um determinado usuário (pra ver com quais clientes o usuário tem parceiria)
    Viewset aberta (não realiza verificação de acesso por Cliente ou Perfil)
    """
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        """
        Retorna apenas o perfil do usuário
        """
        return self.queryset.filter(user_id=self.request.user.id)


class ProfileListCreate(CustomListCreateFilterClass):
    """
    Lista e cria Perfis
    Viewset fechada (limita os resultados com base no plano do Cliente e no acesso do Perfil)
    """
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer
    related_module = 'auth'

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Cria novos Perfis com base em informacoes vindas do front. Cria/pega o usuário
        com base no email informado pelo cliente e define os campos necessários no perfil
        """
        # Repete a validacao de perm de criacao porque demos override no create
        profile: UserProfile = get_profile_from_request(request)
        if not profile.can_create():
            self.permission_denied(
                request,
                **get_custom_action_not_allowed_http_code_and_message()
            )
        data = request.data
        response_msg = _('Sucesso')  # essa msg vai ser redefinida apenas se o usuário c email informado ainda n existir
        user_email = data.get('user_email')  # vou procurar o user pelo email
        user_name = data.get('user_name')  # vou procurar o user pelo email
        if not user_email:
            return get_default_400_response_for_rest_api({'user_email': ''})

        try:
            user = SystemUser.objects.get(email=user_email)  # se existir, blz
        except SystemUser.DoesNotExist:  # se nao, cria um inativo e manda email de convite pra redefinir senha e ativar
            user = SystemUser(first_name=user_name, email=user_email)
            user.set_unusable_password()  # Em vez de criar o usuário com is_active=False, criamos com senha fake
            user.save()
            # Ao criar esse user, o sinal post_save de CustomUser vai enviar o email de ativação de conta pra ele
            response_msg = _(
                'O usuário informado ainda não existe. Um convite foi enviado para o endereço de email informado.')

        UserProfile.new_profile({'user': user, 'client': profile.client, 'allowed_actions': data.get('allowed_actions')})
        return get_default_200_response_for_rest_api({'msg': response_msg, 'id': profile.id})


class ProfileRetrieveUpdateDestroy(CustomRetrieveUpdateDestroyFilterClass):
    """
    Retorna/Altera/Exclui uma instancia de Perfil
    Viewset fechada (limita os resultados com base no plano do Cliente e no acesso do Perfil)
    """
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer
    related_module = 'auth'


class UserList(CustomListFilterClass):
    queryset = SystemUser.objects.all()
    serializer_class = SystemUserSerializer
    related_module = 'auth'


class UserRetrieve(CustomRetrieveFilterClass):
    queryset = SystemUser.objects.all()
    serializer_class = SystemUserSerializer
    related_module = 'auth'


class CustomerList(CustomListFilterClass):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    related_module = 'auth'


class CustomerRetrieveUpdate(CustomRetrieveUpdateFilterClass):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    related_module = 'auth'
