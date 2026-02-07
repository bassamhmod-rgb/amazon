from django.db import models
from django.contrib.auth.models import User

from stores.models import Store, StorePaymentMethod
from accounts.models import Customer


STATUS_CHOICES = [
    ("pending", "قيد الانتظار"),
    ("confirmed", "تم التأكيد"),
]

TRANSACTION_TYPES = [
    ("sale", "بيع"),
    ("purchase", "شراء"),
]

PAYMENT_TYPES = [
    ("full", "تحويل كامل"),
    ("partial", "دفعة مسبقة + باقي عند التسليم"),
    ("cod", "الدفع عند الاستلام"),
]


class Order(models.Model):
    is_seen_by_store = models.BooleanField(default=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    supplier = models.ForeignKey(
        "accounts.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    accounting_invoice_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="رقم الفاتورة في برنامج المحاسبة"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        default="sale"
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # ================= الدفع =================

    payment_method = models.ForeignKey(
        StorePaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    payment_method_name = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    payment_recipient_name = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    payment_account_info = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    payment_additional_info = models.TextField(
        blank=True,
        null=True
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        blank=True,
        null=True
    )

    payment_proof_image = models.ImageField(
        upload_to="payments/",
        blank=True,
        null=True
    )

    payment_transaction_id = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    shipping_address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    DOCUMENT_KINDS = (
    (1, "Invoice"),   # فاتورة
    (2, "Notice"),    # إشعار (قبض / صرف)
)

    document_kind = models.SmallIntegerField(
    choices=DOCUMENT_KINDS,
    default=1,
    help_text="1 = فاتورة, 2 = إشعار قبض/صرف"
)

    def __str__(self):
        return f"Order #{self.id} – {self.store.name}"

    # ================= حسابات =================

    @property
    def items_total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def net_total(self):
        return self.items_total - self.discount

    @property
    def remaining(self):
        return self.net_total - self.payment


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # ✅ الربط الصحيح (Lazy Reference)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    direction = models.IntegerField(
        default=-1,
        help_text="بيع = -1 / شراء = +1"
    )

    item_note = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات المنتج"
    )

    buy_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="تكلفة القطعة وقت البيع / سعر الشراء"
    )

    @property
    def subtotal(self):
        return self.price * abs(self.quantity)

    @property
    def profit(self):
        if self.direction == 1 or self.buy_price is None:
            return 0
        return (self.price - self.buy_price) * abs(self.quantity)
