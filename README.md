# OniSubscriptions

Pacote para gerenciamento de assinatura dos projetos Oni. Ao instalar esse pacote, você terá acesso a configurações de
autenticação e autorização de usuários via API, contendo suporte ao Stripe e endpoints para todo o tramit de usuários e
clientes (para aplicações onde um cliente pode ter mais de um usuário atrelado).

## Get Started
Para instalar o pacote, execute o comando `pip install git+https://github.com/Onimusic/onisubscriptions.git@<version>`, 
onde <version> é o nome da release que deseja instalar.

Adicione a linha `'subscription',` no array `INSTALLED_APPS` do arquivo `settings/base.py` do seu projeto.

Execute o comando `python manage.py migrate` para criar as tabelas necessárias.

Com o migrate, você terá criado as tabelas de usuário (SystemUser), perfil (UserProfile), cliente (Customer) e assinatura (PaidContent).

Para ter acesso aos endpoints de cadastro e login, adicione o path a seguir no `urlpatterns` do arquivo `urls.py` base do seu projeto:
```python
path('auth/', include('subscription.urls', namespace='subscription')),
```

Para configurar o envio de emails, adicione o trecho a seguir nas suas configurações do ansible de acordo com o seu provedor de email:
```python
DEFAULT_FROM_EMAIL = 'postmaster@sandbox80775ca84f734d1298805a8c1c27c481.mailgun.org'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = '465'
EMAIL_HOST_USER = 'postmaster@sandbox80775ca84f734d1298805a8c1c27c481.mailgun.org'
EMAIL_HOST_PASSWORD = '8ad2c1b4d1201ef0068d1e3f426f542c-6d1c649a-ba602d02'
EMAIL_USE_SSL = True
```

Se a sua aplicação for permitir que um cliente tenha mais de um usuário, adicione o trecho a seguir nas suas configurações:
`DJANGO_REST_MULTITOKENAUTH_REQUIRE_USABLE_PASSWORD = False`
Isso vai permitir que noos usuários sejam convidados pelo administrador do cliente.

### Cadastro de usuários
O cadastro de usuários é feito em duas etapas separadas: a criação do usuário e a criação do cliente/perfil.
#### 1. Criação do usuário:
Para criar um usuário, faça uma requisição POST para o endpoint `/register` com os campos `email`, `password` e `first_name` no corpo da requisição.
Nesse ponto o usuário será criado e ele receberá um email de boas vindas que pode ser customizado pela sua aplicação. O 
usuário ainda não possuirá um perfil nem um cliente e portanto ainda não deve conseguir usar o sistema, mas deve conseguir logar.
#### 2. Criação do cliente/perfil:
Para criar um cliente e o perfil do usuário recém-criado, faça uma requisição POST para o endpoint `/complete-signup` com o campo
`client_name` no corpo da requisição. Nesse ponto o cliente e o perfil do usuário serão criados e o usuário poderá logar 
e acessar o sistema. O cliente será criado com o plano free e o perfil com todas as permissões de acesso (pois entende-se 
que o criador do cliente é o seu administrador e portanto pode fazer tudo que estiver disponível no plano free).

### Convidando novos usuários para um cliente já existente
Para adicionar usuários em um cliente que já existe, envie uma requisição POST para o endpoint `/profiles` com os campos 
`user_email`, `user_name` e `allowed_actions` no corpo da requisição. Se o usuário não existir no BD, ele receberá um email com
o convite para ativar sua conta. Em paralelo a isso, o backend criará o usuário com uma senha inativa e gerará um token
de reset de senha, que será enviado no email de convite. O usuário deverá clicar no link do email para resetar sua senha,
e assim, ativar sua conta. O perfil será criado para o cliente que o usuário da requisição está acessando no momento da
requisição.

## Os Modelos
Em primeiro lugar, é importante mencionar que todos os modelos que herdarem de BaseModel estarão sujeitos ao `Soft Delete`.
Na prática, isso significa que ao invocar o método delete() desses objetos, eles não serão propriamente deletados do banco
de dados, mas sim marcados como deletados (`deleted=True`). Fique atento a isso.

