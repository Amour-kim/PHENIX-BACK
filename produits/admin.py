from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from django.utils import timezone
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


# ================================
# MIXINS ET CLASSES UTILITAIRES
# ================================

class BaseModelAdmin(admin.ModelAdmin):
    """Classe de base pour tous les admins avec UUID et traçabilité"""
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # création
            obj.created_by = request.user
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        obj.save()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj) or [])
        # Ajout des champs de date et d'audit en lecture seule
        audit_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
        for field in audit_fields:
            if field not in readonly_fields and hasattr(self.model, field):
                readonly_fields.append(field)
        return readonly_fields

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'updated_by')


class CategoryBaseAdmin(BaseModelAdmin):
    """Classe de base pour les admins de catégories"""
    list_display = ('name', 'is_active', 'usage_count', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def usage_count(self, obj):
        return getattr(obj, 'usage_count', 0)
    usage_count.short_description = "Utilisations"
    usage_count.admin_order_field = 'usage_count'


# ================================
# INLINES POUR LES RELATIONS
# ================================

class EntryItemInline(admin.TabularInline):
    model = EntryItem
    extra = 1
    fields = ('product', 'quantity', 'total_price', 'expiry_date', 'batch_number')
    readonly_fields = ('total_price',)
    autocomplete_fields = ('product',)
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == 'COMPLETED':
            readonly_fields.extend(['product', 'quantity', 'expiry_date', 'batch_number'])
        return readonly_fields


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs created_by et updated_by invisibles
        if 'created_by' in self.fields:
            self.fields['created_by'].widget = forms.HiddenInput()
        if 'updated_by' in self.fields:
            self.fields['updated_by'].widget = forms.HiddenInput()


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    form = SaleItemForm
    extra = 1
    fields = ('product', 'quantity', 'discount', 'tax_rate', 'total_price')
    readonly_fields = ('total_price', 'created_by', 'updated_by')
    autocomplete_fields = ('product',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if not obj.pk:  # Si c'est un nouvel objet
                obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
        formset.save_m2m()
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and hasattr(obj, 'sale') and hasattr(obj.sale, 'status') and hasattr(obj.sale.status, 'code') and obj.sale.status.code in ['COMPLETED', 'REFUNDED']:
            readonly_fields.extend(['product', 'quantity', 'discount', 'tax_rate'])
        return readonly_fields


class PricingPlanFeatureInline(admin.TabularInline):
    model = RecurringExpense
    extra = 0
    fields = ('name', 'amount', 'frequency', 'next_due_date', 'is_active')
    readonly_fields = ('created_by', 'updated_by')


# ================================
# ADMIN DES CATÉGORIES MODULAIRES
# ================================

@admin.register(ProductCategory)
class ProductCategoryAdmin(CategoryBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('product', distinct=True)
        )


@admin.register(ProductUnit)
class ProductUnitAdmin(CategoryBaseAdmin):
    list_display = ('name', 'abbreviation', 'is_active', 'usage_count', 'created_by', 'created_at')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'abbreviation', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('product', distinct=True)
        )


@admin.register(UserRole)
class UserRoleAdmin(CategoryBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('users', distinct=True)
        )


@admin.register(UserStatus)
class UserStatusAdmin(CategoryBaseAdmin):
    list_display = ('name', 'is_default', 'is_active', 'usage_count', 'created_by', 'created_at')
    list_editable = ('is_default', 'is_active')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'description', 'is_default', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('appuser', distinct=True)
        )


@admin.register(EntryType)
class EntryTypeAdmin(CategoryBaseAdmin):
    list_display = ('name', 'code', 'is_active', 'usage_count', 'created_by', 'created_at')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('entry', distinct=True)
        )


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(CategoryBaseAdmin):
    list_display = ('name', 'code', 'is_active', 'usage_count', 'created_by', 'created_at')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('expense', distinct=True) + Count('recurringexpense', distinct=True)
        )


@admin.register(ExpenseStatus)
class ExpenseStatusAdmin(CategoryBaseAdmin):
    list_display = ('name', 'code', 'is_active', 'usage_count', 'created_by', 'created_at')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('expense', distinct=True)
        )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(CategoryBaseAdmin):
    list_display = ('name', 'code', 'is_active', 'usage_count', 'created_by', 'created_at')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('expense', distinct=True) + Count('sale', distinct=True)
        )


