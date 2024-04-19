from django.conf.urls import url
from django.urls import path, include
from onipkg_contrib.log_helper import log_tests
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .views import RegisterView, ModifiedTokenRefreshView, ChangePasswordView, ModifiedObtainTokenPairView, \
    UserRegistrationValidator, CompleteSignupView, GetProfileView, ProfileListCreate, ProfileRetrieveUpdateDestroy, \
    UserList, UserRetrieve, CustomerList, CustomerRetrieveUpdate


class StripeWebhookHandler(APIView):
    """
    Registra uma compra de um usuário no sistema. Essa view é chamada pelo webhook do Stripe, que é acionado toda vez
    que um usuário compra alguma coisa nossa por lá. Temos que identificar o usuário que fez a compra, qual foi o
    produto adquirido e registrar isso no sistema, a partir do método PaidContent.register_purchase.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        if request.data.get('type') == 'payment_intent.succeeded':
            description = data.get('data').get('object').get('description')
            client_id, product_id = description.split('-')
            from subscription.models import PaidContent, Customer
            PaidContent.register_purchase(product_id, Customer.objects.get(id=client_id))
        return Response(status=200)


router = [
    path('login/', ModifiedObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', ModifiedTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('register-validate/', UserRegistrationValidator.as_view(), name='auth_register'),
    path('complete-signup/', CompleteSignupView.as_view(), name='complete_signup'),
    # path('google-login/', GoogleLoginApi.as_view(), name='google-login'),
    # path('facebook-login/', FacebookLoginApi.as_view(), name='google-login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('get-profile', GetProfileView.as_view()),
    path('profiles', ProfileListCreate.as_view()),
    path('profiles/<pk>', ProfileRetrieveUpdateDestroy.as_view()),
    path('users', UserList.as_view()),
    path('users/<pk>', UserRetrieve.as_view()),
    path('customers', CustomerList.as_view()),
    path('customers/<pk>', CustomerRetrieveUpdate.as_view()),
    path('register-purchase', StripeWebhookHandler.as_view(), name='stripe-webhook-register-purchase'),
    url(r'^u/change-password/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]
