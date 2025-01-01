# stocks_app/models.py
from django.db import models

class Order(models.Model):
    date = models.DateField()
    time = models.TimeField()
    ref_id = models.CharField(max_length=20)
    misc_fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commissions_and_fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    action = models.CharField(max_length=10)  # BOT or SOLD
    symbol = models.CharField(max_length=10)  
    shares = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=4)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    
    def __str__(self):
        return f"{self.date} - {self.action} {self.shares} @ {self.price}"

class DailyBalance(models.Model):
    date = models.DateField(unique=True)
    total = models.DecimalField(max_digits=10, decimal_places=2) # profit loss total for the day
    prev_balance = models.DecimalField(max_digits=10, decimal_places=2)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.date} - Balance: {self.account_balance}"