
from typing import ClassVar
from django.contrib.auth.models import AbstractUser
from django.db import models 
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for CivicVoice-Backend.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """
    
    # Overriding fields in AbstractUser
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='users/images/', blank=True, null=True)

    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    reset_password_token = models.CharField(max_length=255, blank=True, null=True)
    reset_otp= models.CharField(max_length=6, blank=True, null=True)
    verify_token = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(_("email address"), unique=True)

    # Update the USERNAME_FIELD and REQUIRED_FIELDS
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})