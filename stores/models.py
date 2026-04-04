from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from PIL import Image, ImageOps, UnidentifiedImageError
from decimal import Decimal

class Store(models.Model):
    update_time = models.BigIntegerField(blank=True, null=True)
    access_id = models.BigIntegerField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stores")
    name = models.CharField(max_length=200)
    rkmdb = models.CharField(max_length=100, blank=True, null=True)
    rkmtb = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True)
    mobile = models.CharField(max_length=20, unique=True, blank=True, null=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    telegram_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
    sales_paused = models.BooleanField(default=False)
    sales_pause_message = models.TextField(blank=True)
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
    # للتحكم بابعاد مساحة الصورة
    hero_height = models.PositiveIntegerField(
        default=350,
        help_text="ارتفاع صورة الهيرو بالبكسل"
    )

    # ⭐ نسبة الكاش باك من ربح الطلب (٪)
    cashback_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="نسبة الكاش باك من ربح الطلب (مثال: 5 = 5%)"
    )
    PRICING_CURRENCIES = [
        ("USD", "دولار"),
        ("SYP", "ليرة سورية"),
    ]
    pricing_currency = models.CharField(
        max_length=3,
        choices=PRICING_CURRENCIES,
        default="SYP",
    )
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="سعر صرف الدولار مقابل الليرة السورية (1 USD = ? SYP)"
    )
    hero_fit = models.CharField(
        max_length=10,
        choices=[
            ("contain", "احتواء (بدون قص)"),
            ("cover", "ملء (مع قص)"),
        ],
        default="contain"
    )
    
    
    def save(self, *args, **kwargs):
        # توليد slug (مثل ما كان)
        if not self.slug:
            self.slug = slugify(self.name)

        update_fields = kwargs.get("update_fields")
        should_process_logo = bool(self.logo)
        if update_fields is not None and "logo" not in update_fields:
            should_process_logo = False
        elif self.pk and self.logo:
            old_logo_name = (
                Store.objects.filter(pk=self.pk).values_list("logo", flat=True).first()
            )
            if old_logo_name == self.logo.name:
                should_process_logo = False

        super().save(*args, **kwargs)

        if should_process_logo:
            self._process_logo_image()

        # تعديل الصورة بدون قص
        if False and self.logo:
            img = Image.open(self.logo.path).convert("RGBA")

            TARGET_W, TARGET_H = 1280, 509

            # نحافظ على النسبة
            img.thumbnail((TARGET_W, TARGET_H), Image.LANCZOS)

            # إنشاء خلفية بنفس المقاس
            background = Image.new("RGBA", (TARGET_W, TARGET_H), (255, 255, 255, 255))
            # إذا بدك خلفية لون:
            # background = Image.new("RGBA", (TARGET_W, TARGET_H), "#f7f9fc")

            # توسيط الصورة
            x = (TARGET_W - img.width) // 2
            y = (TARGET_H - img.height) // 2

            background.paste(img, (x, y), img)

            # حفظ نهائي
            background.convert("RGB").save(
                self.logo.path,
                quality=90,
                optimize=True
            )

    @property
    def formatted_description(self):
        return f"🌟 {self.description}"

    def _process_logo_image(self):
        if not self.logo:
            return

        try:
            logo_path = self.logo.path
        except Exception:
            return

        try:
            with Image.open(logo_path).convert("RGBA") as img:
                target_width, target_height = 1280, 509
                img.thumbnail((target_width, target_height), Image.LANCZOS)

                background = Image.new(
                    "RGBA", (target_width, target_height), (255, 255, 255, 255)
                )
                x = (target_width - img.width) // 2
                y = (target_height - img.height) // 2
                background.paste(img, (x, y), img)

                background.convert("RGB").save(
                    logo_path,
                    quality=90,
                    optimize=True,
                )
        except (FileNotFoundError, UnidentifiedImageError, OSError, ValueError):
            return

    def __str__(self):
        return self.name
#طرق الدفع
class StorePaymentMethod(models.Model):
    update_time = models.BigIntegerField(blank=True, null=True)
    access_id = models.BigIntegerField(blank=True, null=True)

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
