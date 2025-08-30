from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    # ViewSets principaux
    ProductViewSet, SupplierViewSet, CustomerViewSet, TimeSlotViewSet, UserTimeSlotViewSet,
    EntryViewSet, EntryItemViewSet, ExpenseViewSet, RecurringExpenseViewSet, SaleViewSet, SaleItemViewSet,
    
    # ViewSets de configuration
    UserRoleViewSet, UserStatusViewSet, EntryTypeViewSet, ExpenseCategoryViewSet,
    ExpenseStatusViewSet, PaymentMethodViewSet, SaleStatusViewSet, PaymentStatusViewSet,
    ProductCategoryViewSet, ProductUnitViewSet,
    
    # Vues fonctionnelles
    business_dashboard, inventory_report, sales_analytics, financial_dashboard, 
    inventory_dashboard, customer_analytics,
    
    # Vues API custom
    advanced_product_search, business_statistics, 
    generate_sales_report, low_stock_alerts, bulk_update_products,
    validate_sale_data, export_data, backup_data, system_health_check, 
    cleanup_old_data, system_notifications
)

# Configuration du router principal
router = DefaultRouter()

# ================================
# ROUTES POUR LES UTILISATEURS ET RÔLES
# ================================
router.register(r'user-roles', UserRoleViewSet, basename='userrole')
router.register(r'user-statuses', UserStatusViewSet, basename='userstatus')
# router.register(r'users', AppUserViewSet, basename='user')

# ================================
# ROUTES POUR LES FOURNISSEURS ET CLIENTS
# ================================
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'customers', CustomerViewSet, basename='customer')

# ================================
# ROUTES POUR LES CRÉNEAUX HORAIRES
# ================================
router.register(r'time-slots', TimeSlotViewSet, basename='timeslot')
router.register(r'user-time-slots', UserTimeSlotViewSet, basename='usertimeslot')

# ================================
# ROUTES POUR LES ENTREES DE STOCK
# ================================
router.register(r'entry-types', EntryTypeViewSet, basename='entrytype')
router.register(r'entries', EntryViewSet, basename='entry')
router.register(r'entry-items', EntryItemViewSet, basename='entryitem')

# ================================
# ROUTES POUR LES DÉPENSES
# ================================
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expensecategory')
router.register(r'expense-statuses', ExpenseStatusViewSet, basename='expensestatus')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'recurring-expenses', RecurringExpenseViewSet, basename='recurringexpense')

# ================================
# ROUTES POUR LES VENTES
# ================================
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'sale-items', SaleItemViewSet, basename='saleitem')
router.register(r'payment-methods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'payment-statuses', PaymentStatusViewSet, basename='paymentstatus')
router.register(r'sale-statuses', SaleStatusViewSet, basename='salestatus')

# ================================
# ROUTES POUR LES PRODUITS
# ================================
router.register(r'product-categories', ProductCategoryViewSet, basename='productcategory')
router.register(r'product-units', ProductUnitViewSet, basename='productunit')
router.register(r'products', ProductViewSet, basename='product')

# ================================
# PATTERNS D'URL COMPLETS
# ================================
urlpatterns = [
    # Routes du router (API REST)
    path('api/', include(router.urls)),
    
    # ================================
    # VUES FONCTIONNELLES (DASHBOARD)
    # ================================
    path('business-dashboard/', business_dashboard, name='business-dashboard'),
    path('inventory-report/', inventory_report, name='inventory-report'),
    path('sales-analytics/', sales_analytics, name='sales-analytics'),
    path('financial-dashboard/', financial_dashboard, name='financial-dashboard'),
    path('inventory-dashboard/', inventory_dashboard, name='inventory-dashboard'),
    path('customer-analytics/', customer_analytics, name='customer-analytics'),
    
    # ================================
    # API ENDPOINTS CUSTOM
    # ================================
    
    # Recherche et suggestions
    path('api/advanced-search/', advanced_product_search, name='advanced-product-search'),
    
    # Statistiques et rapports
    path('api/business-stats/', business_statistics, name='business-stats'),
    path('api/sales-report/', generate_sales_report, name='generate-sales-report'),
    path('api/low-stock-alerts/', low_stock_alerts, name='low-stock-alerts'),
    
    # Opérations en lot
    path('api/bulk-update/', bulk_update_products, name='bulk-update-products'),
    
    # Export et sauvegarde
    path('api/export/', export_data, name='export-data'),
    path('api/backup/', backup_data, name='backup-data'),
    
    # Validation
    path('api/validate-sale/', validate_sale_data, name='validate-sale'),
    
    # Système
    path('api/system/health/', system_health_check, name='system-health-check'),
    path('api/system/cleanup/', cleanup_old_data, name='cleanup-old-data'),
    path('api/system/notifications/', system_notifications, name='system-notifications'),
]
