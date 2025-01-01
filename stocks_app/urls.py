# stocks_app/urls.py
from django.urls import path
from . import views

app_name = 'stocks_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('calendar-data/', views.get_calendar_data, name='calendar_data'),
    path('daily/<str:date>/', views.daily_trades, name='daily_trades'),
    path('import/', views.import_csv, name='import_csv'),
]