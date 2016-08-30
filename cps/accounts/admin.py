# Mohammad Javad Naderi
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

from accounts.models import User, Permission, Role


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(User, UserAdmin)
