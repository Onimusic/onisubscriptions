================
OniSubscriptions
================

OniSubscriptions é um aplicativo criado para realizar a gestão de assinaturas de um App Django.

Dependências
============

* Python (>= 3.6)
* Django (>= 3.2.23)
* Onipkg Contrib (>= 1.2b)
* Django Rest Framework (>= 3.14)
* Django Rest Framework Simple JWT (>= 5.2.2)
* Django Rest Password Reset (>= 1.3.0)

Certifique-se de que o Onipkg Contrib esteja instalado no seu projeto.

    pip install git+https://github.com/Onimusic/onipkg_contrib.git@v1.2b


Quick Start
===========

1. Adicione o app "subscription" no seu INSTALED_APPS no settings.py do seu projeto.

    INSTALED_APPS = (
        ...
        'subscription',
        ...
    )

2. Faça a implementação das classes Abstratas criando os relacionamentos.

    class CustomUser(AbstractCustomUser):
        ...

3. Adicione a classe CustomUser no settings.py do seu projeto.

    AUTH_USER_MODEL = 'subscription.CustomUser'

4. Rode o comando `python manage.py makemigrations` para criar as migrações.


Para Desenvolvedores
====================

O pacote pode ser estendido e testado da seguinte forma:

1. Clone o repositório do projeto.

    git clone

2. Crie um ambiente virtual e instale as dependências.

    python -m venv venv
    pip install -r requirements.txt

3. Modifique o código.

4. Altere a versão do pacote no arquivo `setup.cfg`.

5. Faça o build do pacote.

    python setup.py sdist bdist_wheel

6. Instale o pacote no seu projeto.

    pip install dist/onipkg_contrib_subscription-<versão>.tar.gz

7. Teste o pacote.
