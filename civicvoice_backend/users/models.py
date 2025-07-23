
from typing import ClassVar
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.db.models import EmailField
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
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    username = None  # type: ignore

    # Custom fields
    name = CharField(_("Name of User"), blank=True, max_length=255)
    reset_password_token = CharField(max_length=255, blank=True, null=True)
    reset_otp= CharField(max_length=6, blank=True, null=True)
    verify_token = CharField(max_length=255, blank=True, null=True)
    email = EmailField(_("email address"), unique=True)

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