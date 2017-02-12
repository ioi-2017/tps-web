# Mohammad Javad Naderi
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.translation import ugettext_lazy as _
from django.db import models


class User(AbstractUser):
    """
    CPS' customized User model
    """



