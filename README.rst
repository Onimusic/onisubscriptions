================
OniSubscriptions
================

OniSubscriptions é um aplicativo criado para realizar a gestão de assinaturas de um App Django.

Quick Start
===========

1. Adicione o app "subscription" no seu INSTALED_APPS no settings.py do seu projeto.

    INSTALED_APPS = (
        ...
        'subscription',
        ...
    )

2. Adicione a url do app no urls.py do seu projeto.

    path('subscriptions/', include('subscription.urls', namespace='subscription')),

3. Rode o comando `python manage.py migrate` para criar as tabelas no banco de dados.
