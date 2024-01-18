# from typing import Optional

# from django.db import models
# from django.db.models import QuerySet
# from django.utils.translation import gettext_lazy as t
# from django.contrib.auth.models import AbstractUser, Permission
# from django.contrib.auth.base_user import BaseUserManager

# from onipkg_contrib.models.base_model import BaseModel
# from subscription.utils.utils import BasePermissionClass


# class CustomUserManager(BaseUserManager):
#     def create_superuser(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError("User must have an email")
#         if not password:
#             raise ValueError("User must have a password")

#         user = self.model(
#             email=self.normalize_email(email)
#         )
#         user.set_password(password)
#         user.is_superuser = True
#         user.is_staff = True
#         user.is_active = True
#         user.save(using=self._db)
#         return user


# class CustomUser(AbstractUser):
#     """Classe que implementa a classe do usuário com a adição de alguns campos desejados.

#     Attributes
#         dark_mode (models.BooleanField): Preferência quanto ao uso ou não do tema escuro.
#         desired_notifications (models.CharField): Preferência quanto as notificações do usuário.
#         system_language (models.CharField): Preferência quanto a linguagem em uso no sistema.
#     """

#     # Override de campos padrao pra evitar erros de autenticacao
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []  # Ao definir o email como username_field, deve-se tirar ele do required_fields. N sei pq
#     username = None
#     email = models.EmailField(t('email address'), unique=True)

#     objects = CustomUserManager()

#     # Campos customizados daqui pra baixo
#     class NotificationTypes(models.TextChoices):
#         NOTIFICATION_ONE = 'NONE', t('Notificação Tipo 1')
#         NOTIFICATION_TWO = 'NTWO', t('Notificação Tipo 2')
#         NOTIFICATION_THREE = 'NTHR', t('Notificação Tipo 3')

#     class SystemLanguages(models.TextChoices):
#         PORTUGUESE = 'PT', t('Português')
#         ENGLISH = 'EN', t('Inglês')
#         SPANISH = 'ES', t('Espanhol')

#     spotify_id = models.CharField(max_length=255, null=True, blank=True, verbose_name=t('ID Spotify do usuário'))
#     spotify_id_access_token = models.TextField(null=True, blank=True, verbose_name=t('Token de acesso Spotify'))
#     spotify_id_refresh_token = models.TextField(null=True, blank=True, verbose_name=t('Token de refresh Spotify'))
#     has_seen_the_tutorial = models.BooleanField(verbose_name=t('Já viu o tutorial'), default=False, help_text=t(
#         'Se este campo estiver desmarcado, a plataforma entenderá que é o primeiro login do usuário e mostrará o tutorial.'))
#     token = models.UUIDField(null=True, unique=True)
#     firebase_uid = models.CharField(max_length=100, null=True, blank=True,
#                                     verbose_name=t(
#                                         'UUID do usuário no firebase (para login no mobile e disparo de notificações)'))
#     facebook_long_lived_token = models.CharField(max_length=255, null=True, blank=True,
#                                                  verbose_name=t('Token de acesso do Facebook'))
#     facebook_long_lived_token_fetch_date = models.DateTimeField(null=True, blank=True,
#                                                                 verbose_name=t(
#                                                                     'Data de obtenção do token de acesso do Facebook'))

#     class Meta:
#         ordering = ['email', 'id']
#         verbose_name = t('Usuário')
#         verbose_name_plural = t('Usuários')

#     def partnerships(self):
#         """ Retorna as parcerias desse usuário """
#         return self.partner_set.all()

#     def artists(self) -> QuerySet('Artist'):
#         """ Retorna os artistas com os quais esse perfil tem algum relacionamento """
#         try:
#             owned_artists = self.manager.artists()
#         except Manager.DoesNotExist:
#             owned_artists = []
#         partnership_artists = Artist.objects.filter(partner__in=self.partnerships())
#         artists_list = list(set(owned_artists).union(set(partnership_artists)))
#         if len(artists_list):
#             if isinstance(artists_list[0], QuerySet):
#                 return artists_list[0]
#             elif isinstance(artists_list[0], Artist):
#                 return artists_list
#         return Artist.objects.none()

