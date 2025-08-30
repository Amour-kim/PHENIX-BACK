from django.contrib import admin
from .models import User, UserRole
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

# @admin.site.unregister(Group)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'users_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_per_page = 20
    ordering = ('name',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'is_active')
        }),
    )
    
    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = "Nombre d'utilisateurs"

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active',)
    fieldsets = (
        ('Informations authentification', {
            'fields': ('username', 'email', 'password', 'role'),
        }),
        ('Informations Personnelle', {
            'fields': ('last_name', 'first_name', 'profil'),
        }),
        ('Informations Systeme', {
            'fields': ('is_superuser', 'is_active', 'is_staff'),
        }),
        ('Informations Permissions', {
            'fields': ('groups',),
        }),
        ('Informations Permissions supplementaire', {
            'fields': ('user_permissions',),
        }),
    )
    add_fieldsets = (
        ('Informations authentification', {
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
        ('Informations Personnelle', {
            'fields': ('last_name', 'first_name', 'profil'),
        }),
        ('Informations Systeme', {
            'fields': ('is_superuser', 'is_active', 'is_staff'),
        }),
        ('Informations Permissions', {
            'fields': ('groups',),
        }),
        ('Informations Permissions supplementaire', {
            'fields': ('user_permissions',),
        }),
    )
    ordering = ('username',)
    list_per_page = 10

    def save_model(self, request, obj, form, change):
        if not change:
            fichier = request.FILES.get('profil')
            if fichier:
                obj.profil = fichier
            obj.save()
        else:
            super().save_model(request, obj, form, change)

admin.site.site_header = "IOI - Administration"
admin.site.site_title = "IOI - Admin"
admin.site.index_title = "Bienvenue sur l'espace d'administration IOI"
admin.site.site_url = 'http://localhost:3000/'
