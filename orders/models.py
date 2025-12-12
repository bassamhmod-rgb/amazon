from django.db import models
from django.contrib.auth.models import User
from stores.models import Store
from products.models import Product
from accounts.models import Customer
from stores.models import StorePaymentMethod

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    supplier = models.ForeignKey(
    "accounts.Supplier",
    on_delete=models.SET_NULL,
    null=True, blank=True,
    related_name="orders"
)

    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default="sale")
    # 🔵 نوع طريقة الدفع الأصلية (ربط مع جدول StorePaymentMethod)
    payment_method = models.ForeignKey(
    StorePaymentMethod,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="orders_payment"
)


    # 🔵 نسخة ثابتة من اسم الطريقة
    payment_method_name = models.CharField(max_length=120, blank=True, null=True)

    # 🔵 اسم الشخص الذي ستذهب له الدفعة (مفيد للحوالات)
    payment_recipient_name = models.CharField(max_length=120, blank=True, null=True)

    # 🔵 رقم الحساب / رقم الهاتف / رقم التحويل / حسب نوع الدفع
    payment_account_info = models.CharField(max_length=255, blank=True, null=True)

    # 🔵 تفاصيل إضافية (ملاحظات الدفع)
    payment_additional_info = models.TextField(blank=True, null=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, blank=True, null=True)
    shipping_address = models.CharField(max_length=255, blank=True, null=True)
    payment_proof_image = models.ImageField(upload_to="payments/", blank=True, null=True)
    payment_transaction_id = models.CharField(max_length=120, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.store.name}"

    # 🔥 مجموع كل العناصر قبل الحسم
    @property
    def items_total(self):
        return sum(item.subtotal for item in self.items.all())

    # 🔥 قبل الحسم
    @property
    def total_before_discount(self):
        return self.items_total

    # 🔥 صافي بعد الحسم
    @property
    def net_total(self):
        return self.items_total - self.discount

    # 🔥 المتبقي بعد الدفع
    @property
    def remaining(self):
        return self.net_total - self.payment



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    direction = models.IntegerField(default=-1)  # بيع = -1 / شراء = +1
    item_note = models.TextField(blank=True, null=True, verbose_name="ملاحظات المنتج")
    buy_price = models.DecimalField(
    
    max_digits=10,
    decimal_places=2,
    null=True,
    blank=True,
    help_text="تكلفة القطعة وقت البيع / سعر الشراء"
)

    # 🔥 مجموع البند المعروض (دائمًا موجب)
    @property
    def subtotal(self):
        return self.price * abs(self.quantity)
    #لحساب متوسط التكلفة عند البيع
    @property
    def profit(self):
        # شراء → لا يوجد ربح
        if self.direction == 1:
            return 0
        
        if self.buy_price is None:
            return 0
        
        return (self.price - self.buy_price) * abs(self.quantity)