from abc import ABC

from django.contrib.auth.hashers import make_password

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.authtoken.models import Token


from rest_framework_jwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from subscriptions.serializers import UserMembershipSerializer
from xrpwallet.serializers import UserXrpWalletDetailSerializer
from .models import User, Profile
from beats.validators import (
    FileExtensionValidator
)
from beats.utils import get_username_unique_slug


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'username_slug', 'full_name', 'avatar', 'cover_photo', 'bio', 'location',
                  'birth_date', 'blue_tick_verified', 'website_link', 'instagram_link', 'facebook_link',
                  'twitter_link', 'youtube_link', 'followers_count', 'following_count',
                  'track_count', 'get_subscription_badge']


class ChildProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile

        fields = ['id', 'username', 'username_slug', 'avatar', 'blue_tick_verified', 'followers_count',
                  'following_count', 'track_count', 'get_subscription_badge']


class SecondChildProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'username_slug', 'avatar', 'get_subscription_badge']


class ChildFullUserSerializer(serializers.ModelSerializer):
    user_xrp_wallet = UserXrpWalletDetailSerializer(read_only=True)
    profile = ChildProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'profile', 'user_xrp_wallet')


class GetFullUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    user_xrp_wallet = UserXrpWalletDetailSerializer(read_only=True)
    membership_plan = UserMembershipSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'username_slug', 'first_name', 'last_name', 'email', 'profile',
                  'membership_plan', 'is_staff', 'user_xrp_wallet')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def get_user_data(self, user):
        serializer = GetFullUserSerializer(user)
        return serializer.data

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom data to the response
        user = self.user

        data['user'] = self.get_user_data(user)

        return data


class UserSerializerWithToken(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    membership_plan = UserMembershipSerializer(read_only=True)
    phone_number = PhoneNumberField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'username_slug', 'first_name', 'last_name', 'phone_number', 'email', 'password',
            'profile',
            'membership_plan', 'algorand_public_address')
        extra_kwargs = {'password': {'write_only': True}}

    # def validate_password(self, value: str) -> str:
    #     return make_password(value)

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        token = Token.objects.create(user_id=user.id)
        user.email_verification_token = token.key
        user.save()
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True, validators=[FileExtensionValidator('image')])
    cover_photo = serializers.ImageField(required=True, validators=[FileExtensionValidator('image')])
    user = GetFullUserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'bio', 'location', 'birth_date', 'cover_photo', 'avatar', 'website_link', 'instagram_link',
                  'facebook_link',
                  'twitter_link', 'youtube_link']


# Email Verification Code
class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(read_only=True)


class ResetPasswordSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, write_only=True, allow_blank=True)
    email = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)


# send email to users about important notification.
class Important_Notification(serializers.Serializer):
    body = serializers.CharField(max_length=999)
