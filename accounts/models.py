from django.db import models
from django.conf import settings
from django.db.models import Sum

class PointsTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="المستخدم")
    amount = models.IntegerField(verbose_name="القيمة (موجب للإضافة، سالب للخصم)")
    date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ العملية")
    note = models.CharField(max_length=255, blank=True, null=True, verbose_name="ملاحظات")
    extra_data = models.TextField(blank=True, null=True, verbose_name="بيانات إضافية")

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.user.username}: {sign}{self.amount} نقطة بتاريخ {self.date.strftime('%Y-%m-%d %H:%M')}"

    @staticmethod
    def get_user_balance(user):
        """
        إرجاع مجموع النقاط للمستخدم بشكل آمن.
        يستخدم فلتر على user_id (أسرع وأوضح) ويعالج حالة None.
        """
        # نستخدم user_id لتجنّب أي تحويل غير مقصود إذا مررنا كائن User أو id
        user_id = user.id if hasattr(user, "id") else int(user)
        result = PointsTransaction.objects.filter(user_id=user_id).aggregate(total=Sum('amount'))
        total = result.get('total')
        return int(total) if total is not None else 0

    class Meta:
        verbose_name = "عملية نقاط"
        verbose_name_plural = "عمليات النقاط"
