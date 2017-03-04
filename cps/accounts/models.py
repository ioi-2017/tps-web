# Mohammad Javad Naderi
import random
import string

from django.contrib.auth.models import AbstractUser, Permission
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings
from tempfile import TemporaryDirectory
from gnupg import GPG
from django.core.mail import send_mail


class User(AbstractUser):
    """
    CPS' customized User model
    """

    gpg_key = models.TextField(verbose_name=_("gpg key"), blank=True)

    def send_mail(self, subject, body):
        if self.gpg_key:
            with TemporaryDirectory() as tmp_dir:
                gpg = GPG(homedir=tmp_dir)
                key = gpg.import_keys(self.gpg_key)
                body = str(gpg.encrypt(body, *key.fingerprints))
        send_mail(subject, body, settings.EMAIL_ADDRESS, [self.email])

    def generate_password(self):
        password = ''.join(random.SystemRandom().choice(
            string.ascii_uppercase + string.digits + string.ascii_lowercase
        ) for _ in range(16))
        self.set_password(password)
        self.save()
        return password

