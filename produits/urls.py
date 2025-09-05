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
router.register(r'suppliers', SupplierViewSet, basename='supplier') # http://localhost:8000/produits/api/suppliers/
router.register(r'customers', CustomerViewSet, basename='customer') # http://localhost:8000/produits/api/customers/

# ================================
# ROUTES POUR LES CRÉNEAUX HORAIRES
# ================================
router.register(r'time-slots', TimeSlotViewSet, basename='timeslot') # http://localhost:8000/produits/api/time-slots/
router.register(r'user-time-slots', UserTimeSlotViewSet, basename='usertimeslot') # http://localhost:8000/produits/api/user-time-slots/

# ================================
# ROUTES POUR LES ENTREES DE STOCK
# ================================
router.register(r'entry-types', EntryTypeViewSet, basename='entrytype') # http://localhost:8000/produits/api/entry-types/
router.register(r'entries', EntryViewSet, basename='entry') # http://localhost:8000/produits/api/entries/
router.register(r'entry-items', EntryItemViewSet, basename='entryitem') # http://localhost:8000/produits/api/entry-items/

# ================================
# ROUTES POUR LES DÉPENSES
# ================================
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expensecategory') # http://localhost:8000/produits/api/expense-categories/
router.register(r'expense-statuses', ExpenseStatusViewSet, basename='expensestatus') # http://localhost:8000/produits/api/expense-statuses/
router.register(r'expenses', ExpenseViewSet, basename='expense') # http://localhost:8000/produits/api/expenses/
router.register(r'recurring-expenses', RecurringExpenseViewSet, basename='recurringexpense') # http://localhost:8000/produits/api/recurring-expenses/

# ================================
# ROUTES POUR LES VENTES
# ================================
router.register(r'sales', SaleViewSet, basename='sale') # http://localhost:8000/produits/api/sales/
router.register(r'sale-items', SaleItemViewSet, basename='saleitem') # http://localhost:8000/produits/api/sale-items/
router.register(r'payment-methods', PaymentMethodViewSet, basename='paymentmethod') # http://localhost:8000/produits/api/payment-methods/
router.register(r'payment-statuses', PaymentStatusViewSet, basename='paymentstatus') # http://localhost:8000/produits/api/payment-statuses/
router.register(r'sale-statuses', SaleStatusViewSet, basename='salestatus') # http://localhost:8000/produits/api/sale-statuses/

# ================================
# ROUTES POUR LES PRODUITS
# ================================
router.register(r'product-categories', ProductCategoryViewSet, basename='productcategory') # http://localhost:8000/produits/api/product-categories/
router.register(r'product-units', ProductUnitViewSet, basename='productunit') # http://localhost:8000/produits/api/product-units/
router.register(r'products', ProductViewSet, basename='product') # http://localhost:8000/produits/api/products/

# ================================
# PATTERNS D'URL COMPLETS
# ================================
urlpatterns = [
    # Routes du router (API REST)
    path('api/', include(router.urls)),
    
    # ================================
    # VUES FONCTIONNELLES (DASHBOARD)
    # ================================
    path('business-dashboard/', business_dashboard, name='business-dashboard'), # http://localhost:8000/produits/business-dashboard/
    path('inventory-report/', inventory_report, name='inventory-report'), # http://localhost:8000/produits/inventory-report/
    path('sales-analytics/', sales_analytics, name='sales-analytics'), # http://localhost:8000/produits/sales-analytics/
    path('financial-dashboard/', financial_dashboard, name='financial-dashboard'), # http://localhost:8000/produits/financial-dashboard/
    path('inventory-dashboard/', inventory_dashboard, name='inventory-dashboard'), # http://localhost:8000/produits/inventory-dashboard/
    path('customer-analytics/', customer_analytics, name='customer-analytics'), # http://localhost:8000/produits/customer-analytics/
    
    # ================================
    # API ENDPOINTS CUSTOM
    # ================================
    
    # Recherche et suggestions
    path('api/advanced-search/', advanced_product_search, name='advanced-product-search'), # http://localhost:8000/produits/api/advanced-search/
    
    # Statistiques et rapports
    path('api/business-stats/', business_statistics, name='business-stats'), # http://localhost:8000/produits/api/business-stats/
    path('api/sales-report/', generate_sales_report, name='generate-sales-report'), # http://localhost:8000/produits/api/sales-report/
    path('api/low-stock-alerts/', low_stock_alerts, name='low-stock-alerts'), # http://localhost:8000/produits/api/low-stock-alerts/
    
    # Opérations en lot
    path('api/bulk-update/', bulk_update_products, name='bulk-update-products'), # http://localhost:8000/produits/api/bulk-update/
    
    # Export et sauvegarde
    path('api/export/', export_data, name='export-data'), # http://localhost:8000/produits/api/export/
    path('api/backup/', backup_data, name='backup-data'), # http://localhost:8000/produits/api/backup/
    
    # Validation
    path('api/validate-sale/', validate_sale_data, name='validate-sale'), # http://localhost:8000/produits/api/validate-sale/
    
    # Système
    path('api/system/health/', system_health_check, name='system-health-check'), # http://localhost:8000/produits/api/system/health/
    path('api/system/cleanup/', cleanup_old_data, name='cleanup-old-data'), # http://localhost:8000/produits/api/system/cleanup/
    path('api/system/notifications/', system_notifications, name='system-notifications'), # http://localhost:8000/produits/api/system/notifications/
]
