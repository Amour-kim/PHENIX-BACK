from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
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

User = get_user_model()


# ================================
# SERIALIZER UTILISATEUR DE BASE
# ================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


# ================================
# SERIALIZERS POUR LES CATÉGORIES MODULAIRES
# ================================

class ProductCategorySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'description', 'is_active', 'product_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_product_count(self, obj):
        """Retourne le nombre de produits dans cette catégorie"""
        return obj.product_set.filter(is_active=True).count()


class ProductUnitSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductUnit
        fields = [
            'id', 'name', 'abbreviation', 'is_active', 'usage_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Retourne le nombre de produits utilisant cette unité"""
        return obj.product_set.filter(is_active=True).count()


class UserRoleSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'name', 'description', 'is_active', 'users_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_users_count(self, obj):
        """Retourne le nombre d'utilisateurs avec ce rôle"""
        return obj.appuser_set.count()


class UserStatusSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserStatus
        fields = [
            'id', 'name', 'description', 'is_default', 'is_active', 'users_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_users_count(self, obj):
        """Retourne le nombre d'utilisateurs avec ce statut"""
        return obj.appuser_set.count()


class EntryTypeSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EntryType
        fields = [
            'id', 'name', 'code', 'description', 'is_active', 'usage_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Retourne le nombre d'entrées de ce type"""
        return obj.entry_set.count()


class ExpenseCategorySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'name', 'code', 'description', 'is_active', 'usage_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Retourne le nombre de dépenses dans cette catégorie"""
        return obj.expense_set.count() + obj.recurringexpense_set.count()


class ExpenseStatusSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseStatus
        fields = [
            'id', 'name', 'code', 'description', 'is_active', 'usage_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Retourne le nombre de dépenses avec ce statut"""
        return obj.expense_set.count()


class PaymentMethodSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'code', 'description', 'is_active', 'usage_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Retourne le nombre d'utilisations de cette méthode"""
        return obj.expense_set.count() + obj.sale_set.count()


class SaleStatusSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SaleStatus
        fields = [
            'id', 'name', 'code', 'description', 'is_active', 'usage_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Retourne le nombre de ventes avec ce statut"""
        return obj.sale_set.count()


class PaymentStatusSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentStatus
        fields = [
            'id', 'name', 'code', 'description', 'is_active', 'usage_count',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Retourne le nombre de ventes avec ce statut de paiement"""
        return obj.sale_set.count()


# ================================
# SERIALIZERS POUR LES MODÈLES PRINCIPAUX
# ================================

class SupplierSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    entries_count = serializers.SerializerMethodField()
    expenses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'email', 'phone', 'address', 'contact_person', 'notes', 'is_active',
            'entries_count', 'expenses_count', 'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_entries_count(self, obj):
        """Retourne le nombre d'entrées de stock de ce fournisseur"""
        return obj.entry_set.count()
    
    def get_expenses_count(self, obj):
        """Retourne le nombre de dépenses liées à ce fournisseur"""
        return obj.expense_set.count()


class CustomerSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    sales_count = serializers.SerializerMethodField()
    total_purchases = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone', 'address', 'notes', 'is_active',
            'sales_count', 'total_purchases', 'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_sales_count(self, obj):
        """Retourne le nombre de ventes de ce client"""
        return obj.sale_set.count()
    
    def get_total_purchases(self, obj):
        """Retourne le montant total des achats du client"""
        from django.db.models import Sum
        total = obj.sale_set.aggregate(total=Sum('total_amount'))['total']
        return total or 0


class ProductSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    unit = ProductUnitSerializer(read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'category', 'unit', 'purchase_price', 'selling_price',
            'current_stock', 'alert_threshold', 'barcode', 'image_url', 'is_active', 'is_low_stock',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de produits"""
    category = ProductCategorySerializer(read_only=True)
    unit = ProductUnitSerializer(read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'unit', 'selling_price', 'current_stock', 'purchase_price',
            'alert_threshold', 'is_active', 'is_low_stock'
        ]


class TimeSlotSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = [
            'id', 'name', 'start_time', 'end_time', 'is_active', 'description', 'order',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserTimeSlotSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    time_slot_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = UserTimeSlot
        fields = [
            'id', 'user', 'user_id', 'time_slot', 'time_slot_id', 'is_active', 'description',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserTimeSlotCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTimeSlot
        fields = ['user', 'time_slot', 'is_active', 'description']


class UserTimeSlotListSerializer(serializers.ModelSerializer):
    time_slot = TimeSlotSerializer(read_only=True)

    class Meta:
        model = UserTimeSlot
        fields = ['id', 'time_slot', 'is_active', 'description']


class TimeSlotWithUsersSerializer(TimeSlotSerializer):
    users = serializers.SerializerMethodField()

    class Meta(TimeSlotSerializer.Meta):
        fields = TimeSlotSerializer.Meta.fields + ['users']
    
    def get_users(self, obj):
        # Récupère les utilisateurs associés à ce créneau via la relation UserTimeSlot
        user_time_slots = obj.usertimeslot_set.filter(is_active=True).select_related('user')
        users = [uts.user for uts in user_time_slots]
        # Utilisation d'un UserSerializer avec seulement les champs nécessaires
        return UserSerializer(users, many=True, context=self.context).data


# ================================
# SERIALIZERS POUR LES ENTRÉES DE STOCK
# ================================

class EntryItemSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    product = ProductListSerializer(read_only=True)
    # entry = EntrySerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    entry_id = serializers.PrimaryKeyRelatedField(
        queryset=Entry.objects.all(),
        source='entry',
        write_only=True,
        required=False  # Rendre optionnel pour la mise à jour
    )
    
    class Meta:
        model = EntryItem
        fields = [
            'id', 'entry', 'entry_id', 'product', 'product_id', 'quantity', 'total_price',
            'expiry_date', 'batch_number', 'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_price', 'entry']


class EntrySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    entry_type = EntryTypeSerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True)
    items = EntryItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Entry
        fields = [
            'id', 'reference', 'entry_type', 'supplier', 'entry_date', 'notes',
            'total_amount', 'tax_amount', 'status', 'items',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]


class EntryCreateUpdateSerializer(serializers.ModelSerializer):
    # items = EntryItemSerializer(many=True)
    class Meta:
        model = Entry
        fields = [
            'id', 'entry_type', 'supplier', 'entry_date', 'notes',
            'total_amount', 'tax_amount', 'status', 'items',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
 

# ================================
# SERIALIZERS POUR LES DÉPENSES
# ================================

class RecurringExpenseSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    category = ExpenseCategorySerializer(read_only=True)
    generated_expenses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RecurringExpense
        fields = [
            'id', 'name', 'description', 'category', 'amount', 'frequency', 'next_due_date', 'is_active',
            'generated_expenses_count', 'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
    
    def get_generated_expenses_count(self, obj):
        """Retourne le nombre de dépenses générées"""
        return obj.expense_set.count()


class ExpenseSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    category = ExpenseCategorySerializer(read_only=True)
    status = ExpenseStatusSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True)
    recurring_expense = RecurringExpenseSerializer(read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'reference', 'description', 'category', 'amount', 'tax_amount', 'total_amount',
            'expense_date', 'due_date', 'payment_date', 'payment_method', 'status', 'receipt_url',
            'notes', 'supplier', 'recurring_expense',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount']


class ExpenseListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de dépenses"""
    category = ExpenseCategorySerializer(read_only=True)
    status = ExpenseStatusSerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'reference', 'description', 'category', 'total_amount', 'expense_date',
            'status', 'supplier'
        ]


# ================================
# SERIALIZERS POUR LES VENTES
# ================================


class SaleItemSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    sale_id = serializers.PrimaryKeyRelatedField(
        queryset=Sale.objects.all(),
        source='sale',
        write_only=True
    )
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'sale_id', 'product', 'product_id', 'quantity', 
            'discount', 'tax_rate', 'total_price',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_price']


class SaleSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    payment_status = PaymentStatusSerializer(read_only=True)
    status = SaleStatusSerializer(read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'reference', 'customer', 'sale_date', 'subtotal', 'discount_amount',
            'tax_amount', 'total_amount', 'payment_method', 'payment_status', 'status',
            'notes', 'table_number', 'is_take_away', 'customer_name', 'customer_phone',
            'items', 'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount']


class SaleListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes de ventes"""
    customer = CustomerSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    status = SaleStatusSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'reference', 'customer', 'customer_name', 'sale_date', 'total_amount',
            'payment_method', 'status', 'is_take_away', 'items_count'
        ]
    
    def get_items_count(self, obj):
        """Retourne le nombre d'articles dans la vente"""
        return obj.items.count()


class SaleCreateUpdateSerializer(serializers.ModelSerializer):
    # items = SaleItemSerializer(many=True)
    class Meta:
        model = Sale
        fields = [
            'customer', 'sale_date', 'subtotal', 'discount_amount',
            'tax_amount', 'payment_method', 'payment_status', 'status',
            'notes', 'table_number', 'is_take_away', 'customer_name', 'customer_phone', 'created_by',
        ]



# ================================
# SERIALIZERS STATISTIQUES
# ================================

class ProductStockAlertSerializer(serializers.Serializer):
    """Serializer pour les alertes de stock"""
    product = ProductListSerializer()
    current_stock = serializers.DecimalField(max_digits=10, decimal_places=2)
    alert_threshold = serializers.DecimalField(max_digits=10, decimal_places=2)
    difference = serializers.DecimalField(max_digits=10, decimal_places=2)


class SalesStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de ventes"""
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_sale = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_products = serializers.ListField()
    sales_by_method = serializers.DictField()
    sales_by_status = serializers.DictField()


class ExpenseStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de dépenses"""
    total_expenses = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    expenses_by_category = serializers.DictField()
    expenses_by_status = serializers.DictField()
    upcoming_payments = serializers.IntegerField()


class InventoryStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'inventaire"""
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    stock_alerts = ProductStockAlertSerializer(many=True)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer pour le tableau de bord général"""
    sales_stats = SalesStatsSerializer()
    expense_stats = ExpenseStatsSerializer()
    inventory_stats = InventoryStatsSerializer()
    recent_activities = serializers.ListField()


# ================================
# SERIALIZERS POUR LA CRÉATION/MODIFICATION SIMPLIFIÉE
# ================================

class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la création de produits"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category', 'unit', 'purchase_price', 'selling_price',
            'current_stock', 'alert_threshold', 'barcode', 'image_url', 'is_active'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)


class CustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la création de clients"""
    
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'address', 'notes', 'is_active'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)


class SupplierCreateSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la création de fournisseurs"""
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'email', 'phone', 'address', 'contact_person', 'notes', 'is_active'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)