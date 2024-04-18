from typing import Optional, List

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as t
from django.contrib.auth.models import AbstractUser, Permission
from django.contrib.auth.base_user import BaseUserManager

from onipkg_contrib.log_helper import log_error
from onipkg_contrib.models.base_model import BaseModel
from subscription.utils.utils import BasePermissionClass


class AllowedActions(models.TextChoices):
    ADMINISTRATOR = 'ADM', t(
        'Administrador. Pode ver, criar, alterar e apagar tudo.')
    EDITOR = 'EDT', t(
        'Editor. Pode ver, criar e alterar tudo, mas sem apagar.')
    VIEWER = 'VIE', t(
        'Visualizador. Pode ver tudo, mas sem criar, alterar ou apagar.')

    @classmethod
    def get_delete_permissions(cls) -> List[str]:
        """ Retorna o(s) código(s) de role que pode realizar ações do tipo DELETE """
        return [cls.ADMINISTRATOR]

    @classmethod
    def get_update_permissions(cls) -> List[str]:
        """ Retorna o(s) código(s) de role que pode realizar ações do tipo UPDATE """
        return [cls.ADMINISTRATOR, cls.EDITOR]

    @classmethod
    def get_create_permissions(cls) -> List[str]:
        """ Retorna o(s) código(s) de role que pode realizar ações do tipo CREATE """
        return [cls.ADMINISTRATOR, cls.EDITOR]

    @classmethod
    def get_read_permissions(cls) -> List[str]:
        """ Retorna o(s) código(s) de role que pode realizar ações do tipo READ """
        return [cls.ADMINISTRATOR, cls.EDITOR, cls.VIEWER]


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


class SystemUser(AbstractUser):
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

    class Meta:
        ordering = ['email', 'id']
        verbose_name = t('Usuário')
        verbose_name_plural = t('Usuários')

    # métodos da classe - Quer herdar precisa implementar esse método
    @staticmethod
    def new_user(data: dict) -> Optional['SystemUser']:
        """ Cria e retorna uma instancia de SystemUser com base no email e senha passados em data
        """
        try:
            user = SystemUser(email=data.get('email'), first_name=data.get('first_name'),
                              last_name=data.get('last_name'))
            user.set_password(data.get('password'))
            user.save()
            return user
        except Exception as e:
            print(e)
            log_error(e)
            return None


class Customer(BaseModel):
    """Classe que representa o cliente do sistema. Possui um dono e pode possuir outros usuários atrelados. Possui um
    ou mais conteúdos pagos (no mínimo possui um conteúdo pago que é a assinatura free).

    Attributes:
        name (models.CharField): Nome do cliente.
    """
    name = models.CharField(verbose_name=t('Nome'), max_length=255, null=True, blank=True)
    owner = models.OneToOneField(to=SystemUser, on_delete=models.PROTECT, verbose_name=t('Dono'))

    class Meta:
        verbose_name = t('Cliente')
        verbose_name_plural = t('Clientes')

    @staticmethod
    def new_customer(data: dict) -> Optional['Customer']:
        """ Cria e retorna uma instancia de Manager com base nos dados passados
        """
        try:
            manager = Customer(**data)
            manager.save()
            return manager
        except Exception as e:
            log_error(e)

    @property
    def quota(self) -> int:
        """
        Indica a quantidade de créditos que esse Manager tem
        Returns:
            Número inteiro representando a quandidade de créditos
        """
        return 100000

    def has_quota(self, amount) -> bool:
        """
        Verifica se o Manager tem os créditos desejados
        Args:
            amount: quantia desejada

        Returns:
            True se a quantidade desejada é menor que a quantidade de créditos que o Manager possui
        """
        return amount <= self.quota

    def use_quota(self, amount) -> None:
        """
        Gasta uma determinada quantia em créditos desse Manager
        Args:
            amount: quantia gasta

        Returns:
            None
        """
        return self.quota - amount

    def get_active_signature(self) -> 'PaidContent':
        """
        Retorna a assinatura ativa do cliente
        """
        active_signatures = self.paidcontent_set.filter(type=PaidContent.Types.SIGNATURE,
                                                        expiration_date__gte=timezone.localtime(timezone.now()))
        if len(active_signatures) > 1:
            if active_signatures.filter(is_exclusive=True).count() > 1:
                raise Exception('Cliente possui mais de uma assinatura exclusiva ativa')
        elif len(active_signatures) == 0:
            # Se o cara nao tiver uma assinatura ativa, coloca ele no plano free automaticamente
            PaidContent.register_purchase('free', self)
        return active_signatures[0]

    @property
    def available_features(self) -> list[str]:
        """
        Retorna a lista de funcionalidades disponíveis para o cliente, com base nas features listadas no json, sob
        o stripe_id que representa a assinatura do cliente
        """
        return [content.get('id') for content in self.get_active_signature().get_data().get('purchased_content', []) if
                content.get('type') == 'feature']