@admin.register(SaleStatus)
class SaleStatusAdmin(CategoryBaseAdmin):
    list_display = ('name', 'code', 'is_active', 'usage_count', 'created_by', 'created_at')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('sale', distinct=True)
        )


@admin.register(PaymentStatus)
class PaymentStatusAdmin(CategoryBaseAdmin):
    list_display = ('name', 'code', 'is_active', 'usage_count', 'created_by', 'created_at')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            usage_count=Count('sale', distinct=True)
        )


# ================================
# ADMIN DES MODÈLES PRINCIPAUX
# ================================

@admin.register(Supplier)
class SupplierAdmin(BaseModelAdmin):
    list_display = ('name', 'email', 'phone', 'contact_person', 'is_active', 'entries_count', 'expenses_count', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'email', 'phone', 'contact_person')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'email', 'phone', 'contact_person', 'is_active')
        }),
        ('Adresse', {
            'fields': ('address',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            entries_count=Count('entry', distinct=True),
            expenses_count=Count('expense', distinct=True)
        )

    def entries_count(self, obj):
        return obj.entries_count
    entries_count.short_description = "Entrées"
    entries_count.admin_order_field = 'entries_count'

    def expenses_count(self, obj):
        return obj.expenses_count
    expenses_count.short_description = "Dépenses"
    expenses_count.admin_order_field = 'expenses_count'


@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'is_active', 'sales_count', 'total_purchases', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Informations Personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'is_active')
        }),
        ('Adresse', {
            'fields': ('address',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            sales_count=Count('sale', distinct=True),
            total_purchases=Sum('sale__total_amount') or 0
        )

    def sales_count(self, obj):
        return obj.sales_count
    sales_count.short_description = "Ventes"
    sales_count.admin_order_field = 'sales_count'

    def total_purchases(self, obj):
        return f"{obj.total_purchases:.2f} €" if obj.total_purchases else "0.00 €"
    total_purchases.short_description = "Total achats"
    total_purchases.admin_order_field = 'total_purchases'


@admin.register(Product)
class ProductAdmin(BaseModelAdmin):
    list_display = ('name', 'category', 'unit', 'selling_price', 'current_stock', 'stock_status', 'is_active', 'created_by', 'created_at')
    list_filter = ('category', 'unit', 'is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description', 'barcode')
    list_editable = ('is_active',)
    autocomplete_fields = ('category', 'unit')
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'description', 'category', 'unit', 'barcode', 'image_url', 'is_active')
        }),
        ('Tarification', {
            'fields': ('purchase_price', 'selling_price')
        }),
        ('Stock', {
            'fields': ('current_stock', 'alert_threshold')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_active', 'mark_as_inactive', 'reset_stock_alert']

    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">Stock faible</span>'
            )
        return format_html(
            '<span style="color: green;">Normal</span>'
        )
    stock_status.short_description = "État du stock"

    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} produits activés.')
    mark_as_active.short_description = "Activer les produits sélectionnés"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} produits désactivés.')
    mark_as_inactive.short_description = "Désactiver les produits sélectionnés"

    def reset_stock_alert(self, request, queryset):
        updated = queryset.update(alert_threshold=5)
        self.message_user(request, f'Seuil d\'alerte remis à 5 pour {updated} produits.')
    reset_stock_alert.short_description = "Remettre le seuil d'alerte à 5"


