def get_partner_from_request(request):
    """
    Pega o parceiro com base na request. Supõe-se que a request já passou pelo Middleware e que o campo request.manager
    esteja disponível.
    Args:
        request: Requisição HTTP

    Returns:
        Objeto do tipo Partner
    """
    from django.apps import apps
    user_id = request.user.id
    manager_id = request.current_manager or 1
    return apps.get_model('core', 'Partner').objects.get(user_id=user_id, manager_id=manager_id)