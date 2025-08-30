from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class BaseModelWithUUID(models.Model):
    """Modèle de base avec UUID et utilisateur de création/modification"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, 
        related_name="%(class)s_created", 
        verbose_name="Créé par",
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, 
        related_name="%(class)s_updated", 
        verbose_name="Modifié par",
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


# ============= CATÉGORIES MODULAIRES =============

class ProductCategory(BaseModelWithUUID):
    """Catégories de produits modulaires"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'product_category'
        verbose_name = "Catégorie de produit"
        verbose_name_plural = "Catégories de produit"
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductUnit(BaseModelWithUUID):
    """Unités de mesure pour les produits"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom de l'unité")
    abbreviation = models.CharField(max_length=10, unique=True, verbose_name="Abréviation")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'product_unit'
        verbose_name = "Unité de produit"
        verbose_name_plural = "Unités de produit"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class UserRole(BaseModelWithUUID):
    """Rôles des utilisateurs"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du rôle")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'user_role'
        verbose_name = "Rôle utilisateur"
        verbose_name_plural = "Rôles utilisateur"
        ordering = ['name']

    def __str__(self):
        return self.name

class UserStatus(BaseModelWithUUID):
    """Statuts des utilisateurs"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du statut")
    description = models.TextField(blank=True, verbose_name="Description")
    is_default = models.BooleanField(default=False, verbose_name="Statut par défaut")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'user_status'
        verbose_name = "Statut utilisateur"
        verbose_name_plural = "Statuts utilisateur"
        ordering = ['name']

    def __str__(self):
        return self.name

class EntryType(BaseModelWithUUID):
    """Types d'entrée de stock"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du type")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'entry_type'
        verbose_name = "Type d'entrée"
        verbose_name_plural = "Types d'entrée"
        ordering = ['name']

    def __str__(self):
        return self.name


class ExpenseCategory(BaseModelWithUUID):
    """Catégories de dépenses"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'expense_category'
        verbose_name = "Catégorie de dépense"
        verbose_name_plural = "Catégories de dépense"
        ordering = ['name']

    def __str__(self):
        return self.name


class ExpenseStatus(BaseModelWithUUID):
    """Statuts de dépenses"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du statut")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'expense_status'
        verbose_name = "Statut de dépense"
        verbose_name_plural = "Statuts de dépense"
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentMethod(BaseModelWithUUID):
    """Méthodes de paiement"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la méthode")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'payment_method'
        verbose_name = "Méthode de paiement"
        verbose_name_plural = "Méthodes de paiement"
        ordering = ['name']

    def __str__(self):
        return self.name


class SaleStatus(BaseModelWithUUID):
    """Statuts de vente"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du statut")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'sale_status'
        verbose_name = "Statut de vente"
        verbose_name_plural = "Statuts de vente"
        ordering = ['name']

    def __str__(self):
        return self.name


