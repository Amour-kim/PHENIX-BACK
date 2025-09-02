from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta

from .models import (
    # Catégories modulaires
    ProductCategory, ProductUnit, UserRole, UserStatus, EntryType, 
    ExpenseCategory, ExpenseStatus, PaymentMethod, SaleStatus, PaymentStatus,
    
    # Modèles principaux
    Supplier, Customer, Product, TimeSlot,
    
    # Gestion des entrées
    Entry, EntryItem,
    
    # Gestion des dépenses
    RecurringExpense, Expense,
    
    # Gestion des ventes
    Sale, SaleItem, UserTimeSlot
)

from .serializers import (
    # Serializers pour les catégories modulaires
    ProductCategorySerializer, ProductUnitSerializer, UserRoleSerializer, UserStatusSerializer,
    EntryTypeSerializer, ExpenseCategorySerializer, ExpenseStatusSerializer, PaymentMethodSerializer,
    SaleStatusSerializer, PaymentStatusSerializer,
    
    # Serializers principaux
    SupplierSerializer, CustomerSerializer, ProductSerializer, ProductListSerializer,
    TimeSlotSerializer,
    
    # Serializers pour les entrées
    EntrySerializer, EntryCreateUpdateSerializer, EntryItemSerializer,
    
    # Serializers pour les dépenses
    RecurringExpenseSerializer, ExpenseSerializer, ExpenseListSerializer,
    
    # Serializers pour les ventes
    SaleSerializer, SaleListSerializer, SaleCreateUpdateSerializer, SaleItemSerializer,
    
    # Serializers de création
    ProductCreateSerializer, CustomerCreateSerializer, SupplierCreateSerializer,
    
    # Serializers statistiques
    ProductStockAlertSerializer, SalesStatsSerializer, ExpenseStatsSerializer,
    InventoryStatsSerializer, DashboardStatsSerializer, UserTimeSlotSerializer,
    UserTimeSlotCreateUpdateSerializer, UserTimeSlotListSerializer
)


