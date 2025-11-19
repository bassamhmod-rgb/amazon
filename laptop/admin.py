from django.contrib import admin
from .models import  Product,Purchase ,Brand , Laptop , Accessoryl , Accessorym,Category_accessoryl,Category_accessorym,Category
# Register your models here.
admin.site.register(Product)
admin.site.register(Brand)
admin.site.register(Laptop)
admin.site.register(Accessoryl)
admin.site.register(Accessorym)
admin.site.register(Category_accessoryl)
admin.site.register(Category_accessorym)
admin.site.register(Category)
admin.site.register(Purchase)
