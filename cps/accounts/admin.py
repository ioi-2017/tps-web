# Mohammad Javad Naderi
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib import admin

from django.template.loader import render_to_string
from import_export.admin import ImportExportModelAdmin

from accounts.models import User
from django.utils.translation import ugettext_lazy as _


def generate_password_and_send_mail(modeladmin, request, queryset):
    for user in queryset.all():
        if not user.gpg_key:
            messages.error(request, "Can only generate passwords for users with GPG key")
            return
    count = 0
    for user in queryset.all():

        email_text = render_to_string("accounts/user_info_email.txt", context={
            "first_name": user.get_full_name(),
            "username": user.username,
            "password": user.generate_password()
        })
        user.send_mail("User details for {}".format(user.get_full_name()), email_text)
        count += 1
    messages.success(request, "{} emails sent successfully".format(count))
generate_password_and_send_mail.short_description = "Generate password and send through email"


def has_gpg_key(obj):
    if obj.gpg_key:
        return True
    return False
has_gpg_key.short_description = "Has GPG?"


class UserAdmin(DjangoUserAdmin, ImportExportModelAdmin):
    actions = [generate_password_and_send_mail, ]
    list_display = ("username", "first_name", "last_name", has_gpg_key, )
    list_display_links = ("username", )
    fieldsets = (
        (None, {'fields': ('username', 'password', 'gpg_key')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(User, UserAdmin)
