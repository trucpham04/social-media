from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_USER = "user"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ADMIN, "Admin"),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
    )
    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self) -> str:
        return self.username or self.email
