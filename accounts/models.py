from django.db import models
from stores.models import Store

class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)

    # الحقول الجديدة 👇
    address = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"

    



class PointsTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("add", "إضافة نقاط"),
        ("subtract", "سحب نقاط"),
        ("adjust", "تعديل الرصيد"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="points")
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.points} pts ({self.transaction_type})"
