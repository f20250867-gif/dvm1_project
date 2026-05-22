from django.db import models
from django.contrib.auth.models import AbstractUser,Group   
# Create your models here.
class User(AbstractUser):
    
    class Role(models.TextChoices):
        ADMIN = "ADMIN", 'admin'
        DRIVER = "DRIVER", 'driver'
        PASSENGER = "PASSENGER", 'passenger'

    base_role = Role.PASSENGER 
        
    role = models.CharField(max_length=50, choices = Role.choices)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
        super().save(*args, **kwargs)
        self._assign_group()

    def _assign_group(self):
        # Create groups if they don't exist, then assign
        if self.role == self.Role.DRIVER:
            group, _ = Group.objects.get_or_create(name='Driver')
            self.groups.set([group])
        elif self.role == self.Role.PASSENGER:
            group, _ = Group.objects.get_or_create(name='Passenger')
            self.groups.set([group])