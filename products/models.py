from django.db import models
from stores.models import Store
from django.db.models import Sum, F
from decimal import Decimal
from orders.models import OrderItem


class Category(models.Model):
    store = models.ForeignKey("stores.Store", on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="unique_category_name_per_store"
            ),
        ]

    def __str__(self):
        return self.name




class Product(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="products"
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=8, decimal_places=2)

    buy_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="متوسط سعر شراء المنتج"
    )

    stock = models.IntegerField(default=0)
    main_image = models.ImageField(upload_to="products/", blank=True, null=True)

    category = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    category2 = models.ForeignKey(
        "products.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secondary_products"
    )

    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="unique_product_name_per_store"
            ),
        ]

    def __str__(self):
        return self.name

    # ⭐⭐⭐ المخزون الحقيقي = المخزون الابتدائي + الحركات
    @property
    def real_stock(self):
        movements = self.order_items.aggregate(
            total=Sum(F("quantity") * F("direction"))
        )["total"] or 0
        return self.stock + movements

    # ⭐ حساب متوسط سعر الشراء (آمن 100%)
    def get_avg_buy_price(self):
        total_qty = Decimal("0")
        total_cost = Decimal("0")

        items = OrderItem.objects.filter(product=self).order_by("id")

        for item in items:
            qty = Decimal(item.quantity or 0)

            # ⛑️ حماية من None بالبيانات القديمة
            if item.buy_price is not None:
                buy_price = Decimal(item.buy_price)
            elif item.direction == 1 and item.price is not None:
                buy_price = Decimal(item.price)
            else:
                buy_price = Decimal("0")

            cost = buy_price * qty

            if item.direction == 1:  # شراء
                total_qty += qty
                total_cost += cost

            elif item.direction == -1:  # بيع
                if item.buy_price is None:
                    current_avg = (total_cost / total_qty) if total_qty > 0 else Decimal("0")
                    cost = current_avg * qty
                total_qty -= qty
                total_cost -= cost

            # إذا انتهى المخزون نعيد الحساب
            if total_qty <= 0:
                total_qty = Decimal("0")
                total_cost = Decimal("0")

        if total_qty > 0:
            return total_cost / total_qty

        return Decimal("0")

class ProductDetails(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="details")
    title = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.title}"

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="product_gallery/")

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductBarcode(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="barcodes")
    value = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "value"],
                name="unique_product_barcode_value"
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.value}"
