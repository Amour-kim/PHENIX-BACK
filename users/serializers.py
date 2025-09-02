from rest_framework import serializers
from .models import User, UserRole

class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'description', 'is_active']
        read_only_fields = ['id']

class UserSerializer(serializers.ModelSerializer):
    # Inclure les détails du rôle au lieu de juste l'ID
    role = UserRoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.all(),
        source='role',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Inclure l'URL de l'image de profil
    profil_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined',
            'last_login', 'profil', 'profil_url', 'role', 'role_id'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_superuser']
        extra_kwargs = {
            'password': {'write_only': True},
            'profil': {'write_only': True}
        }
    
    def get_profil_url(self, obj):
        if obj.profil:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.profil.url)
            return obj.profil.url
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Supprimer les champs sensibles si nécessaire
        if not self.context.get('include_sensitive', False):
            representation.pop('is_superuser', None)
            representation.pop('is_staff', None)
        return representation


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'is_active']
        extra_kwargs = {
            'email': {'required': False},
            'is_active': {'required': False}
        }
