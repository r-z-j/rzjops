# stocks_app/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Order, DailyBalance
import csv
from django.db.models import Sum, F
from datetime import datetime
from decimal import Decimal
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import timedelta

import io

# def index(request):
#     trades = Order.objects.all().order_by('-date', '-time')
#     daily_balances = DailyBalance.objects.all().order_by('-date')
#     return render(request, 'stocks_app/index.html', {
#         'trades': trades,
#         'daily_balances': daily_balances
#     })

def index(request):
    # Get the most recent DailyBalance
    most_recent_balance = DailyBalance.objects.order_by('-date').first()
    
    # Pass the most recent balance to the template
    context = {
        'most_recent_balance': most_recent_balance
    }
    return render(request, 'stocks_app/index.html', context)


def get_calendar_data(request):
    daily_balances = DailyBalance.objects.all()
    events = []
    
    week_total = Decimal('0')
    
    for balance in daily_balances:
        # Check the day of the week: 0 is Monday, 6 is Sunday
        day_of_week = balance.date.weekday()

        if day_of_week == 6:  # Sunday, display nothing
            continue
        
        if day_of_week == 5:  # Saturday
            # Add the weekly total to the calendar for Saturday
            events.append({
                'title': f'${balance.account_balance}',
                'start': balance.date.strftime('%Y-%m-%d'),
                'borderColor': '#212121',
                'textColor': '#212121',
                'backgroundColor': '#ffb300',  
            })
            events.append({
                'title': f'${week_total}',
                'start': balance.date.strftime('%Y-%m-%d'),
                'end': balance.date.strftime('%Y-%m-%d'),
                'borderColor': '#212121',
                'backgroundColor': '#28a745' if week_total >= 0 else '#dc3545',
            })
            # Reset the week total after adding Saturday's event
            week_total = Decimal('0')
        else:
            # Accumulate the weekly total for Monday to Friday
            week_total += balance.total
            
            events.append({
                'title': f'${balance.total}',
                'start': balance.date.strftime('%Y-%m-%d'),
                'url': f'/stocks/daily/{balance.date.strftime("%Y-%m-%d")}/',
                'borderColor': '#212121',
                'backgroundColor': '#28a745' if balance.total >= 0 else '#dc3545',
            })
    
    return JsonResponse(events, safe=False)


def daily_trades(request, date):
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        trades = Order.objects.filter(date=selected_date).order_by('time')
        daily_balance = DailyBalance.objects.get(date=selected_date)

        # Generate x-axis labels: 5-minute increments from 7:00 AM to 4:00 PM
        start_time = datetime.strptime("07:00", "%H:%M")
        end_time = datetime.strptime("16:00", "%H:%M")
        time_labels = []
        current_time = start_time
        while current_time <= end_time:
            time_labels.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=5)

        # Generate y-axis data points: profit or loss at each time increment
        profit_loss_data = []
        current_balance = daily_balance.prev_balance  # Start from the previous balance
        cumulative_profit_loss = Decimal("0.00")  # Initialize cumulative profit/loss
        trade_index = 0

        for label in time_labels:
            label_time = datetime.strptime(label, "%H:%M").time()

            # Check for trades up to the current time
            while trade_index < len(trades) and trades[trade_index].time <= label_time:
                trade = trades[trade_index]
                if trade.action == 'SOLD':
                    # Calculate profit or loss based on balance difference
                    profit_loss = trade.balance - current_balance
                    cumulative_profit_loss += profit_loss

                    # Update the current balance
                    current_balance = trade.balance

                trade_index += 1

            # Append the cumulative profit/loss at this time
            profit_loss_data.append(float(cumulative_profit_loss))

        return render(request, 'stocks_app/daily_trades.html', {
            'trades': trades,
            'date': selected_date,
            'daily_balance': daily_balance,
            'time_labels': time_labels,
            'profit_loss_data': profit_loss_data,
        })
    except (DailyBalance.DoesNotExist, ValueError):
        return render(request, 'stocks_app/daily_trades.html', {
            'trades': [],
            'date': date,
            'error': 'No trades found for this date.'
        })


def import_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8')
        csv_data = csv.reader(io.StringIO(decoded_file))
        
        # Skip header rows
        for _ in range(3):
            next(csv_data)
            
        for row in csv_data:
            if not row or len(row) < 9 or row[0] == 'DATE':  # Skip empty rows and header row
                continue

            try:
                # Parse date
                if not row[0]:
                    continue
                date = datetime.strptime(row[0], '%m/%d/%y').date()

                # Parse current balance
                balance = row[8].replace(',', '').replace('$', '').strip()
                current_balance = Decimal(balance) if balance else Decimal('0')

                if row[2] == 'TRD':  # Process trade rows
                    time = datetime.strptime(row[1], '%H:%M:%S').time()
                    action = 'BOT' if 'BOT' in row[4] else 'SOLD'
                    shares = abs(int(row[4].split()[1]))

                    misc_fees = row[5].replace(',', '').replace('$', '').strip()
                    misc_fees = Decimal(misc_fees) if misc_fees else None

                    commissions_and_fees = row[6].replace(',', '').replace('$', '').strip()
                    commissions_and_fees = Decimal(commissions_and_fees) if commissions_and_fees else None

                    amount = row[7].replace(',', '').replace('$', '').strip()
                    amount = Decimal(amount) if amount else Decimal('0')

                    Order.objects.create(
                        date=date,
                        time=time,
                        ref_id=row[3],
                        misc_fees=misc_fees,
                        commissions_and_fees=commissions_and_fees,
                        action=action,
                        symbol=row[4].split()[2],  # Extract symbol from description
                        shares=shares,
                        price=Decimal(row[4].split('@')[1].strip()),
                        amount=amount,
                        balance=current_balance,
                    )

                elif row[2] == 'BAL':  # Process balance rows
                    last_balance_record = DailyBalance.objects.order_by('-date').first()
                    last_balance = last_balance_record.account_balance if last_balance_record else Decimal('0')

                    daily_total = current_balance - last_balance

                    DailyBalance.objects.create(
                        date=date - timedelta(days=1),
                        total=daily_total,
                        prev_balance=last_balance,
                        account_balance=current_balance
                    )

            except IntegrityError as e:
                print(f"Duplicate record or error occurred: {e}")
            except Exception as e:
                print(f"Error processing row {row}: {e}")

        messages.success(request, 'CSV file imported successfully!')
        return redirect('stocks_app:index')
    
    return render(request, 'stocks_app/import.html')