class PaidContent(BaseModel):
    """Modelo conteúdo pago. Pode ser uma assinatura mensal, anual ou uma compra pontual.

    Attributes:
        type (models.CharField): Tipo da assinatura.
        expiration_date (models.DateTimeField): Data de expiração da assinatura.
        start_date (models.DateTimeField): Data de início da assinatura.
        value (models.DecimalField): Valor da assinatura.
    """

    class Types(models.TextChoices):
        SIGNATURE = 'SIG', t('Assinatura')
        ONE_TIME_ONLY = 'OT', t('Compra Pontual')

    customer = models.ForeignKey(to=Customer, on_delete=models.CASCADE, verbose_name=t('Cliente'))
    # tipo do plano
    type = models.CharField(verbose_name=t('Tipo da compra'), max_length=3, null=True, blank=True)
    is_exclusive = models.BooleanField(verbose_name=t('É uma assinatura exclusiva?'), default=False)
    # data de expiração
    expiration_date = models.DateTimeField(verbose_name=t('Vencimento'), null=True, blank=True)
    # inicio da vigencia da assinatura
    start_date = models.DateTimeField(verbose_name=t('Data de Vigor'), null=True, blank=True)
    # valor da assinatura
    value = models.DecimalField(verbose_name=t('Valor pago'), max_digits=10, decimal_places=2, null=True, blank=True)
    # id do conteúdo no Stripe
    stripe_id = models.CharField(verbose_name=t('ID Stripe'), max_length=255)

    class Meta:
        verbose_name = t('Conteúdo Pago')
        verbose_name_plural = t('Conteúdos Pagos')

    def __str__(self):
        return self.stripe_id

    @staticmethod
    def get_products() -> dict:
        """
        Carrega os produtos pagáveis do arquivo json e retorna em formato de dicionário
        """
        import json
        from django.conf import settings
        # carrega o arquivo de planos
        with open(settings.BASE_DIR / 'subscription/plans.json', 'r') as f:
            plans = json.load(f)
        return plans

    def get_data(self) -> dict:
        """
        Pega os dados do produto pagável, compilando informações do json e do bd
        """
        plans = self.get_products()
        plan = plans[self.stripe_id]  # acesso direto proposital p dar keyerror se não existir. se vira aí pra tratar <3
        plan['expiration_date'] = self.expiration_date
        plan['start_date'] = self.start_date
        return plan

    @classmethod
    def register_purchase(cls, stripe_id: str, customer: 'Customer') -> None:
        """ Preenche os dados de uma assinatura com base nos planos definidos no arquivo json.

        Args:
            stripe_id: id do plano no stripe
            customer: objeto customer que realizou a assinatura
        """
        from datetime import timedelta

        plans = cls.get_products()
        # pega o plano do cliente
        plan = plans[stripe_id]

        purchase = cls(customer=customer, stripe_id=stripe_id)
        # pega o valor da assinatura
        purchase.value = plan['value']

        # pega a data de inicio da assinatura
        purchase.start_date = timezone.localtime(timezone.now())

        # calcula a data de vencimento da assinatura
        if expiration_time := plan.get('expiration_time'):
            purchase.expiration_date = purchase.start_date + timedelta(days=expiration_time)

        purchase.type = plan['type']
        purchase.is_exclusive = plan['signature_exclusive']

        # salva a assinatura
        purchase.save()

    def has_expired(self) -> bool:
        """Verifica se a assinatura expirou.

        Returns:
            bool: True se a assinatura expirou, False caso contrário.
        """

        # se a data de expiração for menor que a data atual, retorna que venceu
        if self.expiration_date and self.expiration_date < timezone.localtime(timezone.now()):
            return True

        # se não, retorna q nao venceu
        return False


