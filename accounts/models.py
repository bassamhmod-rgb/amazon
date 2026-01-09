from django.db import models
from stores.models import Store
from django.db.models import Q

class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)

    address = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    # 🔥 الرصيد الحالي للعميل (مبلغ)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="رصيد العميل الحالي (موجب: عليه / سالب: له)"
    )

    # 🔥 الرصيد السابق (اختياري – إن كنت تستخدمه)
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="الرصيد السابق بين التاجر والعميل"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="unique_customer_name_per_store"
            ),
            models.UniqueConstraint(
                fields=["store", "phone"],
                name="unique_customer_phone_per_store"
            ),
        ]
    def save(self, *args, **kwargs):
        # 🔐 ضمان الاسم: إذا فاضي → خليه رقم الهاتف
        if not self.name:
            self.name = self.phone
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.phone}"
    

    



class PointsTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("add", "إضافة نقاط"),
        ("subtract", "سحب نقاط"),
        ("adjust", "تعديل الرصيد"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="points")
    customer_name = models.CharField(max_length=150)
    points = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    access_id = models.IntegerField(
        blank=True,
        null=True,
        help_text="رقم السجل في جدول الكاش باك ببرنامج المحاسبة"
    )
    def __str__(self):
        return f"{self.customer} - {self.points} pts ({self.transaction_type})"
# الموردين

class Supplier(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="suppliers"
    )

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # 🔥 الرصيد السابق بين التاجر والمورّد
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="الرصيد السابق بين التاجر والمورّد"
    )

    # 🔥 الرصيد الحالي للمورّد (مبلغ)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="رصيد المورّد الحالي (موجب: له / سالب: عليه)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
      constraints = [
        models.UniqueConstraint(
            fields=["store", "name"],
            name="unique_supplier_name_per_store"
        ),
        models.UniqueConstraint(
            fields=["store", "phone"],
            condition=Q(phone__isnull=False) & ~Q(phone=""),
            name="unique_supplier_phone_per_store_when_exists"
        ),
    ]


    def __str__(self):
        return self.name
