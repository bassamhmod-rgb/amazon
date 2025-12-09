from django.db import models
from django.contrib.auth.models import User
from stores.models import Store
from products.models import Product

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="carts")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user} - {self.store}"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def get_total(self):
        return self.total()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_note = models.TextField(blank=True, null=True, verbose_name="ملاحظات المنتج")
    def subtotal(self):
        return self.product.price * self.quantity
