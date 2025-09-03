from django.db import models
from django.contrib.auth.models import AbstractUser


class UserRole(models.Model):
    """Rôles des utilisateurs"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du rôle")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'role_users'
        verbose_name = "Rôle utilisateur"
        verbose_name_plural = "Rôles utilisateur"
        ordering = ['name']

    def __str__(self):
        return self.name
    
class User(AbstractUser):
    profil = models.ImageField(upload_to="users/images/")
    role = models.ForeignKey(UserRole, on_delete=models.PROTECT, related_name="users", verbose_name="Rôle", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        return f"{self.username} ({self.groups.name})"
