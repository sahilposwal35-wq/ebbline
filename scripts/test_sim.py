import datetime
from decimal import Decimal

# Anchor: 2026-10-01, balance: 95,000.00, buffer: 15,000.00
# Projection runs from 2026-10-02 to 2027-10-01 (365 days)

anchor_date = datetime.date(2026, 10, 1)
anchor_balance = Decimal('95000.00')
buffer_min = Decimal('15000.00')

# Rules:
# R1: Salary: +75000 on day 1 of each month (start 2026-01-01)
# R2: Rent: -30000 on day 5 of each month (start 2026-01-05)
# R3: Home Loan EMI: -22000 on day 10 of each month (start 2026-01-10)
# R4: Utilities: -4000 on day 12 of each month (start 2026-01-12)
# R5: SIP: -10000 on day 15 of each month (start 2026-01-15)
# R6: Subscriptions (Discretionary): -3000 on day 8 of each month (start 2026-01-08)
# R7: Dining (Discretionary): -5000 on day 18 of each month (start 2026-01-18)
# R8: Groceries: -3500 every 2 weeks starting 2026-10-03
# R9: Month-End Maintenance: -2000 on 31st of month starting 2026-01-31
# R10: Leap-Year Software: -1200 on 29 Feb starting 2024-02-29 (every 12 months)
# R11: Annual Insurance: -45000 on 20 Nov starting 2026-11-20 (every 12 months)

def simulate():
    balance = anchor_balance
    curr = anchor_date + datetime.timedelta(days=1)
    end = anchor_date + datetime.timedelta(days=365)
    first_breach = None
    min_bal = balance
    min_bal_date = curr

    while curr <= end:
        net = Decimal('0.00')
        # Check rule occurrences
        # Salary on 1st
        if curr.day == 1:
            net += Decimal('75000.00')
        # Groceries every 14 days from 2026-10-03
        if (curr - datetime.date(2026, 10, 3)).days % 14 == 0 and curr >= datetime.date(2026, 10, 3):
            net -= Decimal('3500.00')
        # Rent on 5th
        if curr.day == 5:
            net -= Decimal('30000.00')
        # Subscriptions on 8th
        if curr.day == 8:
            net -= Decimal('3000.00')
        # EMI on 10th
        if curr.day == 10:
            net -= Decimal('22000.00')
        # Utilities on 12th
        if curr.day == 12:
            net -= Decimal('4000.00')
        # SIP on 15th
        if curr.day == 15:
            net -= Decimal('10000.00')
        # Dining on 18th
        if curr.day == 18:
            net -= Decimal('5000.00')
        # Insurance on Nov 20
        if curr.month == 11 and curr.day == 20:
            net -= Decimal('45000.00')
        # Month-end maintenance: clamp 31st
        # For months with < 31 days, lands on last day of month
        # In Oct (31): Oct 31
        # In Nov (30): Nov 30
        last_day_of_month = (datetime.date(curr.year, curr.month + 1, 1) - datetime.timedelta(days=1)).day if curr.month < 12 else 31
        if curr.day == min(31, last_day_of_month):
            net -= Decimal('2000.00')

        balance += net
        if balance < min_bal:
            min_bal = balance
            min_bal_date = curr
        if balance < buffer_min and first_breach is None:
            first_breach = curr

        if curr <= datetime.date(2026, 11, 25):
            print(f"{curr} | Net: {net:10} | Balance: {balance:10} | Below buffer: {balance < buffer_min}")

        curr += datetime.timedelta(days=1)

    print(f"\nResult: First breach = {first_breach}, Min balance = {min_bal} on {min_bal_date}")

if __name__ == '__main__':
    simulate()
