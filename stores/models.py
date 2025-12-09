from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class Store(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True)
    mobile = models.CharField(max_length=20)
    theme = models.IntegerField(default=1, choices=[(i, f"Theme {i}") for i in range(1, 6)])
    description = models.TextField(blank=True)
    description2 = models.TextField(blank=True)
    description3 = models.TextField(blank=True)
    description4 = models.TextField(blank=True)
    description5 = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    allow_full_payment = models.BooleanField(default=True)   # تحويل كامل
    allow_partial_payment = models.BooleanField(default=False)  # دفعة مسبقة + باقي عند التسليم
    allow_cash_on_delivery = models.BooleanField(default=False)  # الدفع عند الاستلام
 # ⭐ نسبة الدفع المطلوبة لجميع طرق الدفع
    payment_required_percentage = models.PositiveIntegerField(default=0)

# تعريف "دالة" لعرض الوصف بشكل منسق
    @property
    def formatted_description(self):
        """تُرجع الوصف مسبوقاً برمز النجمة."""
        return f"🌟 {self.description}"
    
    def __str__(self):
        return self.name
    
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

#طرق الدفع
class StorePaymentMethod(models.Model):

    PAYMENT_TYPES = [
        ("cash", "Cash"),
        ("cod", "Cash on Delivery"),
        ("bank", "Bank Transfer"),
        ("wallet", "E-Wallet"),
        ("hawala", "Hawala / حوالة"),
        ("other", "Other"),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    # الاسم الظاهر على صفحة الدفع
    name = models.CharField(max_length=100)

    # نوع الطريقة (مو ضروري يستخدمو التاجر)
    type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default="other")

    # حقول التفاصيل حسب الحاجة
    recipient_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    # صورة شعار / أيقونة للطريقة
    icon = models.ImageField(upload_to="payment_icons/", blank=True, null=True)

    # ترتيب + تفعيل
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.store.name} – {self.name}"
