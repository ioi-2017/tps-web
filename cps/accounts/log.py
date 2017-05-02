from django.utils.log import AdminEmailHandler

__all__ = ["SuperuserEmailHandler"]

class SuperuserEmailHandler(AdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        print("SSS")
        from accounts.models import User
        for user in User.objects.filter(is_superuser=True).all():
            if user.gpg_key:
                user.send_mail(subject, message)
            else:
                user.send_mail(subject, "You may find the details in the logs")