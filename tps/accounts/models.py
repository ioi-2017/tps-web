# Mohammad Javad Naderi
import random
import string

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser, Permission, UserManager, PermissionsMixin
from django.core import validators
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings
from tempfile import TemporaryDirectory
from pretty_bad_protocol.gnupg import GPG
from django.core.mail import send_mail


class User(AbstractBaseUser, PermissionsMixin):
    """
    CPS' customized User model
    """
    username = models.CharField(
        _('username'),
        max_length=30,
        unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(
                r'^[\w.@+-]+$',
                _('Enter a valid username. This value may contain only '
                  'letters, numbers ' 'and @/./+/-/_ characters.')
            ),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=30, blank=False)
    email = models.EmailField(_('email address'), blank=False)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    gpg_key = models.TextField(verbose_name=_("gpg key"), blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

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

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