class UserProfile(BaseModel):
    """ Modelo Many-to-many que liga um usuário a um cliente """
    user = models.OneToOneField(to=SystemUser, on_delete=models.CASCADE, verbose_name=t('Usuário'),
                                related_name='profile')
    client = models.ForeignKey(to=Customer, on_delete=models.CASCADE, verbose_name=t('Cliente'), null=True, blank=True)
    allowed_actions = models.CharField(verbose_name=t('Funcionalidades Acessíveis'),
                                       choices=AllowedActions.choices, default=AllowedActions.ADMINISTRATOR,
                                       max_length=3)
    available_features = models.CharField(verbose_name=t('Funcionalidades Disponíveis'), max_length=255, null=True,
                                          blank=True)

    class Meta:
        verbose_name = t('Perfil de Usuário')
        verbose_name_plural = t('Perfis de Usuários')
        unique_together = ['user', 'client']

    def __str__(self):
        return f'{self.user.email} ({self.client.name})'

    @staticmethod
    def new_profile(data: dict) -> Optional["UserProfile"]:
        """
        Cria e retorna uma instância de perfil com base nos dados passados
        """
        try:
            profile = UserProfile(**data)
            profile.save()
            return profile
        except Exception as e:
            log_error(e)

    def can_read(self) -> bool:
        """ Indica se a instância de usuário tem permissão para READ """
        return self.allowed_actions in AllowedActions.get_read_permissions()

    def can_delete(self) -> bool:
        """ Indica se a instância de usuário tem permissão para DELETE """
        return self.allowed_actions in AllowedActions.get_delete_permissions()

    def can_update(self) -> bool:
        """ Indica se a instância de usuário tem permissão para UPDATE """
        return self.allowed_actions in AllowedActions.get_update_permissions()

    def can_create(self) -> bool:
        """ Indica se a instância de usuário tem permissão para CREATE """
        return self.allowed_actions in AllowedActions.get_create_permissions()

    def get_available_features(self) -> List[str]:
        """ Retorna a lista de códigos das funcionalidades disponíveis pro usuário com base no cliente dele
        """
        # Faz uma interseção pra garantir que o perfil não acesse funcionalidades que o cliente não tem acesso
        return [] if not self.available_features or not self.client else list(
            set(self.client.available_features).intersection(set(self.available_features.split(','))))

    def can_access_feature(self, feature: str) -> bool:
        """ Verifica se o usuário tem acesso a uma determinada funcionalidade
        """
        return feature in self.get_available_features()

    def has_credits(self, price) -> bool:
        """
        Verifica se o usuário pode gastar uma determinada quantia de créditos do Manager dele
        Args:
            price: quantidade de créditos necessária

        Returns:
            True se o usuário puder gastar os créditos desejados
        """
        if not self.client:
            return False
        return self.client.has_quota(price)

    def spend_credits(self, price) -> None:
        """
        Gasta créditos do usuário (pela RN, quem tem crédito é o Manager, então é um Profile que gasta os créditos de
        um Manager)
        Args:
            price: quantidade de créditos gasta

        Returns:
            None
        """
        if not self.client:
            return
        self.client.use_quota(price)
