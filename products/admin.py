from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "stock")
    list_filter = ("price",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("price", "stock")

