# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN","Admin"
        DRIVER = "DRIVER","Driver"
        PASSENGER = "PASSENGER", "Passenger"

    base_role = Role.PASSENGER

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.PASSENGER
    )

    wallet_balance = models.DecimalField(    
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    def save(self, *args, **kwargs):         
        if not self.pk and not self.role:
            self.role = self.base_role
        super().save(*args, **kwargs)
        self._assign_group()
        self._create_profile()

    def _assign_group(self):
        if self.role == self.Role.DRIVER:
            group, _ = Group.objects.get_or_create(name='Driver')
            self.groups.set([group])
        elif self.role == self.Role.PASSENGER:
            group, _ = Group.objects.get_or_create(name='Passenger')
            self.groups.set([group])

    def _create_profile(self):
        if self.role == self.Role.DRIVER:
            DriverProfile.objects.get_or_create(user=self)
        elif self.role == self.Role.PASSENGER:
            PassengerProfile.objects.get_or_create(user=self)

    def __str__(self):
        return f"{self.username} ({self.role})"


class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Driver: {self.user.username}"


class PassengerProfile(models.Model):
    user= models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_profile')

    def __str__(self):
        return f"Passenger: {self.user.username}"


class Transaction(models.Model):

    TRANSACTION_TYPES = [
        ('topup',     'Top Up'),
        ('deduction', 'Fare Deduction'),
        ('earning',   'Driver Earning'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    trip = models.ForeignKey('trips.Trip',on_delete=models.SET_NULL,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.transaction_type} | {self.amount}"

