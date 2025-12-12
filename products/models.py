from django.db import models
from stores.models import Store
from django.db.models import Sum, F


class Category(models.Model):
    name = models.CharField(max_length=255)
    store = models.ForeignKey("stores.Store", on_delete=models.CASCADE, related_name="categories")
    
    def __str__(self):
        return self.name


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
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
    category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name="products")
    category2 = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name="secondary_products")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
# ⭐⭐⭐ المخزون الحقيقي = مجموع (الكمية × الاتجاه)
    @property
    def real_stock(self):
        total = self.orderitem_set.aggregate(
        total=Sum(F("quantity") * F("direction"))
        )["total"]
        return total or 0

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
