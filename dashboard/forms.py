from django import forms
from products.models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = ["store"]   # 🔥 المهم جداً
        labels = {
            "name": "اسم الفئة",
        }
