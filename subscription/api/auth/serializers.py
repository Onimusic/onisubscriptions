from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.utils.translation import gettext as _
from rest_framework_simplejwt.tokens import RefreshToken

from subscription.models import UserProfile, SystemUser, Customer


class ModifiedTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        # adicionando o campo expires_in
        refresh = self.get_token(self.user)
        data['expires_in'] = int(refresh.access_token.lifetime.total_seconds())
        return data


class ModifiedTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        # adicionando o campo expires_in
        data = super().validate(attrs)
        refresh = RefreshToken(attrs['refresh'])
        data['expires_in'] = int(refresh.access_token.lifetime.total_seconds())
        return data


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(
        queryset=get_user_model().objects.all())])
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password': _('Senhas não coincidem.')})
        return attrs

    def create(self, validated_data):
        user = get_user_model().objects.create(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
        )
        user.set_password(validated_data.get('password'))
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('user', 'client', 'allowed_actions')


class SystemUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
        ]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'owner',
        ]
