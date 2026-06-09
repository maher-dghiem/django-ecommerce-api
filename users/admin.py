# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("id", "email", "username", "is_staff", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)

    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("phone", "avatar")}),
    )
