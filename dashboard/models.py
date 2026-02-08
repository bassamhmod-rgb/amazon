from decimal import Decimal

from django.db import models
from django.utils import timezone

from stores.models import Store


class ExpenseType(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="expense_types")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ExpenseReason(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="expense_reasons")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Expense(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="expenses")
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    date = models.DateField(default=timezone.now)
    expense_type = models.ForeignKey(
        ExpenseType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    expense_reason = models.ForeignKey(
        ExpenseReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.store} - {self.amount}"
