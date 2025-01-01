# Register your models here.

from django.contrib import admin
from stocks_app.models import Order, DailyBalance

admin.site.register(Order)
admin.site.register(DailyBalance)
