from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "phone",
            "last_name", "password", "password2"
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        validated_data["is_active"] = True
        user = User.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "full_name": f"{instance.first_name} {instance.last_name}",
            "phone": instance.phone,
            "is_active": instance.is_active,
            "is_staff": instance.is_staff,
            "image": instance.image.url if getattr(instance, "image", None) else None,
            
        }



#  me api 


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name", "phone", "image"
        )

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "full_name": f"{instance.first_name} {instance.last_name}",
            "phone": instance.phone,
            "is_active": instance.is_active,
            "is_staff": instance.is_staff,
            "image": instance.image.url if getattr(instance, "image", None) else None,
        }