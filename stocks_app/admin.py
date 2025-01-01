# Register your models here.

from django.contrib import admin
from stocks_app.models import Trade, DailyBalance

admin.site.register(Trade)
admin.site.register(DailyBalance)
