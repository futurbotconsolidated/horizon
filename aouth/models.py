from django.db import models

from django.contrib.auth.models import AbstractUser, BaseUserManager
import datetime

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=str(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):

    GENDER_CHOICES = (
        ('M','Male'),
        ('F','Female'),
        ('O','Others'),
    )

    email = models.EmailField(
        verbose_name='Email Address',
        max_length=254,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    # User Profile Fields
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    full_name = models.CharField(max_length=254)
    gender = models.CharField(max_length=1,choices=GENDER_CHOICES)
    phone = models.CharField(max_length=13, unique=True)
    phone_verified = models.BooleanField(default=False)
    avatar = models.CharField(max_length=254, default="avatar.png")
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = CustomUserManager()
    
    def save(self, *args, **kwargs):
        self.username = str(self.phone)
        super(CustomUser, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.phone