# ================================
# VIEWSETS POUR LES CATÉGORIES MODULAIRES
# ================================

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des catégories de produits"""
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Dépenses par période"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expenses = self.queryset.filter(expense_date__range=[start_date, end_date])
        serializer = self.get_serializer(expenses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Dépenses en retard"""
        today = timezone.now().date()
        overdue_expenses = self.queryset.filter(
            due_date__lt=today,
            status__in=['pending', 'approved']
        )
        serializer = self.get_serializer(overdue_expenses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des dépenses"""
        expenses = self.queryset
        
        summary = {
            'total_expenses': expenses.count(),
            'total_amount': expenses.aggregate(total=Sum('total_amount'))['total'] or 0,
            'average_expense': expenses.aggregate(avg=Avg('total_amount'))['avg'] or 0,
            'expenses_by_category': {},
            'expenses_by_status': {},
            'overdue_count': expenses.filter(
                due_date__lt=timezone.now().date(),
                status__in=['pending', 'approved']
            ).count()
        }
        
        return Response(summary)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def mark_as_paid(self, request, pk=None):
        """Marquer une dépense comme payée"""
        expense = self.get_object()
        
        if expense.status == 'paid':
            return Response(
                {'error': 'Expense is already marked as paid'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expense.status = 'paid'
        expense.payment_date = timezone.now().date()
        expense.updated_by = request.user
        expense.save()
        
        return Response({
            'message': 'Expense marked as paid successfully',
            'expense_id': expense.id,
            'payment_date': expense.payment_date
        })


# ================================
# VIEWSETS POUR LES VENTES
# ================================

class SaleViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des ventes"""
    queryset = Sale.objects.select_related(
        'customer', 'payment_method', 'payment_status', 'status', 'created_by'
    ).prefetch_related('items__product')
    serializer_class = SaleSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer', 'payment_method', 'payment_status', 'status', 'is_take_away']
    search_fields = ['reference', 'customer_name', 'customer_phone', 'notes']
    ordering_fields = ['sale_date', 'total_amount', 'created_at']
    ordering = ['-sale_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return SaleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SaleCreateUpdateSerializer
        return SaleSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        response_data['id'] = serializer.instance.id
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Ventes par période"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sales = self.queryset.filter(sale_date__range=[start_date, end_date])
        serializer = self.get_serializer(sales, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today_sales(self, request):
        """Ventes du jour"""
        today = timezone.now().date()
        today_sales = self.queryset.filter(sale_date=today)
        serializer = self.get_serializer(today_sales, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sales_summary(self, request):
        """Résumé des ventes"""
        sales = self.queryset
        today = timezone.now().date()
        
        summary = {
            'total_sales': sales.count(),
            'total_revenue': sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'average_sale': sales.aggregate(avg=Avg('total_amount'))['avg'] or 0,
            'today_sales': sales.filter(sale_date=today).count(),
            'today_revenue': sales.filter(sale_date=today).aggregate(
                total=Sum('total_amount'))['total'] or 0,
            'pending_payments': sales.filter(payment_status__code='pending').count(),
            'take_away_ratio': self._calculate_take_away_ratio(sales)
        }
        
        return Response(summary)

    def _calculate_take_away_ratio(self, sales):
        """Calcule le ratio de ventes à emporter"""
        total_sales = sales.count()
        if total_sales == 0:
            return 0
        take_away_sales = sales.filter(is_take_away=True).count()
        return round((take_away_sales / total_sales) * 100, 2)

    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """Produits les plus vendus"""
        limit = int(request.query_params.get('limit', 10))
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        top_products = SaleItem.objects.filter(
            sale__sale_date__gte=start_date
        ).values(
            'product__name', 'product__id'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price'),
            sales_count=Count('sale')
        ).order_by('-total_quantity')[:limit]
        
        return Response(list(top_products))

    @action(detail=False, methods=['get'])
    def payment_methods_stats(self, request):
        """Statistiques par méthode de paiement"""
        stats = self.queryset.values(
            'payment_method__name', 'payment_method__code'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('-total_amount')
        
        return Response(list(stats))

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def complete_sale(self, request, pk=None):
        """Finaliser une vente"""
        sale = self.get_object()
        
        if sale.status.code == 'completed':
            return Response(
                {'error': 'Sale is already completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le statut
        completed_status = SaleStatus.objects.get(code='completed')
        sale.status = completed_status
        sale.updated_by = request.user
        sale.save()
        
        # Décrémenter les stocks
        for item in sale.items.all():
            product = item.product
            if product.current_stock >= item.quantity:
                product.current_stock -= item.quantity
                product.save()
            else:
                return Response(
                    {'error': f'Insufficient stock for {product.name}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({
            'message': 'Sale completed successfully',
            'sale_id': sale.id,
            'status': sale.status.name
        })

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def cancel_sale(self, request, pk=None):
        """Annuler une vente"""
        sale = self.get_object()
        reason = request.data.get('reason', 'No reason provided')
        
        if sale.status.code == 'cancelled':
            return Response(
                {'error': 'Sale is already cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le statut
        cancelled_status = SaleStatus.objects.get(code='cancelled')
        sale.status = cancelled_status
        sale.notes = f"{sale.notes or ''}\nCancelled: {reason}"
        sale.updated_by = request.user
        sale.save()
        
        return Response({
            'message': 'Sale cancelled successfully',
            'sale_id': sale.id,
            'reason': reason
        })


class SaleItemViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des articles de ventes"""
    serializer_class = SaleItemSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sale', 'product']
    ordering_fields = ['created_at', 'quantity', 'unit_price', 'total_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = SaleItem.objects.select_related('sale', 'product', 'created_by')
        sale_id = self.request.query_params.get('sale')
        if sale_id:
            queryset = queryset.filter(sale_id=sale_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ================================
# VUES FONCTIONNELLES SPÉCIALISÉES
# ================================

def business_dashboard(request):
    """Vue pour le tableau de bord principal"""
    # Authentication check removed - accessible to all
    
    today = timezone.now().date()
    
    context = {
        'total_products': Product.objects.filter(is_active=True).count(),
        'low_stock_products': Product.objects.filter(
            current_stock__lte=F('alert_threshold'),
            is_active=True
        ).count(),
        'total_customers': Customer.objects.filter(is_active=True).count(),
        'total_suppliers': Supplier.objects.filter(is_active=True).count(),
        'today_sales': Sale.objects.filter(sale_date=today).count(),
        'today_revenue': Sale.objects.filter(sale_date=today).aggregate(
            total=Sum('total_amount'))['total'] or 0,
        'pending_expenses': Expense.objects.filter(status='pending').count(),
        'overdue_expenses': Expense.objects.filter(
            due_date__lt=today,
            status__in=['pending', 'approved']
        ).count(),
        'recent_sales': Sale.objects.order_by('-created_at')[:5],
        'recent_entries': Entry.objects.order_by('-created_at')[:5],
        'user_sales_count': Sale.objects.filter(created_by=request.user).count(),
    }
    return render(request, 'business/dashboard.html', context)


def inventory_report(request):
    """Vue pour le rapport d'inventaire"""
    # Authentication check removed - accessible to all
    
    products = Product.objects.select_related('category', 'unit').filter(is_active=True)
    
    # Calculs
    total_value = sum(
        (product.current_stock * product.purchase_price) 
        for product in products 
        if product.current_stock and product.purchase_price
    )
    
    low_stock_products = products.filter(current_stock__lte=F('alert_threshold'))
    
    context = {
        'products': products,
        'total_products': products.count(),
        'total_inventory_value': total_value,
        'low_stock_products': low_stock_products,
        'categories': ProductCategory.objects.filter(is_active=True),
    }
    return render(request, 'business/inventory_report.html', context)


def sales_analytics(request):
    """Vue pour les analyses de ventes"""
    # Authentication check removed - accessible to all
    
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    sales = Sale.objects.filter(sale_date__gte=last_30_days)
    
    context = {
        'total_sales': sales.count(),
        'total_revenue': sales.aggregate(total=Sum('total_amount'))['total'] or 0,
        'average_sale': sales.aggregate(avg=Avg('total_amount'))['avg'] or 0,
        'sales_by_date': self._get_sales_by_date(sales),
        'top_customers': self._get_top_customers(last_30_days),
        'payment_methods_stats': self._get_payment_methods_stats(sales),
    }
    return render(request, 'business/sales_analytics.html', context)

def _get_sales_by_date(self, sales):
    """Obtient les ventes par date"""
    return sales.values('sale_date').annotate(
        daily_sales=Count('id'),
        daily_revenue=Sum('total_amount')
    ).order_by('sale_date')

def _get_top_customers(self, start_date):
    """Obtient les meilleurs clients"""
    return Customer.objects.annotate(
        total_purchases=Sum('sale__total_amount'),
        sales_count=Count('sale')
    ).filter(
        sale__sale_date__gte=start_date,
        total_purchases__gt=0
    ).order_by('-total_purchases')[:10]

def _get_payment_methods_stats(self, sales):
    """Obtient les statistiques par méthode de paiement"""
    return sales.values(
        'payment_method__name'
    ).annotate(
        count=Count('id'),
        total_amount=Sum('total_amount')
    ).order_by('-total_amount')


# ================================
# VUES API CUSTOM POUR RECHERCHE AVANCÉE
# ================================

@api_view(['GET'])
@permission_classes([AllowAny])
def advanced_product_search(request):
    """Recherche avancée de produits avec filtres multiples"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category_id', '')
    low_stock_only = request.GET.get('low_stock', '').lower() == 'true'
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    queryset = Product.objects.select_related('category', 'unit').filter(is_active=True)
    
    # Recherche textuelle
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(barcode__icontains=query)
        )
    
    # Filtre par catégorie
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    # Filtre par stock faible
    if low_stock_only:
        queryset = queryset.filter(current_stock__lte=F('alert_threshold'))
    
    # Filtre par prix
    if min_price:
        try:
            queryset = queryset.filter(selling_price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            queryset = queryset.filter(selling_price__lte=float(max_price))
        except ValueError:
            pass
    
    serializer = ProductListSerializer(queryset, many=True)
    return Response({
        'count': queryset.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def business_statistics(request):
    """Statistiques générales de l'entreprise"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Statistiques de ventes
    sales = Sale.objects.all()
    recent_sales = sales.filter(sale_date__gte=last_30_days)
    
    # Statistiques de dépenses
    expenses = Expense.objects.all()
    recent_expenses = expenses.filter(expense_date__gte=last_30_days)
    
    # Statistiques d'inventaire
    products = Product.objects.filter(is_active=True)
    low_stock_products = products.filter(current_stock__lte=F('alert_threshold'))
    
    stats = {
        'sales': {
            'total': sales.count(),
            'recent': recent_sales.count(),
            'total_revenue': sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'recent_revenue': recent_sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'average_sale': sales.aggregate(avg=Avg('total_amount'))['avg'] or 0,
        },
        'expenses': {
            'total': expenses.count(),
            'recent': recent_expenses.count(),
            'total_amount': expenses.aggregate(total=Sum('total_amount'))['total'] or 0,
            'recent_amount': recent_expenses.aggregate(total=Sum('total_amount'))['total'] or 0,
            'pending': expenses.filter(status='pending').count(),
            'overdue': expenses.filter(
                due_date__lt=today,
                status__in=['pending', 'approved']
            ).count(),
        },
        'inventory': {
            'total_products': products.count(),
            'low_stock_alerts': low_stock_products.count(),
            'total_value': sum(
                (product.current_stock * product.purchase_price) 
                for product in products 
                if product.current_stock and product.purchase_price
            ),
            'categories_count': ProductCategory.objects.filter(is_active=True).count(),
        },
        'customers': {
            'total': Customer.objects.filter(is_active=True).count(),
            'active_customers': Customer.objects.filter(
                sale__sale_date__gte=last_30_days
            ).distinct().count(),
        },
        'suppliers': {
            'total': Supplier.objects.filter(is_active=True).count(),
            'active_suppliers': Supplier.objects.filter(
                entry__entry_date__gte=last_30_days
            ).distinct().count(),
        }
    }
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_sales_report(request):
    """Générer un rapport de ventes pour une période donnée"""
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    format_type = request.data.get('format', 'json')  # json, csv, pdf
    
    if not start_date or not end_date:
        return Response(
            {'error': 'start_date and end_date are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    sales = Sale.objects.filter(
        sale_date__range=[start_date, end_date]
    ).select_related('customer', 'payment_method', 'status').prefetch_related('items')
    
    report_data = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary': {
            'total_sales': sales.count(),
            'total_revenue': sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'average_sale': sales.aggregate(avg=Avg('total_amount'))['avg'] or 0,
        },
        'sales': SaleSerializer(sales, many=True).data,
        'generated_at': timezone.now().isoformat(),
        'generated_by': request.user.username
    }
    
    if format_type == 'json':
        return Response(report_data)
    else:
        return Response(
            {'error': 'Only JSON format is currently supported'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def low_stock_alerts(request):
    """Alertes de stock bas avec détails"""
    threshold_multiplier = float(request.GET.get('threshold_multiplier', 1.0))
    
    low_stock_products = Product.objects.select_related('category', 'unit').filter(
        current_stock__lte=F('alert_threshold') * threshold_multiplier,
        is_active=True
    ).annotate(
        stock_difference=F('alert_threshold') - F('current_stock'),
        days_remaining=Case(
            When(current_stock__lte=0, then=0),
            default=F('current_stock') / 10,  # Estimation basée sur consommation moyenne
            output_field=models.IntegerField()
        )
    )
    
    alerts = []
    for product in low_stock_products:
        alert_level = 'critical' if product.current_stock <= 0 else 'warning'
        if product.current_stock <= (product.alert_threshold * 0.5):
            alert_level = 'urgent'
        
        alerts.append({
            'product': ProductListSerializer(product).data,
            'current_stock': product.current_stock,
            'alert_threshold': product.alert_threshold,
            'stock_difference': product.stock_difference,
            'estimated_days_remaining': product.days_remaining,
            'alert_level': alert_level,
            'suggested_order_quantity': max(
                product.alert_threshold * 2 - product.current_stock, 
                0
            )
        })
    
    return Response({
        'total_alerts': len(alerts),
        'critical_alerts': len([a for a in alerts if a['alert_level'] == 'critical']),
        'urgent_alerts': len([a for a in alerts if a['alert_level'] == 'urgent']),
        'warning_alerts': len([a for a in alerts if a['alert_level'] == 'warning']),
        'alerts': alerts
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_update_products(request):
    """Mise à jour en lot des produits"""
    product_ids = request.data.get('product_ids', [])
    updates = request.data.get('updates', {})
    
    if not product_ids or not updates:
        return Response(
            {'error': 'product_ids and updates are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Filtrer les champs autorisés pour la mise à jour en lot
    allowed_fields = ['is_active', 'alert_threshold', 'selling_price', 'category']
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        return Response(
            {'error': 'No valid fields provided for update'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    products = Product.objects.filter(id__in=product_ids)
    updated_count = products.update(**filtered_updates, updated_by=request.user)
    
    return Response({
        'updated_count': updated_count,
        'message': f'{updated_count} products updated successfully',
        'updated_fields': list(filtered_updates.keys())
    })


# ================================
# VUES POUR LA VALIDATION ET REPORTING
# ================================

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_sale_data(request):
    """Valide les données d'une vente avant création/modification"""
    sale_data = request.data.get('sale_data', {})
    items_data = request.data.get('items_data', [])
    
    errors = []
    warnings = []
    
    # Validation des données de base
    if not sale_data.get('customer') and not sale_data.get('customer_name'):
        errors.append('Customer or customer name is required')
    
    if not sale_data.get('payment_method'):
        errors.append('Payment method is required')
    
    if not items_data:
        errors.append('At least one item is required')
    
    # Validation des articles et vérification du stock
    total_estimated = 0
    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        
        if not product_id:
            errors.append('Product ID is required for each item')
            continue
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            if product.current_stock < quantity:
                warnings.append(
                    f'Insufficient stock for {product.name}. Available: {product.current_stock}, Required: {quantity}'
                )
            
            total_estimated += product.selling_price * quantity
            
        except Product.DoesNotExist:
            errors.append(f'Product with ID {product_id} not found')
    
    validation_result = {
        'is_valid': len(errors) == 0,
        'estimated_total': total_estimated,
        'errors': errors,
        'warnings': warnings,
        'items_count': len(items_data),
        'ready_for_processing': len(errors) == 0
    }
    
    return Response(validation_result)


@api_view(['GET'])
@permission_classes([AllowAny])
def export_data(request):
    """Export général des données en JSON"""
    export_type = request.GET.get('type', 'all')  # all, products, customers, sales, expenses
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    export_data = {
        'export_info': {
            'type': export_type,
            'generated_at': timezone.now().isoformat(),
            'generated_by': request.user.username,
            'period': None
        }
    }
    
    # Gestion des filtres par date si fournis
    date_filter = {}
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            export_data['export_info']['period'] = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            date_filter = {'created_at__date__range': [start_date, end_date]}
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if export_type in ['all', 'products']:
        products = Product.objects.select_related('category', 'unit').filter(**date_filter)
        export_data['products'] = ProductSerializer(products, many=True).data
    
    if export_type in ['all', 'customers']:
        customers = Customer.objects.filter(**date_filter)
        export_data['customers'] = CustomerSerializer(customers, many=True).data
    
    if export_type in ['all', 'sales']:
        sale_date_filter = {}
        if start_date and end_date:
            sale_date_filter = {'sale_date__range': [start_date, end_date]}
        
        sales = Sale.objects.select_related(
            'customer', 'payment_method', 'status'
        ).prefetch_related('items').filter(**sale_date_filter)
        export_data['sales'] = SaleSerializer(sales, many=True).data
    
    if export_type in ['all', 'expenses']:
        expense_date_filter = {}
        if start_date and end_date:
            expense_date_filter = {'expense_date__range': [start_date, end_date]}
        
        expenses = Expense.objects.select_related(
            'category', 'status', 'payment_method', 'supplier'
        ).filter(**expense_date_filter)
        export_data['expenses'] = ExpenseSerializer(expenses, many=True).data
    
    return Response(export_data)


# ================================
# VUES POUR LES TABLEAUX DE BORD SPÉCIALISÉS
# ================================

@api_view(['GET'])
@permission_classes([AllowAny])
def financial_dashboard(request):
    """Tableau de bord financier complet"""
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    
    # Revenus du mois courant
    current_month_sales = Sale.objects.filter(sale_date__gte=current_month_start)
    current_month_revenue = current_month_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Revenus du mois précédent
    last_month_sales = Sale.objects.filter(
        sale_date__gte=last_month_start,
        sale_date__lte=last_month_end
    )
    last_month_revenue = last_month_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Dépenses du mois courant
    current_month_expenses = Expense.objects.filter(expense_date__gte=current_month_start)
    current_month_expense_total = current_month_expenses.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Dépenses du mois précédent
    last_month_expenses = Expense.objects.filter(
        expense_date__gte=last_month_start,
        expense_date__lte=last_month_end
    )
    last_month_expense_total = last_month_expenses.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculs de croissance
    revenue_growth = 0
    if last_month_revenue > 0:
        revenue_growth = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    
    expense_growth = 0
    if last_month_expense_total > 0:
        expense_growth = ((current_month_expense_total - last_month_expense_total) / last_month_expense_total) * 100
    
    dashboard_data = {
        'current_month': {
            'revenue': current_month_revenue,
            'expenses': current_month_expense_total,
            'profit': current_month_revenue - current_month_expense_total,
            'sales_count': current_month_sales.count(),
            'expenses_count': current_month_expenses.count()
        },
        'last_month': {
            'revenue': last_month_revenue,
            'expenses': last_month_expense_total,
            'profit': last_month_revenue - last_month_expense_total,
            'sales_count': last_month_sales.count(),
            'expenses_count': last_month_expenses.count()
        },
        'growth': {
            'revenue_growth': round(revenue_growth, 2),
            'expense_growth': round(expense_growth, 2),
            'profit_margin_current': round((current_month_revenue - current_month_expense_total) / current_month_revenue * 100, 2) if current_month_revenue > 0 else 0,
            'profit_margin_last': round((last_month_revenue - last_month_expense_total) / last_month_revenue * 100, 2) if last_month_revenue > 0 else 0
        },
        'cash_flow': {
            'receivables': Sale.objects.filter(payment_status__code='pending').aggregate(total=Sum('total_amount'))['total'] or 0,
            'payables': Expense.objects.filter(status='pending').aggregate(total=Sum('total_amount'))['total'] or 0,
            'overdue_payments': Expense.objects.filter(
                due_date__lt=today,
                status__in=['pending', 'approved']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
        },
        'top_revenue_sources': self._get_top_revenue_products(current_month_start),
        'expense_breakdown': self._get_expense_breakdown(current_month_start)
    }
    
    return Response(dashboard_data)

def _get_top_revenue_products(self, start_date):
    """Obtient les produits générant le plus de revenus"""
    return SaleItem.objects.filter(
        sale__sale_date__gte=start_date
    ).values(
        'product__name', 'product__id'
    ).annotate(
        total_revenue=Sum('total_price'),
        quantity_sold=Sum('quantity')
    ).order_by('-total_revenue')[:5]

def _get_expense_breakdown(self, start_date):
    """Obtient la répartition des dépenses par catégorie"""
    return Expense.objects.filter(
        expense_date__gte=start_date
    ).values(
        'category__name', 'category__id'
    ).annotate(
        total_amount=Sum('total_amount'),
        count=Count('id')
    ).order_by('-total_amount')


@api_view(['GET'])
@permission_classes([AllowAny])
def inventory_dashboard(request):
    """Tableau de bord inventaire détaillé"""
    products = Product.objects.select_related('category', 'unit').filter(is_active=True)
    
    # Calculs généraux
    total_products = products.count()
    low_stock_products = products.filter(current_stock__lte=F('alert_threshold'))
    out_of_stock_products = products.filter(current_stock=0)
    
    # Valeur de l'inventaire
    inventory_value = sum(
        (product.current_stock * product.purchase_price) 
        for product in products 
        if product.current_stock and product.purchase_price
    )
    
    # Valeur potentielle (prix de vente)
    potential_value = sum(
        (product.current_stock * product.selling_price) 
        for product in products 
        if product.current_stock and product.selling_price
    )
    
    # Rotation des stocks (approximation basée sur les ventes des 30 derniers jours)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    top_moving_products = SaleItem.objects.filter(
        sale__sale_date__gte=thirty_days_ago
    ).values(
        'product__name', 'product__id', 'product__current_stock'
    ).annotate(
        total_sold=Sum('quantity'),
        turnover_rate=Case(
            When(product__current_stock__gt=0, 
                 then=Sum('quantity') / F('product__current_stock')),
            default=0,
            output_field=models.FloatField()
        )
    ).order_by('-total_sold')[:10]
    
    slow_moving_products = products.annotate(
        recent_sales=Coalesce(
            Subquery(
                SaleItem.objects.filter(product=OuterRef('pk')).aggregate(
                    total=Sum('quantity')
                )['total']
            ), 0
        )
    ).filter(recent_sales=0, current_stock__gt=0)[:10]
    
    dashboard_data = {
        'overview': {
            'total_products': total_products,
            'active_products': total_products,
            'low_stock_alerts': low_stock_products.count(),
            'out_of_stock': out_of_stock_products.count(),
            'categories_count': ProductCategory.objects.filter(is_active=True).count()
        },
        'financial': {
            'inventory_value': inventory_value,
            'potential_value': potential_value,
            'potential_profit': potential_value - inventory_value,
            'average_product_value': inventory_value / total_products if total_products > 0 else 0
        },
        'stock_movement': {
            'top_moving_products': list(top_moving_products),
            'slow_moving_products': ProductListSerializer(slow_moving_products, many=True).data,
            'reorder_suggestions': self._get_reorder_suggestions(products)
        },
        'alerts': {
            'low_stock': ProductListSerializer(low_stock_products, many=True).data,
            'out_of_stock': ProductListSerializer(out_of_stock_products, many=True).data,
            'overstock': self._get_overstock_products(products)
        }
    }
    
    return Response(dashboard_data)

def _get_reorder_suggestions(self, products):
    """Suggestions de réapprovisionnement"""
    suggestions = []
    for product in products.filter(current_stock__lte=F('alert_threshold')):
        # Calcul basé sur les ventes moyennes des 30 derniers jours
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        avg_daily_sales = SaleItem.objects.filter(
            product=product,
            sale__sale_date__gte=thirty_days_ago
        ).aggregate(avg=Avg('quantity'))['avg'] or 0
        
        # Suggestion : stock pour 30 jours + marge de sécurité
        suggested_quantity = max((avg_daily_sales * 45) - product.current_stock, product.alert_threshold)
        
        suggestions.append({
            'product': ProductListSerializer(product).data,
            'current_stock': product.current_stock,
            'suggested_quantity': round(suggested_quantity, 2),
            'estimated_cost': suggested_quantity * product.purchase_price if product.purchase_price else 0,
            'avg_daily_consumption': round(avg_daily_sales, 2)
        })
    
    return suggestions[:10]  # Limiter à 10 suggestions

def _get_overstock_products(self, products):
    """Produits en surstock"""
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    overstock_products = []
    for product in products:
        if product.current_stock > product.alert_threshold * 3:  # 3 fois le seuil
            recent_sales = SaleItem.objects.filter(
                product=product,
                sale__sale_date__gte=thirty_days_ago
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            if recent_sales == 0 or product.current_stock > recent_sales * 2:
                overstock_products.append({
                    'product': ProductListSerializer(product).data,
                    'current_stock': product.current_stock,
                    'recent_sales': recent_sales,
                    'excess_stock': product.current_stock - product.alert_threshold,
                    'tied_capital': (product.current_stock - product.alert_threshold) * product.purchase_price if product.purchase_price else 0
                })
    
    return sorted(overstock_products, key=lambda x: x['tied_capital'], reverse=True)[:10]


@api_view(['GET'])
@permission_classes([AllowAny])
def customer_analytics(request):
    """Analyses détaillées des clients"""
    customers = Customer.objects.filter(is_active=True)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    ninety_days_ago = timezone.now().date() - timedelta(days=90)
    
    # Segmentation des clients
    vip_customers = customers.annotate(
        total_purchases=Sum('sale__total_amount'),
        sales_count=Count('sale')
    ).filter(total_purchases__gte=100000).order_by('-total_purchases')  # VIP > 100k XAF
    
    regular_customers = customers.annotate(
        total_purchases=Sum('sale__total_amount'),
        sales_count=Count('sale')
    ).filter(
        total_purchases__lt=100000,
        total_purchases__gte=25000
    ).order_by('-total_purchases')  # Regular 25k-100k XAF
    
    occasional_customers = customers.annotate(
        total_purchases=Sum('sale__total_amount'),
        sales_count=Count('sale')
    ).filter(total_purchases__lt=25000).order_by('-total_purchases')  # Occasional < 25k XAF
    
    # Clients actifs/inactifs
    active_customers = customers.filter(sale__sale_date__gte=thirty_days_ago).distinct()
    inactive_customers = customers.exclude(sale__sale_date__gte=ninety_days_ago).distinct()
    
    # Analyse de la fidélité
    loyal_customers = customers.annotate(
        sales_count=Count('sale'),
        last_purchase=Max('sale__sale_date')
    ).filter(
        sales_count__gte=5,
        last_purchase__gte=thirty_days_ago
    )
    
    # Nouveaux clients
    new_customers = customers.filter(created_at__gte=thirty_days_ago)
    
    analytics_data = {
        'overview': {
            'total_customers': customers.count(),
            'active_customers': active_customers.count(),
            'inactive_customers': inactive_customers.count(),
            'new_customers': new_customers.count(),
            'customer_retention_rate': self._calculate_retention_rate(customers, thirty_days_ago)
        },
        'segmentation': {
            'vip_customers': {
                'count': vip_customers.count(),
                'customers': CustomerSerializer(vip_customers[:10], many=True).data,
                'avg_purchase': vip_customers.aggregate(avg=Avg('total_purchases'))['avg'] or 0
            },
            'regular_customers': {
                'count': regular_customers.count(),
                'avg_purchase': regular_customers.aggregate(avg=Avg('total_purchases'))['avg'] or 0
            },
            'occasional_customers': {
                'count': occasional_customers.count(),
                'avg_purchase': occasional_customers.aggregate(avg=Avg('total_purchases'))['avg'] or 0
            }
        },
        'loyalty_analysis': {
            'loyal_customers': loyal_customers.count(),
            'average_visits': customers.annotate(
                visits=Count('sale')
            ).aggregate(avg=Avg('visits'))['avg'] or 0,
            'top_loyal_customers': CustomerSerializer(
                loyal_customers.order_by('-sales_count')[:5], 
                many=True
            ).data
        },
        'geographic_distribution': self._get_customer_geographic_data(customers),
        'purchase_patterns': self._analyze_purchase_patterns(thirty_days_ago)
    }
    
    return Response(analytics_data)

def _calculate_retention_rate(self, customers, date_threshold):
    """Calcule le taux de rétention client"""
    total_customers = customers.count()
    if total_customers == 0:
        return 0
    
    returning_customers = customers.filter(
        sale__sale_date__gte=date_threshold
    ).distinct().count()
    
    return round((returning_customers / total_customers) * 100, 2)

def _get_customer_geographic_data(self, customers):
    """Analyse géographique des clients (si adresse disponible)"""
    # Groupement basique par ville/région dans l'adresse
    geographic_data = customers.exclude(
        Q(address__isnull=True) | Q(address='')
    ).values('address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return list(geographic_data)

def _analyze_purchase_patterns(self, start_date):
    """Analyse des modèles d'achat"""
    sales = Sale.objects.filter(sale_date__gte=start_date)
    
    # Analyse par jour de la semaine
    sales_by_weekday = sales.extra(
        select={'weekday': "strftime('%%w', sale_date)"}
    ).values('weekday').annotate(
        count=Count('id'),
        avg_amount=Avg('total_amount')
    ).order_by('weekday')
    
    # Analyse par heure (si timestamp disponible)
    sales_by_hour = sales.extra(
        select={'hour': "strftime('%%H', created_at)"}
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Méthodes de paiement préférées
    payment_preferences = sales.values(
        'payment_method__name'
    ).annotate(
        count=Count('id'),
        total_amount=Sum('total_amount')
    ).order_by('-count')
    
    return {
        'sales_by_weekday': list(sales_by_weekday),
        'sales_by_hour': list(sales_by_hour),
        'payment_preferences': list(payment_preferences),
        'average_transaction_value': sales.aggregate(avg=Avg('total_amount'))['avg'] or 0
    }


# ================================
# VUES POUR LA GESTION DES NOTIFICATIONS
# ================================

@api_view(['GET'])
@permission_classes([AllowAny])
def system_notifications(request):
    """Notifications système pour l'utilisateur"""
    today = timezone.now().date()
    notifications = []
    
    # Alertes de stock
    low_stock_count = Product.objects.filter(
        current_stock__lte=F('alert_threshold'),
        is_active=True
    ).count()
    
    if low_stock_count > 0:
        notifications.append({
            'type': 'stock_alert',
            'level': 'warning',
            'title': f'Alerte de stock',
            'message': f'{low_stock_count} produit(s) en rupture de stock',
            'action_url': '/api/products/low-stock/',
            'created_at': timezone.now().isoformat()
        })
    
    # Dépenses en retard
    overdue_expenses = Expense.objects.filter(
        due_date__lt=today,
        status__in=['pending', 'approved']
    ).count()
    
    if overdue_expenses > 0:
        notifications.append({
            'type': 'payment_overdue',
            'level': 'error',
            'title': 'Paiements en retard',
            'message': f'{overdue_expenses} dépense(s) en retard de paiement',
            'action_url': '/api/expenses/overdue/',
            'created_at': timezone.now().isoformat()
        })
    
    # Dépenses récurrentes dues bientôt
    upcoming_recurring = RecurringExpense.objects.filter(
        next_due_date__lte=today + timedelta(days=7),
        is_active=True
    ).count()
    
    if upcoming_recurring > 0:
        notifications.append({
            'type': 'recurring_due',
            'level': 'info',
            'title': 'Dépenses récurrentes',
            'message': f'{upcoming_recurring} dépense(s) récurrente(s) due(s) bientôt',
            'action_url': '/api/recurring-expenses/due-soon/',
            'created_at': timezone.now().isoformat()
        })
    
    # Ventes non payées
    unpaid_sales = Sale.objects.filter(
        payment_status__code='pending',
        sale_date__lt=today - timedelta(days=3)  # Plus de 3 jours
    ).count()
    
    if unpaid_sales > 0:
        notifications.append({
            'type': 'unpaid_sales',
            'level': 'warning',
            'title': 'Ventes impayées',
            'message': f'{unpaid_sales} vente(s) non payée(s) depuis plus de 3 jours',
            'action_url': '/api/sales/?payment_status=pending',
            'created_at': timezone.now().isoformat()
        })
    
    # Performance du jour
    today_sales = Sale.objects.filter(sale_date=today)
    today_revenue = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    if today_sales.count() == 0:
        notifications.append({
            'type': 'daily_performance',
            'level': 'info',
            'title': 'Performance du jour',
            'message': 'Aucune vente enregistrée aujourd\'hui',
            'action_url': '/api/sales/today-sales/',
            'created_at': timezone.now().isoformat()
        })
    
    return Response({
        'notifications': notifications,
        'unread_count': len(notifications),
        'last_updated': timezone.now().isoformat()
    })


# ================================
# VUES UTILITAIRES ET OUTILS
# ================================

@api_view(['POST'])
@permission_classes([AllowAny])
def backup_data(request):
    """Sauvegarde des données importantes"""
    backup_type = request.data.get('type', 'full')  # full, products, sales, customers
    
    backup_data = {
        'backup_info': {
            'type': backup_type,
            'created_at': timezone.now().isoformat(),
            'created_by': request.user.username,
            'version': '1.0'
        }
    }
    
    try:
        if backup_type in ['full', 'products']:
            products = Product.objects.select_related('category', 'unit').all()
            backup_data['products'] = ProductSerializer(products, many=True).data
            backup_data['product_categories'] = ProductCategorySerializer(
                ProductCategory.objects.all(), many=True
            ).data
            backup_data['product_units'] = ProductUnitSerializer(
                ProductUnit.objects.all(), many=True
            ).data
        
        if backup_type in ['full', 'customers']:
            customers = Customer.objects.all()
            backup_data['customers'] = CustomerSerializer(customers, many=True).data
        
        if backup_type in ['full', 'sales']:
            # Limiter aux 6 derniers mois pour éviter des fichiers trop volumineux
            six_months_ago = timezone.now().date() - timedelta(days=180)
            sales = Sale.objects.filter(sale_date__gte=six_months_ago).select_related(
                'customer', 'payment_method', 'status').prefetch_related('items')
            backup_data['sales'] = SaleSerializer(sales, many=True).data
        
        if backup_type == 'full':
            suppliers = Supplier.objects.all()
            backup_data['suppliers'] = SupplierSerializer(suppliers, many=True).data
            
            # Inclure les données de configuration
            backup_data['configuration'] = {
                'payment_methods': PaymentMethodSerializer(PaymentMethod.objects.all(), many=True).data,
                'sale_statuses': SaleStatusSerializer(SaleStatus.objects.all(), many=True).data,
                'expense_categories': ExpenseCategorySerializer(ExpenseCategory.objects.all(), many=True).data,
            }
        
        return Response({
            'status': 'success',
            'message': 'Backup created successfully',
            'backup_size': len(str(backup_data)),
            'data': backup_data
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Backup failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def system_health_check(request):
    """Vérification de l'état du système"""
    health_data = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    try:
        # Vérification de la base de données
        product_count = Product.objects.count()
        health_data['checks']['database'] = {
            'status': 'ok',
            'message': f'{product_count} products in database'
        }
        
        # Vérification des données critiques
        categories_count = ProductCategory.objects.count()
        if categories_count == 0:
            health_data['checks']['categories'] = {
                'status': 'warning',
                'message': 'No product categories found'
            }
        else:
            health_data['checks']['categories'] = {
                'status': 'ok',
                'message': f'{categories_count} categories configured'
            }
        
        # Vérification des alertes de stock
        critical_stock = Product.objects.filter(current_stock=0, is_active=True).count()
        if critical_stock > 10:
            health_data['checks']['stock'] = {
                'status': 'critical',
                'message': f'{critical_stock} products out of stock'
            }
        elif critical_stock > 0:
            health_data['checks']['stock'] = {
                'status': 'warning',
                'message': f'{critical_stock} products out of stock'
            }
        else:
            health_data['checks']['stock'] = {
                'status': 'ok',
                'message': 'Stock levels normal'
            }
        
        # Vérification des ventes récentes
        recent_sales = Sale.objects.filter(
            sale_date__gte=timezone.now().date() - timedelta(days=7)
        ).count()
        
        if recent_sales == 0:
            health_data['checks']['sales_activity'] = {
                'status': 'warning',
                'message': 'No sales in the last 7 days'
            }
        else:
            health_data['checks']['sales_activity'] = {
                'status': 'ok',
                'message': f'{recent_sales} sales in the last 7 days'
            }
        
        # Déterminer le statut global
        statuses = [check['status'] for check in health_data['checks'].values()]
        if 'critical' in statuses:
            health_data['status'] = 'critical'
        elif 'warning' in statuses:
            health_data['status'] = 'warning'
        else:
            health_data['status'] = 'healthy'
            
    except Exception as e:
        health_data['status'] = 'error'
        health_data['error'] = str(e)
    
    return Response(health_data)


@api_view(['POST'])
@permission_classes([AllowAny])
def cleanup_old_data(request):
    """Nettoyage des anciennes données"""
    days_to_keep = int(request.data.get('days_to_keep', 365))
    dry_run = request.data.get('dry_run', True)  # Mode test par défaut
    
    cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
    
    cleanup_stats = {
        'cutoff_date': cutoff_date.isoformat(),
        'dry_run': dry_run,
        'items_to_delete': {},
        'items_deleted': {} if not dry_run else None
    }
    
    # Anciennes entrées de stock validées
    old_entries = Entry.objects.filter(
        entry_date__lt=cutoff_date,
        status='validated'
    )
    cleanup_stats['items_to_delete']['entries'] = old_entries.count()
    
    # Anciennes dépenses payées
    old_expenses = Expense.objects.filter(
        expense_date__lt=cutoff_date,
        status='paid'
    )
    cleanup_stats['items_to_delete']['expenses'] = old_expenses.count()
    
    # Anciennes ventes terminées
    old_sales = Sale.objects.filter(
        sale_date__lt=cutoff_date,
        status__code='completed'
    )
    cleanup_stats['items_to_delete']['sales'] = old_sales.count()
    
    if not dry_run:
        # Effectuer le nettoyage réel (avec prudence)
        try:
            cleanup_stats['items_deleted']['entries'] = old_entries.delete()[0]
            cleanup_stats['items_deleted']['expenses'] = old_expenses.delete()[0]
            cleanup_stats['items_deleted']['sales'] = old_sales.delete()[0]
            
            cleanup_stats['status'] = 'success'
            cleanup_stats['message'] = 'Cleanup completed successfully'
            
        except Exception as e:
            cleanup_stats['status'] = 'error'
            cleanup_stats['message'] = f'Cleanup failed: {str(e)}'
            return Response(cleanup_stats, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        cleanup_stats['message'] = 'Dry run completed - no data was deleted'
    
    return Response(cleanup_stats)


class ProductUnitViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des unités de produits"""
    queryset = ProductUnit.objects.all()
    serializer_class = ProductUnitSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviation']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des rôles utilisateur"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class UserStatusViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des statuts utilisateur"""
    queryset = UserStatus.objects.all()
    serializer_class = UserStatusSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class EntryTypeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des types d'entrées"""
    queryset = EntryType.objects.all()
    serializer_class = EntryTypeSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des catégories de dépenses"""
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class ExpenseStatusViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des statuts de dépenses"""
    queryset = ExpenseStatus.objects.all()
    serializer_class = ExpenseStatusSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des méthodes de paiement"""
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class SaleStatusViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des statuts de ventes"""
    queryset = SaleStatus.objects.all()
    serializer_class = SaleStatusSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class PaymentStatusViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des statuts de paiement"""
    queryset = PaymentStatus.objects.all()
    serializer_class = PaymentStatusSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ================================
# VIEWSETS POUR LES MODÈLES PRINCIPAUX
# ================================

class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des fournisseurs"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'email', 'phone', 'contact_person']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SupplierCreateSerializer
        return SupplierSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """Récupère toutes les entrées d'un fournisseur"""
        supplier = self.get_object()
        entries = Entry.objects.filter(supplier=supplier).order_by('-entry_date')
        serializer = EntrySerializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def expenses(self, request, pk=None):
        """Récupère toutes les dépenses d'un fournisseur"""
        supplier = self.get_object()
        expenses = Expense.objects.filter(supplier=supplier).order_by('-expense_date')
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Récupère les fournisseurs actifs"""
        active_suppliers = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_suppliers, many=True)
        return Response(serializer.data)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des clients"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['first_name', 'last_name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CustomerCreateSerializer
        return CustomerSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['get'])
    def sales(self, request, pk=None):
        """Récupère toutes les ventes d'un client"""
        customer = self.get_object()
        sales = Sale.objects.filter(customer=customer).order_by('-sale_date')
        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sales_summary(self, request, pk=None):
        """Résumé des ventes d'un client"""
        customer = self.get_object()
        sales = Sale.objects.filter(customer=customer)
        
        summary = {
            'total_sales': sales.count(),
            'total_amount': sales.aggregate(total=Sum('total_amount'))['total'] or 0,
            'average_sale': sales.aggregate(avg=Avg('total_amount'))['avg'] or 0,
            'last_purchase': sales.order_by('-sale_date').first()
        }
        
        return Response(summary)

    @action(detail=False, methods=['get'])
    def top_customers(self, request):
        """Récupère les meilleurs clients"""
        limit = int(request.query_params.get('limit', 10))
        top_customers = self.queryset.annotate(
            total_purchases=Sum('sale__total_amount'),
            sales_count=Count('sale')
        ).filter(total_purchases__gt=0).order_by('-total_purchases')[:limit]
        
        serializer = self.get_serializer(top_customers, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des produits"""
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'unit', 'is_active']
    search_fields = ['name', 'description', 'barcode']
    ordering_fields = ['name', 'current_stock', 'selling_price', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Product.objects.select_related('category', 'unit', 'created_by').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Récupère les produits en rupture de stock"""
        low_stock_products = self.get_queryset().filter(
            current_stock__lte=F('alert_threshold'),
            is_active=True
        )
        serializer = ProductListSerializer(low_stock_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stock_alerts(self, request):
        """Alertes de stock détaillées"""
        low_stock_products = self.get_queryset().filter(
            current_stock__lte=F('alert_threshold'),
            is_active=True
        ).annotate(
            difference=F('alert_threshold') - F('current_stock')
        )
        
        alerts = []
        for product in low_stock_products:
            alerts.append({
                'product': ProductListSerializer(product).data,
                'current_stock': product.current_stock,
                'alert_threshold': product.alert_threshold,
                'difference': product.difference
            })
        
        return Response(alerts)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def adjust_stock(self, request, pk=None):
        """Ajuster le stock d'un produit"""
        product = self.get_object()
        adjustment = request.data.get('adjustment', 0)
        reason = request.data.get('reason', 'Manual adjustment')
        
        try:
            adjustment = float(adjustment)
            if product.current_stock + adjustment < 0:
                return Response(
                    {'error': 'Stock cannot be negative'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            product.current_stock += adjustment
            product.save()
            
            return Response({
                'message': f'Stock adjusted by {adjustment}',
                'new_stock': product.current_stock,
                'reason': reason
            })
        except ValueError:
            return Response(
                {'error': 'Invalid adjustment value'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Produits par catégorie"""
        category_id = request.query_params.get('category_id')
        if category_id:
            products = self.get_queryset().filter(category_id=category_id)
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response(
            {'error': 'category_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def inventory_value(self, request):
        """Calcule la valeur totale de l'inventaire"""
        products = self.get_queryset().filter(is_active=True)
        
        total_value = sum(
            (product.current_stock * product.purchase_price) 
            for product in products 
            if product.current_stock and product.purchase_price
        )
        
        return Response({
            'total_products': products.count(),
            'total_inventory_value': total_value,
            'currency': 'XAF'  # Adapté pour le Gabon
        })


class TimeSlotViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des créneaux horaires"""
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['order', 'start_time', 'created_at']
    ordering = ['order', 'start_time']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class UserTimeSlotViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des associations utilisateurs-créneaux horaires"""
    queryset = UserTimeSlot.objects.select_related('user', 'time_slot', 'created_by', 'updated_by')
    serializer_class = UserTimeSlotSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'time_slot', 'is_active']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserTimeSlotCreateUpdateSerializer
        elif self.action == 'list':
            return UserTimeSlotListSerializer
        return UserTimeSlotSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Récupère les créneaux horaires d'un utilisateur spécifique"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {"error": "Le paramètre 'user_id' est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_time_slots = self.get_queryset().filter(
            user_id=user_id, 
            is_active=True
        ).order_by('time_slot__order', 'time_slot__start_time')
        
        serializer = self.get_serializer(user_time_slots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_time_slot(self, request):
        """Récupère les utilisateurs d'un créneau horaire spécifique"""
        time_slot_id = request.query_params.get('time_slot_id')
        if not time_slot_id:
            return Response(
                {"error": "Le paramètre 'time_slot_id' est requis"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_time_slots = self.get_queryset().filter(
            time_slot_id=time_slot_id, 
            is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        
        # Utilisation d'un sérialiseur personnalisé pour inclure les détails de l'utilisateur
        users = [uts.user for uts in user_time_slots]
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)


# ================================
# VIEWSETS POUR LES ENTRÉES DE STOCK
# ================================

class EntryViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des entrées de stock"""
    queryset = Entry.objects.select_related('entry_type', 'supplier', 'created_by').prefetch_related('items__product')
    serializer_class = EntrySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['entry_type', 'supplier', 'status']
    search_fields = ['reference', 'notes']
    ordering_fields = ['entry_date', 'created_at', 'total_amount']
    ordering = ['-entry_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EntryCreateUpdateSerializer
        return EntrySerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Entrées par période"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entries = self.queryset.filter(entry_date__range=[start_date, end_date])
        serializer = self.get_serializer(entries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des entrées"""
        entries = self.queryset
        
        summary = {
            'total_entries': entries.count(),
            'total_amount': entries.aggregate(total=Sum('total_amount'))['total'] or 0,
            'entries_by_status': {},
            'entries_by_type': {},
            'recent_entries': entries.order_by('-created_at')[:5]
        }
        
        # Entrées par statut
        for status_choice in Entry.STATUS_CHOICES:
            status_key, label = status_choice
            count = entries.filter(status=status_key).count()
            summary['entries_by_status'][status_key] = {
                'label': label,
                'count': count
            }
        
        return Response(summary)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def validate_entry(self, request, pk=None):
        """Valider une entrée"""
        entry = self.get_object()
        
        if entry.status == 'validated':
            return Response(
                {'error': 'Entry is already validated'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entry.status = 'validated'
        entry.updated_by = request.user
        entry.save()
        
        # Mettre à jour les stocks des produits
        for item in entry.items.all():
            product = item.product
            product.current_stock += item.quantity
            product.save()
        
        return Response({
            'message': 'Entry validated successfully',
            'entry_id': entry.id,
            'status': entry.status
        })


class EntryItemViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des articles d'entrées"""
    queryset = EntryItem.objects.select_related('entry', 'product', 'created_by')
    serializer_class = EntryItemSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['entry', 'product']
    ordering_fields = ['created_at', 'quantity', 'unit_price']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


# ================================
# VIEWSETS POUR LES DÉPENSES
# ================================

class RecurringExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des dépenses récurrentes"""
    queryset = RecurringExpense.objects.select_related('category', 'created_by')
    serializer_class = RecurringExpenseSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'frequency', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'next_due_date', 'amount', 'created_at']
    ordering = ['next_due_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Dépenses récurrentes dues bientôt"""
        days = int(request.query_params.get('days', 7))
        due_date = timezone.now().date() + timedelta(days=days)
        
        due_expenses = self.queryset.filter(
            next_due_date__lte=due_date,
            is_active=True
        )
        serializer = self.get_serializer(due_expenses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def generate_expense(self, request, pk=None):
        """Générer une dépense à partir d'une dépense récurrente"""
        recurring_expense = self.get_object()
        
        # Créer une nouvelle dépense
        expense = Expense.objects.create(
            description=f"{recurring_expense.name} ({recurring_expense.frequency})",
            category=recurring_expense.category,
            amount=recurring_expense.amount,
            expense_date=timezone.now().date(),
            recurring_expense=recurring_expense,
            status='pending',
            created_by=request.user,
            updated_by=request.user
        )
        
        # Mettre à jour la prochaine date d'échéance
        if recurring_expense.frequency == 'monthly':
            recurring_expense.next_due_date += timedelta(days=30)
        elif recurring_expense.frequency == 'weekly':
            recurring_expense.next_due_date += timedelta(days=7)
        elif recurring_expense.frequency == 'yearly':
            recurring_expense.next_due_date += timedelta(days=365)
        
        recurring_expense.save()
        
        serializer = ExpenseSerializer(expense)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des dépenses"""
    queryset = Expense.objects.select_related('category', 'status', 'payment_method', 'supplier', 'created_by')
    serializer_class = ExpenseSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'payment_method', 'supplier']
    search_fields = ['reference', 'description']
    ordering_fields = ['expense_date', 'due_date', 'total_amount', 'created_at']
    ordering = ['-expense_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExpenseListSerializer
        return ExpenseSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def validate_expense(self, request, pk=None):
        """Valider une dépense"""
        expense = self.get_object()
        
        if expense.status == 'validated':
            return Response(
                {'error': 'Expense is already validated'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expense.status = 'validated'
        expense.updated_by = request.user
        expense.save()
        
        return Response({
            'message': 'Expense validated successfully',
            'expense_id': expense.id,
            'status': expense.status
        })