class PaymentStatus(BaseModelWithUUID):
    """Statuts de paiement"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du statut")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'payment_status'
        verbose_name = "Statut de paiement"
        verbose_name_plural = "Statuts de paiement"
        ordering = ['name']

    def __str__(self):
        return self.name


# ============= MODÈLES PRINCIPAUX =============

class Supplier(BaseModelWithUUID):
    """Modèle pour les fournisseurs"""
    name = models.CharField(max_length=200, verbose_name="Nom du fournisseur")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    contact_person = models.CharField(max_length=200, blank=True, verbose_name="Personne de contact")
    notes = models.TextField(blank=True, verbose_name="Notes")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'supplier'
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['name']

    def __str__(self):
        return self.name


class Customer(BaseModelWithUUID):
    """Modèle pour les clients"""
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    notes = models.TextField(blank=True, verbose_name="Notes")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'customer'
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Product(BaseModelWithUUID):
    """Modèle pour les produits"""
    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    description = models.TextField(blank=True, verbose_name="Description")
    category = models.ForeignKey(
        ProductCategory, 
        on_delete=models.PROTECT, 
        verbose_name="Catégorie"
    )
    unit = models.ForeignKey(
        ProductUnit, 
        on_delete=models.PROTECT, 
        verbose_name="Unité"
    )
    purchase_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Prix d'achat"
    )
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Prix de vente"
    )
    current_stock = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock actuel"
    )
    alert_threshold = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name="Seuil d'alerte"
    )
    barcode = models.CharField(max_length=100, blank=True, unique=True, verbose_name="Code-barres")
    image_url = models.URLField(blank=True, verbose_name="URL de l'image")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'product'
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.current_stock <= self.alert_threshold


class TimeSlot(BaseModelWithUUID):
    """Modèle pour les créneaux horaires"""
    name = models.CharField(max_length=100, verbose_name="Nom du créneau")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        db_table = 'time_slot'
        verbose_name = "Créneau horaire"
        verbose_name_plural = "Créneaux horaires"
        ordering = ['order', 'start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class UserTimeSlot(BaseModelWithUUID):
    """Modèle pour les créneaux horaires des utilisateurs"""
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Utilisateur"
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        verbose_name="Créneau horaire"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        db_table = 'user_time_slot'
        verbose_name = "Créneau horaire de l'utilisateur"
        verbose_name_plural = "Créneaux horaires des utilisateurs"

    def __str__(self):
        return f"{self.user} ({self.time_slot})"


# ============= GESTION DES ENTRÉES DE STOCK =============

class Entry(BaseModelWithUUID):
    """Modèle pour les entrées de stock"""
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence")
    entry_type = models.ForeignKey(
        EntryType, 
        on_delete=models.PROTECT, 
        verbose_name="Type d'entrée"
    )
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT, 
        blank=True, 
        null=True, 
        verbose_name="Fournisseur"
    )
    entry_date = models.DateTimeField(default=timezone.now, verbose_name="Date d'entrée")
    notes = models.TextField(blank=True, verbose_name="Notes")
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Montant total"
    )
    tax_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant de la taxe"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Brouillon'),
            ('PENDING', 'En attente'),
            ('COMPLETED', 'Terminé'),
            ('CANCELLED', 'Annulé'),
        ],
        default='COMPLETED',
        verbose_name="Statut"
    )

    class Meta:
        db_table = 'entry'
        verbose_name = "Entrée de stock"
        verbose_name_plural = "Entrées de stock"
        ordering = ['-entry_date']

    def __str__(self):
        return f"{self.reference} - {self.entry_date.strftime('%d/%m/%Y')}"


class EntryItem(BaseModelWithUUID):
    """Modèle pour les articles d'une entrée de stock"""
    entry = models.ForeignKey(
        Entry, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Entrée"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        verbose_name="Produit"
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Quantité"
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Prix unitaire"
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Prix total"
    )
    expiry_date = models.DateField(blank=True, null=True, verbose_name="Date d'expiration")
    batch_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de lot")

    class Meta:
        db_table = 'entry_item'
        verbose_name = "Article d'entrée"
        verbose_name_plural = "Articles d'entrée"

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ============= GESTION DES DÉPENSES =============