@admin.register(TimeSlot)
class TimeSlotAdmin(BaseModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'is_active', 'order', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', 'start_time')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'description', 'is_active', 'order')
        }),
        ('Horaires', {
            'fields': ('start_time', 'end_time')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# ================================
# ADMIN DES ENTRÉES DE STOCK
# ================================

@admin.register(Entry)
class EntryAdmin(BaseModelAdmin):
    list_display = ('reference', 'entry_type', 'supplier', 'entry_date', 'total_amount', 'status', 'created_by', 'created_at')
    list_filter = ('entry_type', 'supplier', 'status', 'entry_date', 'created_at', 'created_by')
    search_fields = ('reference', 'notes')
    autocomplete_fields = ('entry_type', 'supplier')
    date_hierarchy = 'entry_date'
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('entry_type', 'supplier', 'entry_date', 'status')
        }),
        ('Montants', {
            'fields': ('total_amount', 'tax_amount')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Récupère les champs en lecture seule de la classe parente
        readonly_fields = list(super().get_readonly_fields(request, obj))
        # Ajoute la référence aux champs en lecture seule si c'est une modification
        if obj:
            readonly_fields.append('reference')
        return readonly_fields

    inlines = [EntryItemInline]
    
    actions = ['mark_as_completed', 'mark_as_cancelled']

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f"{updated} entrées marquées comme terminées avec succès.")
    mark_as_completed.short_description = "Marquer comme terminé"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f"{updated} entrées annulées avec succès.")
    mark_as_cancelled.short_description = "Annuler les entrées sélectionnées"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Si c'est une nouvelle entrée
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EntryItem)
class EntryItemAdmin(BaseModelAdmin):
    list_display = ('entry', 'product', 'quantity', 'total_price', 'expiry_date', 'created_by', 'created_at')
    list_filter = ('entry__entry_type', 'product__category', 'expiry_date', 'created_at', 'created_by')
    search_fields = ('entry__reference', 'product__name', 'batch_number')
    autocomplete_fields = ('entry', 'product')
    readonly_fields = BaseModelAdmin.readonly_fields + ('total_price',)


# ================================
# ADMIN DES DÉPENSES
# ================================

