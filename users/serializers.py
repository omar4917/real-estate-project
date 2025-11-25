from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "mobile_number", "date_of_birth", "is_staff")
        read_only_fields = ("id", "is_staff")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ("email", "password", "confirm_password", "first_name", "last_name", "mobile_number", "date_of_birth")

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm = attrs.pop("confirm_password", None)
        if confirm is not None and password != confirm:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), username=identifier, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        attrs["user"] = user
        return attrs