Em segundo lugar, atente-se para o fato de que todos os objetos que estejam sujeitos a permissões de acesso devem herdar
de BasePermissionClass. Isso é necessário para que o sistema possa verificar se o perfil do usuário tem permissão de acesso
ao módulo relacionado àquele objeto. Ao herdar dessa classe, os objetos ganham um método `get_queryset` que por padrão
retorna `cls.objects.all()`. Caso você queira filtrar os objetos que um usuário pode ver, você deve sobrescrever esse método
com o filtro que atenda à RN em questão.

Esse pacote conta com modelos base para gerenciar usuários, perfis, clientes e assinaturas. A seguir, uma breve descrição
de cada um deles:

### SystemUser
Modelo de usuário. Herda de AbstractUser do Django. Esse modelo é responsável por armazenar os dados
de autenticação do usuário, como email e senha. Ele também armazena o nome do usuário e a data de criação do objeto.
A customização do modelo User do Django se deve ao fato de que queremos que o email seja o campo de autenticação do usuário,
abandonando completamente o campo padrão do django `username`. 

### UserProfile
Modelo de perfil. Herda de BaseModel. Esse modelo é responsável por armazenar as permissões de acesso do usuário e o cliente
ao qual ele está atrelado. O campo `allowed_actions` indica se o usuário terá permissão de leitura, escrita, criação ou deleção
nos módulos ao qual o administrador do cliente lhe conceder acesso. Por exemplo, se ele tiver acesso aos módulos X e Y e
permissões de leitura e escrita, ele poderá ver, criar e alterar objetos de X e Y.

### Customer
Modelo de cliente. Herda de BaseModel. Esse modelo é responsável por armazenar os dados do cliente, como nome e data de criação
do objeto. Ele também armazena o usuário que é seu dono. O cliente é o objeto que agrupa os usuários e perfis. Ele é o objeto
a partir do qual se controla as features que os seus usuários acessam no sistema. Uma assinatura/pagamento é feita em um
cliente por um de seus administradores.

### PaidContent
Modelo de assinatura/pagamento. Herda de BaseModel. Esse modelo é responsável por armazenar os dados de assinatura de um 
cliente. Um PaidContent pode ser uma assinatura de um plano que dá acesso a determinados módulos e determinadas quantidades
de conteúdo; e pode ser também um pagamento por um conteúdo ou quantidade específica de um conteúdo.

## A API
O pacote conta com subclasses customizadas de viewsets, herdadas das classes de viewsets do DRF. Essa herança é feita para
permitir ao cliente o uso das features do DRF e ao mesmo tempo limitar o acesso de perfis a features, de acordo com o 
plano do cliente e permissões definidas no perfil. O código para essas viewsets está em `utils/base_viewsets.py`.

### CustomApiViewFilterClass
Herda de APIView. Caso você esteja escrevendo uma viewset que herdaria de APIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe APIView do DRF. A conferência
de permissão de acesso é feita através do método implementado `check_permissions`. Esse método não precisa ser chamado
manualmente: o DRF o invoca por baixo dos panos, portanto não se preocupe com essa parte. O que você precisa fazer é
definir o atributo `related_module` na sua classe. Esse atributo é uma string que deve conter o nome do módulo relacionado
à feature que a view trata. Ao definí-lo, a classe irá verificar se o perfil tem acesso àquele módulo, e tratar a requisição
de acordo. 

Observação importante: Por ser uma classe mais aberta, ela não faz automaticamente nehuma verificação de permissão de
ação (view, create, update ou delete). A verificação automática é feita apenas de acesso ao módulo especificado em 
`related_module`. Verificações de permissão de ação devem ser feitas manualmente em classes que herdam dessa na medida
do necessário para aquela view.

### CustomListFilterClass
Herda de generics.ListAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma viewset que herdaria
de generics.ListAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe ListAPIView do DRF. Ela filtra automaticamente
os objetos da queryset especificada na definição da classe a partir de um método de listagem customizada, que irá obter
os objetos que o usuário pode ver a partir do método `get_queryset` implementado no modelo de objetos que está sendo listado.
Esse método vem por padrão em modelos que herdem de `BasePermissionClass`, e caso não seja feito o seu override, retornará
por padrão um `cls.objects.all()`.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma ListAPIView normal, sem se preocupar com mais nada
relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo e também
a permissão de leitura do perfil.

