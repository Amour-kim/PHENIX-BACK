from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserRoleViewSet
from django.urls import path, include

# Initialisation du routeur
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'user-roles', UserRoleViewSet, basename='user-role')

# URLs personnalisées pour l'authentification et la gestion des utilisateurs
urlpatterns = [
    # Routes du routeur (CRUD pour users et user-roles)
    path('', include(router.urls)),
    
    # Token CSRF
    # path('auth/csrf/', get_csrf_token, name='get-csrf'),
    
    # Authentification
    path('auth/register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('auth/login/', UserViewSet.as_view({'post': 'login'}), name='login'),
    path('auth/logout/', UserViewSet.as_view({'post': 'logout'}), name='logout'),
    path('auth/me/', UserViewSet.as_view({'get': 'test_connection'}), name='current-user'),
    
    # Gestion des comptes
    path('auth/password/reset/', UserViewSet.as_view({'post': 'reset_password'}), name='password-reset'),
    path('auth/password/change/', UserViewSet.as_view({'post': 'change_password'}), name='password-change'),
    
    # Activation du compte
    path('auth/activate/<uidb64>/<token>/', 
         UserViewSet.as_view({'post': 'activate'}), 
         name='account-activate'),
    path('auth/activate/resend/', 
         UserViewSet.as_view({'post': 'resend_activation'}), 
         name='resend-activation'),
]