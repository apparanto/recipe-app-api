from django.db import models
from django.contrib.auth.models import \
    AbstractBaseUser, \
    BaseUserManager, \
    PermissionsMixin
from django.utils.translation import gettext_lazy as _


def validateEmail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        '''Create and saves a new user'''
        if not email or validateEmail(email) is False:
            raise ValueError(_('%(email) is not a valid e-mail address'))

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        '''Creates a new super user'''
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''Custom user model that supports using email instead of username'''
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'email'