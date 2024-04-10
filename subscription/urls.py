from django.urls import path, include
from .api.auth.routes import router as auth_router

app_name = 'subscription'
urlpatterns = [
    path('', include(auth_router)),
]
