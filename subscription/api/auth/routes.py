from django.conf.urls import url
from django.urls import path, include

from .views import RegisterView, ModifiedTokenRefreshView, ChangePasswordView, ModifiedObtainTokenPairView, \
    UserRegistrationValidator, CompleteSignupView

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
    url(r'^u/change-password/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]