### CustomListCreateFilterClass
Herda de generics.ListCreateAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma viewset 
que herdaria de generics.ListCreateAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe ListCreateAPIView do DRF. Ela filtra
automaticamente os objetos da queryset especificada na definição da classe a partir de um método de listagem customizada,
que irá obter os objetos que o usuário pode ver a partir do método `get_queryset` implementado no modelo de objetos que
está sendo listado. Esse método vem por padrão em modelos que herdem de `BasePermissionClass`, e caso não seja feito o seu
override, retornará por padrão um `cls.objects.all()`. A classe também verifica automaticamente se o usuário pode realizar
ações de leitura e criação do objeto desejado.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma ListCreateAPIView normal, sem se preocupar com mais nada
relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo e também
a permissão de criação e leitura do perfil.

## CustomRetrieveFilterClass
Herda de generics.RetrieveAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma viewset que 
herdaria de generics.RetrieveAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe RetrieveAPIView do DRF. Ela obtém o 
objeto desejado após a verificação de permissão de acesso ao módulo e permissão de leitura do perfil.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma RetrieveAPIView normal, sem se preocupar com mais nada
relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo e também
a permissão de leitura do perfil.

## CustomUpdateFilterClass
Herda de generics.UpdateAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma viewset que 
herdaria de generics.UpdateAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe UpdateAPIView do DRF. Ela altera o objeto
apenas se o perfil do usuário tiver permissão de escrita e acesso ao módulo relacionado ao objeto.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma UpdateAPIView normal, sem se preocupar com mais nada
relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo e também
a permissão de escrita do perfil.

## CustomDestroyFilterClass
Herda de generics.DestroyAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma viewset que
herdaria de generics.DestroyAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe DestroyAPIView do DRF. Ela deleta o objeto
apenas se o perfil do usuário tiver permissão de deleção e acesso ao módulo relacionado ao objeto.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma DestroyAPIView normal, sem se preocupar com mais nada
relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo e também
a permissão de deleção do perfil.

## CustomRetrieveUpdateFilterClass
Herda de generics.RetrieveUpdateAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma viewset
que herdaria de generics.RetrieveUpdateAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe RetrieveUpdateAPIView do DRF. Ela obtém e
altera o objeto apenas se o perfil do usuário tiver permissão de leitura (em caso de retrieve) e escrita (em caso de 
update) e acesso ao módulo relacionado ao objeto.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma RetrieveUpdateAPIView normal, sem se preocupar com 
mais nada relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo
e também as permissões de leitura e escrita do perfil, com base na ação realizada (retrieve ou update).

## CustomRetrieveDestroyFilterClass
Herda de generics.RetrieveDestroyAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma viewset
que herdaria de generics.RetrieveDestroyAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe RetrieveDestroyAPIView do DRF. Ela obtém e
deleta o objeto apenas se o perfil do usuário tiver permissão de leitura (em caso de retrieve) e deleção (em caso de
destroy) e acesso ao módulo relacionado ao objeto.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma RetrieveDestroyAPIView normal, sem se preocupar com
mais nada relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo
e também as permissões de leitura e deleção do perfil, com base na ação realizada (retrieve ou destroy).

## CustomRetrieveUpdateDestroyFilterClass
Herda de generics.RetrieveUpdateDestroyAPIView (DRF) e CustomApiViewFilterClass (onisubs). Caso você esteja escrevendo uma
viewset que herdaria de generics.RetrieveUpdateDestroyAPIView, herde dessa classe.

Ao herdar dessa classe, você tem todas as funcionalidades que vêm com a classe RetrieveUpdateDestroyAPIView do DRF. Ela obtém,
altera e deleta o objeto apenas se o perfil do usuário tiver permissão de leitura (em caso de retrieve), escrita (em caso de
update) e deleção (em caso de destroy) e acesso ao módulo relacionado ao objeto.

Ao herdar dessa classe, você como programador deve se preocupar em definir o atributo `related_module`. Para além disso,
pode definir normalmente os demais atributos que atribuiria em uma RetrieveUpdateDestroyAPIView normal, sem se preocupar
com mais nada relativo a permissões do usuário. Por baixo dos panos será feita a conferência de permissão de acesso ao módulo
e também as permissões de leitura, escrita e deleção do perfil, com base na ação realizada (retrieve, update ou destroy).



## Manutenção

### Para gerar os arquivos de distribuíção execute o comando abaixo:
    
```bash
python setup.py sdist bdist_wheel
```
