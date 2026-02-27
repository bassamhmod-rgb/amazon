from django.db import models
from django.contrib.auth.models import User

from stores.models import Store, StorePaymentMethod
from accounts.models import Customer
from django.utils import timezone
import time


STATUS_CHOICES = [
    ("pending", "ظ‚ظٹط¯ ط§ظ„ط§ظ†طھط¸ط§ط±"),
    ("confirmed", "طھظ… ط§ظ„طھط£ظƒظٹط¯"),
]

TRANSACTION_TYPES = [
    ("sale", "ط¨ظٹط¹"),
    ("purchase", "ط´ط±ط§ط،"),
]

PAYMENT_TYPES = [
    ("full", "طھط­ظˆظٹظ„ ظƒط§ظ…ظ„"),
    ("partial", "ط¯ظپط¹ط© ظ…ط³ط¨ظ‚ط© + ط¨ط§ظ‚ظٹ ط¹ظ†ط¯ ط§ظ„طھط³ظ„ظٹظ…"),
    ("cod", "ط§ظ„ط¯ظپط¹ ط¹ظ†ط¯ ط§ظ„ط§ط³طھظ„ط§ظ…"),
]



def _touch_update_time(instance, kwargs):
    instance.update_time = int(time.time() // 60)
    update_fields = kwargs.get("update_fields")
    if update_fields:
        update_fields = set(update_fields)
        update_fields.add("update_time")
        kwargs["update_fields"] = update_fields
class Order(models.Model):
    is_seen_by_store = models.BooleanField(default=False)
    update_time = models.BigIntegerField(blank=True, null=True)

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

    created_at = models.DateTimeField(default=timezone.now)

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

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

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
        (1, "Invoice"),
        (2, "Notice"),
    )

    document_kind = models.SmallIntegerField(
        choices=DOCUMENT_KINDS,
        default=1,
        help_text="1 = فاتورة, 2 = إشعار قبض/صرف"
    )

    def __str__(self):
        return f"Order #{self.id} â€“ {self.store.name}"

    def save(self, *args, **kwargs):
        _touch_update_time(self, kwargs)
        return super().save(*args, **kwargs)

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
    update_time = models.BigIntegerField(blank=True, null=True)
    access_id = models.BigIntegerField(blank=True, null=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # âœ… ط§ظ„ط±ط¨ط· ط§ظ„طµط­ظٹط­ (Lazy Reference)
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
        help_text="ط¨ظٹط¹ = -1 / ط´ط±ط§ط، = +1"
    )

    item_note = models.TextField(
        blank=True,
        null=True,
        verbose_name="ظ…ظ„ط§ط­ط¸ط§طھ ط§ظ„ظ…ظ†طھط¬"
    )

    buy_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="طھظƒظ„ظپط© ط§ظ„ظ‚ط·ط¹ط© ظˆظ‚طھ ط§ظ„ط¨ظٹط¹ / ط³ط¹ط± ط§ظ„ط´ط±ط§ط،"
    )

    @property
    def subtotal(self):
        return self.price * abs(self.quantity)

    @property
    def profit(self):
        if self.direction == 1 or self.buy_price is None:
            return 0
        return (self.price - self.buy_price) * abs(self.quantity)

    def save(self, *args, **kwargs):
        _touch_update_time(self, kwargs)
        return super().save(*args, **kwargs)
