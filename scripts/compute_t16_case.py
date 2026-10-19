import datetime
from decimal import Decimal

# Hand-calculated 3-month case outside MySQL (T16)
# Account 1: Salaried Primary
# Anchor: 2026-10-01, Balance: 95,000.00, Buffer: 15,000.00
# Horizon: 90 days (2026-10-02 to 2026-12-30)

def compute():
    anchor_date = datetime.date(2026, 10, 1)
    anchor_balance = Decimal('95000.00')
    start_date = anchor_date + datetime.timedelta(days=1)
    end_date = start_date + datetime.timedelta(days=89) # 90 days inclusive

    # Days and transactions for Account 1 in this window:
    # 2026-10-03: Groceries -3500.00
    # 2026-10-05: Rent -30000.00
    # 2026-10-08: Subscriptions -3000.00
    # 2026-10-10: Home Loan EMI -22000.00
    # 2026-10-12: Utilities -4000.00
    # 2026-10-15: SIP -10000.00
    # 2026-10-17: Groceries -3500.00
    # 2026-10-18: Dining -5000.00
    # 2026-10-25: One-off Dental -2500.00
    # 2026-10-31: Groceries -3500.00
    # 2026-10-31: Month-End Maintenance -2000.00
    # 2026-11-01: Salary +75000.00
    # 2026-11-05: Rent -30000.00
    # 2026-11-08: Subscriptions -3000.00
    # 2026-11-10: Home Loan EMI -22000.00
    # 2026-11-10: One-off Diwali Gifts -4000.00
    # 2026-11-12: Utilities -4000.00
    # 2026-11-14: Groceries -3500.00
    # 2026-11-15: SIP -10000.00
    # 2026-11-18: Dining -5000.00
    # 2026-11-20: Annual Insurance -45000.00
    # 2026-11-28: Groceries -3500.00
    # 2026-11-30: Month-End Maintenance -2000.00 (November 30 is clamped from 31)
    # 2026-12-01: Salary +75000.00
    # 2026-12-05: Rent -30000.00
    # 2026-12-08: Subscriptions -3000.00
    # 2026-12-10: Home Loan EMI -22000.00
    # 2026-12-12: Utilities -4000.00
    # 2026-12-12: Groceries -3500.00
    # 2026-12-15: SIP -10000.00
    # 2026-12-15: Quarterly Gadget Budget -6000.00
    # 2026-12-18: Dining -5000.00
    # 2026-12-25: Annual Performance Bonus +50000.00
    # 2026-12-26: Groceries -3500.00

    events = {
        datetime.date(2026, 10, 3): [Decimal('-3500.00')],
        datetime.date(2026, 10, 5): [Decimal('-30000.00')],
        datetime.date(2026, 10, 8): [Decimal('-3000.00')],
        datetime.date(2026, 10, 10): [Decimal('-22000.00')],
        datetime.date(2026, 10, 12): [Decimal('-4000.00')],
        datetime.date(2026, 10, 15): [Decimal('-10000.00')],
        datetime.date(2026, 10, 17): [Decimal('-3500.00')],
        datetime.date(2026, 10, 18): [Decimal('-5000.00')],
        datetime.date(2026, 10, 25): [Decimal('-2500.00')],
        datetime.date(2026, 10, 31): [Decimal('-3500.00'), Decimal('-2000.00')],
        datetime.date(2026, 11, 1): [Decimal('75000.00'), Decimal('-1500.00')],
        datetime.date(2026, 11, 5): [Decimal('-30000.00')],
        datetime.date(2026, 11, 8): [Decimal('-3000.00')],
        datetime.date(2026, 11, 10): [Decimal('-22000.00'), Decimal('-4000.00')],
        datetime.date(2026, 11, 12): [Decimal('-4000.00')],
        datetime.date(2026, 11, 14): [Decimal('-3500.00')],
        datetime.date(2026, 11, 15): [Decimal('-10000.00')],
        datetime.date(2026, 11, 18): [Decimal('-5000.00')],
        datetime.date(2026, 11, 20): [Decimal('-45000.00')],
        datetime.date(2026, 11, 28): [Decimal('-3500.00')],
        datetime.date(2026, 11, 30): [Decimal('-2000.00')],
        datetime.date(2026, 12, 1): [Decimal('75000.00'), Decimal('-1500.00')],
        datetime.date(2026, 12, 5): [Decimal('-30000.00')],
        datetime.date(2026, 12, 8): [Decimal('-3000.00')],
        datetime.date(2026, 12, 10): [Decimal('-22000.00')],
        datetime.date(2026, 12, 12): [Decimal('-4000.00'), Decimal('-3500.00')],
        datetime.date(2026, 12, 15): [Decimal('-10000.00'), Decimal('-6000.00')],
        datetime.date(2026, 12, 18): [Decimal('-5000.00')],
        datetime.date(2026, 12, 25): [Decimal('50000.00')],
        datetime.date(2026, 12, 26): [Decimal('-3500.00')],
    }

    lines = []
    lines.append("Hand Calculated Three Month Case for Account 1")
    lines.append(f"Anchor Date: {anchor_date.strftime('%d %b %Y')}")
    lines.append(f"Anchor Balance: INR {anchor_balance:,.2f}")
    lines.append(f"Horizon: {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')} (90 days)")
    lines.append("")
    lines.append("Daily Balances:")

    curr = start_date
    balance = anchor_balance
    records = []

    while curr <= end_date:
        day_events = events.get(curr, [Decimal('0.00')])
        net = sum(day_events)
        balance += net
        records.append((curr, net, balance))
        lines.append(f"{curr.strftime('%d %b %Y')}: Net INR {net:,.2f}, End Balance INR {balance:,.2f}")
        curr += datetime.timedelta(days=1)

    with open('docs/t16_hand_calculation.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

    print(f"Hand calculation generated: {len(records)} days written to docs/t16_hand_calculation.txt")
    return records

if __name__ == '__main__':
    compute()
