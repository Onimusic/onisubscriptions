from typing import Optional

from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as t
from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.auth.base_user import BaseUserManager

from onipkg_contrib.log_helper import log_error
from onipkg_contrib.models.base_model import BaseModel
from subscription.utils.utils import BasePermissionClass


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user


class AbstractCustomUser(AbstractUser):
    """Classe que representa o usuário personalizado.

    Attributes
        dark_mode (models.BooleanField): Preferência quanto ao uso ou não do tema escuro.
        desired_notifications (models.CharField): Preferência quanto as notificações do usuário.
        system_language (models.CharField): Preferência quanto a linguagem em uso no sistema.
    """

    # Override de campos padrao pra evitar erros de autenticacao
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Ao definir o email como username_field, deve-se tirar ele do required_fields. N sei pq
    username = None
    email = models.EmailField(t('email address'), unique=True)

    objects = CustomUserManager()

    class SystemLanguages(models.TextChoices):
        PORTUGUESE = 'PT', t('Português')
        ENGLISH = 'EN', t('Inglês')
        SPANISH = 'ES', t('Espanhol')

    class Meta:
        abstract = True
        ordering = ['email', 'id']
        verbose_name = t('Usuário')
        verbose_name_plural = t('Usuários')

    # métodos da classe - Quer herdar precisa implementar esse método
    @staticmethod
    def new_user(data: dict) -> Optional['AbstractCustomUser']:
        """ Cria e retorna uma instancia de AbstractCustomUser com base no email e senha passados em data
        """
        try:
            user = AbstractCustomUser(email=data.get('email'), first_name=data.get('first_name'),
                              last_name=data.get('last_name'), firebase_uid=data.get('firebase_uid'))
            user.set_password(data.get('password'))
            user.save()
            return user
        except Exception as e:
            print(e)
            log_error(e)
            return None


class AbstractClient(BaseModel):
    """Classe abstrata que representa o cliente.

    Attributes:
        name (models.CharField): Nome do cliente.
    """
    name = models.CharField(verbose_name=t('Nome'), max_length=255, null=True, blank=True)

    class Meta:
        abstract = True
        verbose_name = t('Cliente')
        verbose_name_plural = t('Clientes')


class AbstractSubscription(BaseModel):
    """Modelo abstrato de assinatura.

    Attributes:
        type (models.CharField): Tipo da assinatura.
        expiration_date (models.DateTimeField): Data de expiração da assinatura.
        start_date (models.DateTimeField): Data de início da assinatura.
        value (models.DecimalField): Valor da assinatura.
    """
    class Types(models.TextChoices):
        MONTHLY = 'MO', t('Mensal')
        YEARLY = 'YE', t('Anual')

    # tipo do plano
    type = models.CharField(verbose_name=t('Tipo'), max_length=2, null=True, blank=True)
    # data de expiração
    expiration_date = models.DateTimeField(verbose_name=t('Data de Expiração'), null=True, blank=True)
    # inicio da vigencia da assinatura
    start_date = models.DateTimeField(verbose_name=t('Data de Início'), null=True, blank=True)
    # valor da assinatura
    value = models.DecimalField(verbose_name=t('Valor'), max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        abstract = True
        verbose_name = t('Assinatura')
        verbose_name_plural = t('Assinaturas')

    def __str__(self):
        return f'{self.client} - {self.type} - {self.value}' if self.id else ''
    
    def set_subscription(self) -> None:
        """Preenche os dados de uma assinatura com base nos planos definidos no arquivo json.
        """
        import json
        from datetime import timedelta
        from django.conf import settings
        from django.utils import timezone

        # carrega o arquivo de planos
        with open(settings.BASE_DIR / 'subscription/plans.json', 'r') as f:
            plans = json.load(f)

        # pega o plano do cliente
        plan = plans.get(self.client.type)

        # se o plano não existir, retorna
        if not plan:
            return

        # pega o valor da assinatura
        self.value = plan.get('value')

        # pega a data de inicio da assinatura
        self.start_date = timezone.now()

        # pega a data de expiração da assinatura
        self.expiration_date = self.start_date + timedelta(days=plan.get('duration'))

        # salva a assinatura
        self.save()

    def has_expired(self) -> bool:
        """Verifica se a assinatura expirou.

        Returns:
            bool: True se a assinatura expirou, False caso contrário.
        """
        from django.utils import timezone

        # se a data de expiração for menor que a data atual, retorna True
        if self.expiration_date < timezone.now():
            return True

        # se não, retorna False
        return False
        

class CustomGroup(BaseModel, BasePermissionClass):
    """
    Modelo de Grupo customizado para ser ligado a um Cliente, e o Cliente poder gerenciar seus grupos de permissão.
    Teremos alguns grupos pré-definidos que serão atribuídos ao Cliente quando ele for criado/assinar algum plano.
    Nessa classe não será feito override do método get_queryset para que a filtragem por manager seja feita pelo DRF.
    """
    name = models.CharField(t('Nome'), max_length=150, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=t('Permissões'),
        blank=True,
    )
    # manager = models.ForeignKey(to=Manager, on_delete=models.PROTECT, verbose_name=t('Cliente'))

    class Meta:
        verbose_name = t('Grupo de Permissões')
        verbose_name_plural = t('Grupos de Permissões')
        ordering = ('name',)

    def __str__(self):
        return self.name
