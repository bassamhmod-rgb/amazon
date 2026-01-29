from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "mobile", "rkmdb", "rkmtb", "theme", "is_active")
    search_fields = ("name", "owner__username")
    list_filter = ("theme", "is_active")

