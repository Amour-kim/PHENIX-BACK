from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import UserRole
from .serializers import (
    UserSerializer, 
    UserCreateSerializer, 
    UserUpdateSerializer,
    UserRoleSerializer
)

from django.contrib.auth import get_user_model
User = get_user_model()

class UserRoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les rôles utilisateur.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'is_active']

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les utilisateurs.
    """
    queryset = User.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined', 'last_login']
    
    def get_serializer_class(self):
        """
        Retourne la classe de sérialiseur appropriée selon l'action.
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """
        Instancie et retourne la liste des permissions requises pour cette vue.
        """
        if self.action in ['create', 'login', 'test_connection']:
            permission_classes = [AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Restreint les utilisateurs retournés à l'utilisateur actuellement authentifié,
        sauf pour les administrateurs qui peuvent voir tous les utilisateurs.
        """
        queryset = User.objects.all().select_related('role')
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
            
        if not user.is_staff:
            # Les utilisateurs normaux ne voient que leur propre profil
            queryset = queryset.filter(id=user.id)
            
        return queryset
        
    def retrieve(self, request, *args, **kwargs):
        """
        Récupère un utilisateur spécifique avec ses relations.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
        
    def create(self, request, *args, **kwargs):
        """
        Crée un nouvel utilisateur avec le sérialiseur approprié.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserSerializer(serializer.instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
        
    def update(self, request, *args, **kwargs):
        """
        Met à jour un utilisateur existant.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserSerializer(instance).data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Authentifie un utilisateur et retourne les informations de session.
        """
        from django.middleware.csrf import get_token

        username = request.data.get('username')
        password = request.data.get('password')
        
        print(username, password)

        if not User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Veuillez fournir un nom d\'utilisateur et un mot de passe correct!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier si l'utilisateur est déjà connecté
        if request.user.is_authenticated:
            return Response({
                'message': 'Déjà connecté',
                'user': UserSerializer(request.user).data,
                'is_staff': request.user.is_staff,
                'sessionid': request.session.session_key
            }, status=status.HTTP_200_OK)
              
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Sauvegarder la session avant la connexion
                if not request.session.session_key:
                    request.session.save()
                
                # Connecter l'utilisateur
                login(request, user)
                
                # Régénérer le token CSRF
                get_token(request)
                
                return Response(
                    {
                        'message': 'Connexion réussie',
                        'user': UserSerializer(user).data,
                        'is_staff': user.is_staff,
                        'sessionid': request.session.session_key,
                        'csrf_token': request.META.get('CSRF_COOKIE')
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Ce compte est désactivé'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Identifiants invalides'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Déconnecte l'utilisateur et supprime la session.
        """
        logout(request)
        response = Response(
            {'message': 'Déconnexion réussie'},
            status=status.HTTP_200_OK
        )
        # Supprimer les cookies de session
        response.delete_cookie('sessionid')
        response.delete_cookie('csrftoken')
        return response
        
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """
        Envoie un email de réinitialisation de mot de passe.
        """
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.core.mail import send_mail
        from django.conf import settings
        
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Ne pas révéler si l'email existe ou non pour des raisons de sécurité
            return Response(
                {'message': 'Si un compte avec cet email existe, un email de réinitialisation a été envoyé'},
                status=status.HTTP_200_OK
            )
            
        # Générer un token de réinitialisation
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Envoyer l'email (à implémenter selon votre configuration d'email)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        send_mail(
            'Réinitialisation de votre mot de passe',
            f'Pour réinitialiser votre mot de passe, cliquez sur le lien suivant: {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return Response(
            {'message': 'Un email de réinitialisation a été envoyé à votre adresse email'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Permet à un utilisateur de changer son mot de passe.
        """
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentification requise'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not all([old_password, new_password]):
            return Response(
                {'error': 'Ancien et nouveau mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Vérifier l'ancien mot de passe
        if not user.check_password(old_password):
            return Response(
                {'error': 'Ancien mot de passe incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Changer le mot de passe
        user.set_password(new_password)
        user.save()
        
        # Mettre à jour la session pour éviter la déconnexion
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        
        return Response(
            {'message': 'Mot de passe mis à jour avec succès'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def activate(self, request, uidb64=None, token=None):
        """
        Active un compte utilisateur avec un token de validation.
        """
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        from django.contrib.auth.tokens import default_token_generator
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response(
                {'message': 'Compte activé avec succès'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Lien d\'activation invalide ou expiré'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def resend_activation(self, request):
        """
        Renvoie l'email d'activation du compte.
        """
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.core.mail import send_mail
        from django.conf import settings
        
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response(
                {'error': 'Aucun compte inactif trouvé avec cet email'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Générer un token d'activation
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Envoyer l'email d'activation
        activate_url = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
        send_mail(
            'Activez votre compte',
            f'Pour activer votre compte, cliquez sur le lien suivant: {activate_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return Response(
            {'message': 'Email d\'activation renvoyé avec succès'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def test_connection(self, request):
        from django.contrib.sessions.backends.db import SessionStore
        from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
        from django.middleware.csrf import get_token
        from django.utils import timezone
        
        # Récupérer la clé de session depuis les cookies ou l'en-tête
        session_key = request.COOKIES.get('sessionid') or request.META.get('HTTP_X_SESSIONID')
        
        # Débogage initial
        print("\n=== Debug test_connection ===")
        print(f"Request method: {request.method}")
        print(f"Session key from cookies/header: {session_key}")
        print(f"Request user: {request.user} (authenticated: {request.user.is_authenticated})")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request cookies: {request.COOKIES}")
        
        # Initialiser la session si elle n'existe pas
        if not hasattr(request, 'session') or not request.session.session_key:
            if session_key:
                # Essayer de charger la session existante
                session = SessionStore(session_key=session_key)
                if session.exists(session_key):
                    request.session = session
                    request.session['last_activity'] = str(timezone.now())
                    print(f"Session chargée depuis la base de données: {session_key}")
                else:
                    request.session = SessionStore()
                    request.session.create()
                    session_key = request.session.session_key
                    print(f"Nouvelle session créée: {session_key}")
            else:
                request.session = SessionStore()
                request.session.create()
                session_key = request.session.session_key
                print(f"Nouvelle session créée (pas de session existante): {session_key}")
        
        # Mettre à jour la dernière activité
        request.session['last_activity'] = str(timezone.now())
        request.session.modified = True
        
        # Vérifier si l'utilisateur est authentifié
        is_authenticated = request.user.is_authenticated
        user_data = None
        
        if is_authenticated:
            # Récupérer les données utilisateur
            user_data = UserSerializer(request.user).data
            
            # S'assurer que la session contient les informations d'authentification
            if not request.session.get('_auth_user_id'):
                print("Mise à jour des informations d'authentification dans la session")
                request.session[SESSION_KEY] = str(request.user.id)
                request.session[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.ModelBackend'
                request.session[HASH_SESSION_KEY] = request.user.get_session_auth_hash()
                request.session.save()
        
        # Préparer la réponse
        response_data = {
            'is_authenticated': is_authenticated,
            'user': user_data,
            'sessionid': request.session.session_key,
            'timestamp': str(timezone.now()),
            'csrf_token': get_token(request)
        }
        
        # Débogage final
        print(f"Session ID final: {request.session.session_key}")
        print(f"Données de session: {dict(request.session)}")
        print(f"Auth user ID: {request.session.get('_auth_user_id')}")
        print("=== Fin du débogage ===\n")
        
        # Créer la réponse avec les en-têtes appropriés
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Configurer les en-têtes CORS
        origin = request.headers.get('Origin')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization, X-SessionID'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        
        # Configurer les cookies de session
        response.set_cookie(
            'sessionid',
            request.session.session_key,
            httponly=True,
            samesite='Lax',
            secure=False,  # À mettre à True en production avec HTTPS
            max_age=1209600 if is_authenticated else None,  # 2 semaines si authentifié
            path='/'  # Important pour que le cookie soit envoyé sur toutes les routes
        )
        
        # Ajouter le token CSRF dans les cookies pour le frontend
        response.set_cookie(
            'csrftoken',
            get_token(request),
            samesite='Lax',
            secure=False  # À mettre à True en production avec HTTPS
        )
        
        return response
