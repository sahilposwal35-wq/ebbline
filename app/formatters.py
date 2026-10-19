from decimal import Decimal
import datetime

def format_inr(val):
    if val is None:
        return "INR 0.00"
    d = Decimal(str(val))
    is_neg = d < 0
    abs_d = abs(d)
    s = f"{abs_d:.2f}"
    parts = s.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) > 3:
        last3 = integer_part[-3:]
        rest = integer_part[:-3]
        res = []
        while len(rest) > 2:
            res.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            res.insert(0, rest)
        grouped = ','.join(res) + ',' + last3
    else:
        grouped = integer_part

    prefix = "INR -" if is_neg else "INR "
    return f"{prefix}{grouped}.{decimal_part}"

def format_date(dt):
    if dt is None:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.date.fromisoformat(dt)
        except Exception:
            return dt
    return dt.strftime("%d %b %Y")