@admin.register(RecurringExpense)
class RecurringExpenseAdmin(BaseModelAdmin):
    list_display = ('name', 'category', 'amount', 'frequency', 'next_due_date', 'is_active', 'generated_count', 'created_by', 'created_at')
    list_filter = ('category', 'frequency', 'is_active', 'next_due_date', 'created_at', 'created_by')
    search_fields = ('name', 'description')
    autocomplete_fields = ('category',)
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'description', 'category', 'is_active')
        }),
        ('Récurrence', {
            'fields': ('amount', 'frequency', 'next_due_date')
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            generated_count=Count('expense', distinct=True)
        )

    def generated_count(self, obj):
        return obj.generated_count
    generated_count.short_description = "Dépenses générées"
    generated_count.admin_order_field = 'generated_count'


@admin.register(Expense)
class ExpenseAdmin(BaseModelAdmin):
    list_display = ('reference', 'description', 'category', 'total_amount', 'expense_date', 'status', 'supplier', 'created_by', 'created_at')
    list_filter = ('category', 'status', 'payment_method', 'supplier', 'expense_date', 'created_at', 'created_by')
    search_fields = ('reference', 'description')
    autocomplete_fields = ('category', 'status', 'payment_method', 'supplier', 'recurring_expense')
    date_hierarchy = 'expense_date'
    readonly_fields = BaseModelAdmin.readonly_fields + ('total_amount',)
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('reference', 'description', 'category', 'supplier')
        }),
        ('Montants', {
            'fields': ('amount', 'tax_amount', 'total_amount')
        }),
        ('Dates', {
            'fields': ('expense_date', 'due_date', 'payment_date')
        }),
        ('Paiement', {
            'fields': ('payment_method', 'status')
        }),
        ('Autres', {
            'fields': ('receipt_url', 'notes', 'recurring_expense'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_paid', 'mark_as_cancelled']

    def mark_as_paid(self, request, queryset):
        paid_status = ExpenseStatus.objects.filter(code='PAID').first()
        if paid_status:
            updated = queryset.update(status=paid_status, payment_date=timezone.now().date())
            self.message_user(request, f'{updated} dépenses marquées comme payées.')
        else:
            self.message_user(request, 'Statut "PAID" introuvable.', level='error')
    mark_as_paid.short_description = "Marquer comme payé"

    def mark_as_cancelled(self, request, queryset):
        cancelled_status = ExpenseStatus.objects.filter(code='CANCELLED').first()
        if cancelled_status:
            updated = queryset.update(status=cancelled_status)
            self.message_user(request, f'{updated} dépenses annulées.')
        else:
            self.message_user(request, 'Statut "CANCELLED" introuvable.', level='error')
    mark_as_cancelled.short_description = "Annuler les dépenses sélectionnées"


# ================================
# ADMIN DES VENTES
# ================================

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('reference', 'customer_display', 'sale_date', 'total_amount', 'payment_method', 'status', 'is_take_away', 'created_by', 'created_at')
    list_filter = ('payment_method', 'payment_status', 'status', 'is_take_away', 'sale_date', 'created_at', 'created_by')
    search_fields = ('reference', 'customer_name', 'customer_phone', 'table_number')
    autocomplete_fields = ('customer', 'payment_method', 'payment_status', 'status')
    date_hierarchy = 'sale_date'
    readonly_fields = ('total_amount', 'created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [SaleItemInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if not obj.pk:  # Si c'est un nouvel objet
                obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            
            # Mise à jour du stock si la vente est marquée comme terminée
            if hasattr(obj.sale, 'status') and obj.sale.status and hasattr(obj.sale.status, 'code') and obj.sale.status.code == 'COMPLETED':
                if hasattr(obj, 'product') and obj.product:
                    obj.product.current_stock -= obj.quantity
                    obj.product.save()
        
        formset.save_m2m()
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('customer', 'sale_date', 'table_number', 'is_take_away')
        }),
        ('Client sans compte', {
            'fields': ('customer_name', 'customer_phone'),
            'description': 'À utiliser si le client n\'a pas de compte'
        }),
        ('Montants', {
            'fields': ('subtotal', 'discount_amount', 'tax_amount', 'total_amount')
        }),
        ('Paiement', {
            'fields': ('payment_method', 'payment_status', 'status')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def customer_display(self, obj):
        if obj.customer:
            return str(obj.customer)
        return obj.customer_name or "Client anonyme"
    customer_display.short_description = "Client"
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # Si l'objet existe déjà
            readonly_fields.append('reference')
        return readonly_fields

    actions = ['mark_as_completed', 'mark_as_cancelled']

    def mark_as_completed(self, request, queryset):
        completed_status = SaleStatus.objects.filter(code='COMPLETED').first()
        if completed_status:
            updated = queryset.update(status=completed_status)
            self.message_user(request, f'{updated} ventes marquées comme terminées.')
        else:
            self.message_user(request, 'Statut "COMPLETED" introuvable.', level='error')
    mark_as_completed.short_description = "Marquer comme terminé"

    def mark_as_cancelled(self, request, queryset):
        cancelled_status = SaleStatus.objects.filter(code='CANCELLED').first()
        if cancelled_status:
            updated = queryset.update(status=cancelled_status)
            self.message_user(request, f'{updated} ventes annulées.')
        else:
            self.message_user(request, 'Statut "CANCELLED" introuvable.', level='error')
    mark_as_cancelled.short_description = "Annuler les ventes sélectionnées"


@admin.register(SaleItem)
class SaleItemAdmin(BaseModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'discount', 'total_price', 'created_by', 'created_at')
    list_filter = ('sale__status', 'product__category', 'sale__sale_date', 'created_at', 'created_by')
    search_fields = ('sale__reference', 'product__name')
    autocomplete_fields = ('sale', 'product')
    readonly_fields = BaseModelAdmin.readonly_fields + ('total_price',)


@admin.register(UserTimeSlot)
class UserTimeSlotAdmin(BaseModelAdmin):
    """Administration des associations utilisateurs-créneaux horaires"""
    list_display = ('user_display', 'time_slot_display', 'is_active', 'created_by', 'created_at')
    list_filter = ('time_slot', 'is_active', 'created_at', 'created_by')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'time_slot__name')
    list_editable = ('is_active',)
    autocomplete_fields = ('user', 'time_slot')
    
    fieldsets = (
        ('Association', {
            'fields': ('user', 'time_slot', 'is_active')
        }),
        ('Détails', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "-"
    user_display.short_description = "Utilisateur"
    user_display.admin_order_field = 'user__first_name'
    
    def time_slot_display(self, obj):
        if obj.time_slot:
            return f"{obj.time_slot.name} ({obj.time_slot.start_time.strftime('%H:%M')}-{obj.time_slot.end_time.strftime('%H:%M')})"
        return "-"
    time_slot_display.short_description = "Créneau horaire"
    time_slot_display.admin_order_field = 'time_slot__name'



# ================================
# PERSONNALISATION DE L'ADMIN
# ================================

# Configuration globale de l'admin
admin.site.site_header = "Analytics Suite - Administration"
admin.site.site_title = "Analytics Suite Admin"
admin.site.index_title = "Gestion de la Suite Analytics"

# Configuration des champs autocomplete pour améliorer les performances
# Note: Les modèles non utilisés ont été commentés
Product.search_fields = ['name', 'description']
