from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "stock", "category", "category2", "main_image", "description", "active"]
        labels = {
            "name": "اسم المنتج",
            "price": "السعر",
            "stock": "الكمية بالمخزون",
            "category": "الفئة",
            "category2": "فئة فرعية",
            "main_image": "الصورة الرئيسية",
            "description": "الوصف",
            "active": "مفعل؟",
        }

    def __init__(self, *args, **kwargs):
        store = kwargs.pop("store", None)  # 🔥 استلام المتجر
        super().__init__(*args, **kwargs)

        if store:
            # 🔥 فلترة الفئات تبع نفس المتجر فقط
            qs = Category.objects.filter(store=store)
            self.fields["category"].queryset = qs
            self.fields["category2"].queryset = qs
        else:
            self.fields["category"].queryset = Category.objects.none()
            self.fields["category2"].queryset = Category.objects.none()


# 👇 يبقى كما هو
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
