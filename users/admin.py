from django.contrib import admin
from .models import Transaction
# Register your models here.

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'amount', 'transaction_type', 'trip', 'created_at')
    list_filter   = ('transaction_type',)
    search_fields = ('user__username',)


