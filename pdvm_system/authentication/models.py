from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from pdvm_basis.pdvm_util import getNewId

# Klasse für das Management des Account
class AccountManager(BaseUserManager):
    def create_user(self, username, email, password, **kwargs):
        if not email:
            raise ValueError('Das Benutzerkonto benötigt eine valide Email-Adresse!')

        if not username:
            raise ValueError('Das Benutzerkonto muss eine validen Namen haben!')

        account = Account(
            id = getNewId(),
            email = email,
            username = username,
            first_name = kwargs.get('first_name'),
            last_name = kwargs.get('last_name')
        )

        account.set_password(password)
        account.save()

        return account

    def create_superuser(self, username, email, password, **kwargs):
        account = self.create_user( username, email, password, **kwargs)

        account.is_admin = True
        account.save()

        return account

# Django Modell für den 'Account' - erzeugt Kommunikation mit der Datenbank
class Account(AbstractBaseUser):
    # id wird mit einer UUID belegt
    id = models.UUIDField(primary_key=True, default=getNewId ,unique=True)
    # Email Adresse zwingend erforderlich
    email = models.EmailField(unique=True)
    # Benutzername zwingend erforderlich - maximal 50 Zeichen lang
    username = models.CharField(max_length=50, blank=False)
    # Vorname nicht zwingend - maximal 50 Zeichen lang
    first_name = models.CharField(max_length=50, blank=True)
    # Nachname nicht zwingend - maximal 50 Zeichen lang
    last_name = models.CharField(max_length=50, blank=True)
    # tagline nicht zwingend - maximal 150 Zeichen lang
    tagline = models.CharField(max_length=150, blank=True)
    # Kurzkommentar - maximal 300 Zeichen lang
    comment = models.CharField(max_length=300, blank= True)

    # Kennzeichen für Adminberechtigung - default nein
    is_admin = models.BooleanField(default=False)

    # Erstellungsdatum - DateTime Feld
    created_at = models.DateTimeField(auto_now_add=True)
    # Änderungsdatum - DateTime Feld
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()
    # Werte von Django User setzen
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __unicode__(self):
        return self.email
   
    def get_full_name(self):
        return ' '.join([self.first_name, self.last_name])

    def get_short_name(self):
        return self.first_name
    @property
    def is_superuser(self):
        return self.is_admin

    @property
    def is_staff(self):
       return self.is_admin

    @property
    def is_activ(self):
       return True

    def has_perm(self, perm, obj=None):
       return self.is_admin

    def has_module_perms(self, app_label):
       return self.is_admin

    @is_staff.setter
    def is_staff(self, value):
        self._is_staff = value
