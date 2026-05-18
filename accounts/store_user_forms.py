from django import forms

from .models import StoreUser


class StoreUserForm(forms.ModelForm):
    raw_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        label="كلمة المرور",
        help_text="اتركه فارغاً للإبقاء على كلمة المرور الحالية.",
    )

    sales_orders = forms.BooleanField(required=False, label="السماح بإدخال طلبات البيع")
    purchase_orders = forms.BooleanField(required=False, label="السماح بإدخال طلبات الشراء")
    products = forms.BooleanField(required=False, label="السماح بإدارة المنتجات")

    class Meta:
        model = StoreUser
        fields = [
            "identifier",
            "name",
            "warehouse",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        warehouses_qs = kwargs.pop("warehouses_qs", None)
        super().__init__(*args, **kwargs)

        if warehouses_qs is not None:
            self.fields["warehouse"].queryset = warehouses_qs

        perms = {}
        if self.instance and getattr(self.instance, "permissions", None):
            perms = self.instance.permissions or {}

        if self.instance and self.instance.pk:
            if self.instance.password:
                self.fields["raw_password"].help_text = "كلمة المرور محفوظة (مشفرة). اترك الحقل فارغاً للإبقاء عليها، أو اكتب كلمة جديدة للتغيير."
            else:
                self.fields["raw_password"].help_text = "لم يتم تعيين كلمة مرور بعد. ضع كلمة مرور ليتمكن المستخدم من تسجيل الدخول."

        self.fields["sales_orders"].initial = bool(perms.get("sales_orders"))
        self.fields["purchase_orders"].initial = bool(perms.get("purchase_orders"))
        self.fields["products"].initial = bool(perms.get("products"))

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.permissions = {
            "sales_orders": bool(self.cleaned_data.get("sales_orders")),
            "purchase_orders": bool(self.cleaned_data.get("purchase_orders")),
            "products": bool(self.cleaned_data.get("products")),
        }
        raw_password = self.cleaned_data.get("raw_password")
        if raw_password:
            obj.set_password(raw_password)
        if commit:
            obj.save()
        return obj
