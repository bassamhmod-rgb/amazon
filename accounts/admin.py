from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Sum
from .models import PointsTransaction

User = get_user_model()

@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'date', 'note')
    list_filter = ('user', 'date')
    search_fields = ('user__username', 'note')
    ordering = ('-date',)


# نضيف عمود الرصيد للمستخدمين مع دعم للفرز عن طريق annotate في queryset
class UserAdmin(BaseUserAdmin):
    def get_points_balance(self, obj):
        # نعتمد على الدالة الآمنة في الموديل
        return PointsTransaction.get_user_balance(obj)
    get_points_balance.short_description = "رصيد النقاط"
    get_points_balance.admin_order_field = 'points_balance'  # اسم الحقل المُعلَن في queryset


def get_queryset(self, request):
    qs = super().get_queryset(request)
    qs = qs.annotate(points_balance=Sum('pointstransaction_set__amount'))
    return qs

list_display = BaseUserAdmin.list_display + ('get_points_balance',)



# unregister ثم register الموديل المعدل
try:
    admin.site.unregister(User)
except Exception:
    pass
admin.site.register(User, UserAdmin)