#     # métodos da classe
#     @staticmethod
#     def new_user(data: dict) -> Optional['CustomUser']:
#         """ Cria e retorna uma instancia de CustomUser com base no email e senha passados em data
#         """
#         try:
#             user = CustomUser(email=data.get('email'), first_name=data.get('first_name'),
#                               last_name=data.get('last_name'), firebase_uid=data.get('firebase_uid'))
#             user.set_password(data.get('password'))
#             user.save()
#             return user
#         except Exception as e:
#             print(e)
#             log_error(e)
#             return None

#     def refresh_facebook_long_lived_token(self):
#         """
#         Atualiza o token de acesso do Facebook do usuário
#         """
#         import requests
#         refresh_url = f'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={FACEBOOK_APP_ID}&client_secret={FACEBOOK_APP_SECRET}&fb_exchange_token={self.facebook_long_lived_token}'
#         response = requests.get(refresh_url)
#         if response.status_code == 200:
#             self.facebook_long_lived_token = response.json().get('access_token')
#             self.facebook_long_lived_token_fetch_date = datetime.now()
#             self.save()
#         else:
#             log_error(f'Erro ao atualizar token de acesso do Facebook do usuário {self.email}')


# class Client(BaseModel):
#     name = models.CharField(verbose_name=t('Nome'), max_length=255, null=True, blank=True)

#     def get_users(self) -> QuerySet['CustomUser']:
#         """Retorna os usuários desse cliente."""
#         return self.customuser_set.all()


# class Subscription(BaseModel):
#     """Modelo de assinatura.

#     Args:
#         BaseModel (models.Model): Modelo Base. Herdamos para poder usar os campos de data padrão dos nossos modelos.
#     """
#     class Types(models.TextChoices):
#         MONTHLY = 'MO', t('Mensal')
#         YEARLY = 'YE', t('Anual')

#     # tipo do plano
#     type = models.CharField(verbose_name=t('Tipo'), max_length=255, null=True, blank=True)
#     # data de expiração
#     expiration_date = models.DateTimeField(verbose_name=t('Data de Expiração'), null=True, blank=True)
#     # inicio da vigencia da assinatura
#     start_date = models.DateTimeField(verbose_name=t('Data de Início'), null=True, blank=True)
#     # valor da assinatura
#     value = models.DecimalField(verbose_name=t('Valor'), max_digits=10, decimal_places=2, null=True, blank=True)
#     # cliente
#     client = models.ForeignKey(Client, verbose_name=t('Cliente'), on_delete=models.CASCADE, null=True, blank=True)

#     def __str__(self):
#         return f'{self.client} - {self.type} - {self.value}' if self.id else ''
    
#     def set_subscription(self) -> None:
#         """Preenche os dados de uma assinatura com base nos planos definidos no arquivo json.
#         """
#         import json
#         from datetime import timedelta
#         from django.conf import settings
#         from django.utils import timezone

#         # carrega o arquivo de planos
#         with open(settings.BASE_DIR / 'subscription/plans.json', 'r') as f:
#             plans = json.load(f)

#         # pega o plano do cliente
#         plan = plans.get(self.client.type)

#         # se o plano não existir, retorna
#         if not plan:
#             return

#         # pega o valor da assinatura
#         self.value = plan.get('value')

#         # pega a data de inicio da assinatura
#         self.start_date = timezone.now()

#         # pega a data de expiração da assinatura
#         self.expiration_date = self.start_date + timedelta(days=plan.get('duration'))

#         # salva a assinatura
#         self.save()
        

# class CustomGroup(BaseModel, BasePermissionClass):
#     """
#     Modelo de Grupo customizado para ser ligado a um Cliente, e o Cliente poder gerenciar seus grupos de permissão.
#     Teremos alguns grupos pré-definidos que serão atribuídos ao Cliente quando ele for criado/assinar algum plano.
#     Nessa classe não será feito override do método get_queryset para que a filtragem por manager seja feita pelo DRF.
#     """
#     name = models.CharField(t('Nome'), max_length=150, unique=True)
#     permissions = models.ManyToManyField(
#         Permission,
#         verbose_name=t('Permissões'),
#         blank=True,
#     )
#     # manager = models.ForeignKey(to=Manager, on_delete=models.PROTECT, verbose_name=t('Cliente'))

#     class Meta:
#         verbose_name = t('Grupo de Permissões')
#         verbose_name_plural = t('Grupos de Permissões')
#         ordering = ('name',)

#     def __str__(self):
#         return self.name