class RecurringExpense(BaseModelWithUUID):
    """Modèle pour les dépenses récurrentes"""
    name = models.CharField(max_length=200, verbose_name="Nom de la dépense récurrente")
    description = models.TextField(blank=True, verbose_name="Description")
    category = models.ForeignKey(
        ExpenseCategory, 
        on_delete=models.PROTECT, 
        verbose_name="Catégorie"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Montant"
    )
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('WEEKLY', 'Hebdomadaire'),
            ('MONTHLY', 'Mensuel'),
            ('QUARTERLY', 'Trimestriel'),
            ('YEARLY', 'Annuel'),
        ],
        verbose_name="Fréquence"
    )
    next_due_date = models.DateField(verbose_name="Prochaine échéance")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'recurring_expense'
        verbose_name = "Dépense récurrente"
        verbose_name_plural = "Dépenses récurrentes"
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(BaseModelWithUUID):
    """Modèle pour les dépenses"""
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence")
    description = models.CharField(max_length=255, verbose_name="Description")
    category = models.ForeignKey(
        ExpenseCategory, 
        on_delete=models.PROTECT, 
        verbose_name="Catégorie"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Montant"
    )
    tax_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant de la taxe"
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Montant total"
    )
    expense_date = models.DateField(default=timezone.now, verbose_name="Date de la dépense")
    due_date = models.DateField(blank=True, null=True, verbose_name="Date d'échéance")
    payment_date = models.DateField(blank=True, null=True, verbose_name="Date de paiement")
    payment_method = models.ForeignKey(
        PaymentMethod, 
        on_delete=models.PROTECT, 
        blank=True, 
        null=True,
        verbose_name="Méthode de paiement"
    )
    status = models.ForeignKey(
        ExpenseStatus, 
        on_delete=models.PROTECT, 
        verbose_name="Statut"
    )
    receipt_url = models.URLField(blank=True, verbose_name="URL du reçu")
    notes = models.TextField(blank=True, verbose_name="Notes")
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT, 
        blank=True, 
        null=True,
        verbose_name="Fournisseur"
    )
    recurring_expense = models.ForeignKey(
        RecurringExpense, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        verbose_name="Dépense récurrente"
    )

    class Meta:
        db_table = 'expense'
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.reference} - {self.description}"

    def save(self, *args, **kwargs):
        self.total_amount = self.amount + self.tax_amount
        super().save(*args, **kwargs)


# ============= GESTION DES VENTES =============

class Sale(BaseModelWithUUID):
    """Modèle pour les ventes"""
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence")
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.PROTECT, 
        blank=True, 
        null=True,
        verbose_name="Client"
    )
    sale_date = models.DateTimeField(default=timezone.now, verbose_name="Date de vente")
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Sous-total"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant de la remise"
    )
    tax_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Montant de la taxe"
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Montant total"
    )
    payment_method = models.ForeignKey(
        PaymentMethod, 
        on_delete=models.PROTECT, 
        verbose_name="Méthode de paiement"
    )
    payment_status = models.ForeignKey(
        PaymentStatus, 
        on_delete=models.PROTECT, 
        verbose_name="Statut de paiement"
    )
    status = models.ForeignKey(
        SaleStatus, 
        on_delete=models.PROTECT, 
        verbose_name="Statut"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    table_number = models.CharField(max_length=20, blank=True, verbose_name="Numéro de table")
    is_take_away = models.BooleanField(default=False, verbose_name="À emporter")
    customer_name = models.CharField(max_length=200, blank=True, verbose_name="Nom du client")
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone du client")

    class Meta:
        db_table = 'sale'
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-sale_date']

    def __str__(self):
        return f"{self.reference} - {self.sale_date.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        super().save(*args, **kwargs)


class SaleItem(BaseModelWithUUID):
    """Modèle pour les articles d'une vente"""
    sale = models.ForeignKey(
        Sale, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Vente"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        verbose_name="Produit"
    )
    product_name = models.CharField(max_length=200, verbose_name="Nom du produit")
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        verbose_name="Quantité"
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Prix unitaire"
    )
    discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Remise"
    )
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Taux de taxe (%)"
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Prix total"
    )

    class Meta:
        db_table = 'sale_item'
        verbose_name = "Article de vente"
        verbose_name_plural = "Articles de vente"

    def __str__(self):
        return f"{self.product_name} - {self.quantity}"

    def save(self, *args, **kwargs):
        base_price = self.quantity * self.unit_price
        discounted_price = base_price - self.discount
        tax_amount = discounted_price * (self.tax_rate / 100)
        self.total_price = discounted_price + tax_amount
        super().save(*args, **kwargs)