import os
from PIL import Image, ImageDraw, ImageFont

def generate_er_diagram():
    os.makedirs('docs', exist_ok=True)
    width = 1600
    height = 1100
    image = Image.new('RGB', (width, height), color='#F7F3EA')
    draw = ImageDraw.Draw(image)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_tbl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        font_col = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception:
        font_title = font_tbl = font_col = ImageFont.load_default()

    draw.text((50, 30), "Ebbline Entity Relationship Diagram", fill='#13303A', font=font_title)
    draw.text((50, 65), "Relational Cash Flow Forecasting Engine Schema (MySQL 8.0+)", fill='#5B6B73', font=font_col)

    tables = {
        'account': {
            'rect': (50, 110, 310, 290),
            'cols': ['account_id (PK)', 'name (UQ)', 'account_type (ENUM)', 'buffer_min (DECIMAL)', 'is_active (BOOL)', 'created_at (TIMESTAMP)']
        },
        'balance_checkpoint': {
            'rect': (50, 340, 310, 480),
            'cols': ['checkpoint_id (PK)', 'account_id (FK)', 'as_of_date (DATE)', 'balance (DECIMAL)']
        },
        'category': {
            'rect': (360, 110, 610, 230),
            'cols': ['category_id (PK)', 'name (UQ)', 'is_essential (BOOL)']
        },
        'recurring_rule': {
            'rect': (360, 280, 620, 560),
            'cols': ['rule_id (PK)', 'account_id (FK)', 'category_id (FK)', 'label (VARCHAR)', 'amount (DECIMAL)', 'unit (ENUM)', 'every_n (TINYINT)', 'start_date (DATE)', 'end_date (DATE)', 'is_active (BOOL)']
        },
        'one_off_event': {
            'rect': (360, 600, 620, 780),
            'cols': ['event_id (PK)', 'account_id (FK)', 'category_id (FK)', 'event_date (DATE)', 'amount (DECIMAL)', 'label (VARCHAR)']
        },
        'scenario': {
            'rect': (670, 110, 930, 240),
            'cols': ['scenario_id (PK)', 'name (UQ)', 'description (VARCHAR)', 'created_at (TIMESTAMP)']
        },
        'scenario_change': {
            'rect': (670, 290, 940, 520),
            'cols': ['change_id (PK)', 'scenario_id (FK)', 'rule_id (FK NULL)', 'event_id (FK NULL)', 'action (ENUM)', 'value (DECIMAL)', 'from_date (DATE)', 'to_date (DATE)']
        },
        'projection_run': {
            'rect': (990, 110, 1270, 430),
            'cols': ['run_id (PK)', 'scenario_id (FK)', 'account_id (FK)', 'horizon_start (DATE)', 'horizon_end (DATE)', 'anchor_date (DATE)', 'anchor_balance (DECIMAL)', 'min_balance (DECIMAL)', 'min_balance_date (DATE)', 'first_breach_date (DATE)', 'days_below_buffer (INT)']
        },
        'projection_day': {
            'rect': (1320, 110, 1550, 270),
            'cols': ['run_id (PK, FK)', 'day (PK, DATE)', 'net (DECIMAL)', 'balance (DECIMAL)']
        },
        'projection_event': {
            'rect': (1320, 320, 1560, 550),
            'cols': ['event_id (PK)', 'run_id (FK)', 'due_date (DATE)', 'source_type (ENUM)', 'source_id (INT)', 'label (VARCHAR)', 'category_id (FK)', 'amount (DECIMAL)']
        },
        'actual_txn': {
            'rect': (670, 570, 930, 780),
            'cols': ['txn_id (PK)', 'account_id (FK)', 'txn_date (DATE)', 'amount (DECIMAL)', 'label (VARCHAR)', 'rule_id (FK NULL)', 'event_id (FK NULL)', 'source_hash (CHAR UQ)']
        },
        'rule_history': {
            'rect': (360, 830, 620, 1050),
            'cols': ['history_id (PK)', 'rule_id (FK)', 'changed_at (TIMESTAMP)', 'old_amount, new_amount', 'old_start, new_start', 'old_end, new_end', 'old_active, new_active']
        },
        'calendar_day': {
            'rect': (50, 530, 310, 630),
            'cols': ['day (PK, DATE)']
        }
    }

    for name, info in tables.items():
        x1, y1, x2, y2 = info['rect']
        draw.rounded_rectangle((x1, y1, x2, y2), radius=8, fill='#FFFFFF', outline='#E4DDCF', width=2)
        draw.rounded_rectangle((x1, y1, x2, y1 + 32), radius=8, fill='#0F6B73')
        draw.rectangle((x1, y1 + 20, x2, y1 + 32), fill='#0F6B73')
        draw.text((x1 + 10, y1 + 6), name, fill='#FFFFFF', font=font_tbl)
        curr_y = y1 + 40
        for col in info['cols']:
            color = '#0F6B73' if '(PK' in col else ('#D9922E' if '(FK' in col else '#13303A')
            draw.text((x1 + 10, curr_y), col, fill=color, font=font_col)
            curr_y += 18

    # Relationships lines
    lines = [
        ((310, 180), (360, 300)), # account -> rule
        ((310, 200), (360, 620)), # account -> event
        ((180, 290), (180, 340)), # account -> checkpoint
        ((310, 220), (670, 590)), # account -> actual_txn
        ((310, 150), (990, 150)), # account -> projection_run
        ((610, 150), (620, 320)), # category -> rule
        ((500, 230), (500, 600)), # category -> event
        ((620, 350), (670, 350)), # rule -> scenario_change
        ((620, 640), (670, 420)), # event -> scenario_change
        ((930, 150), (990, 170)), # scenario -> projection_run
        ((800, 240), (800, 290)), # scenario -> scenario_change
        ((1270, 160), (1320, 160)), # run -> day
        ((1270, 250), (1320, 350)), # run -> proj_event
        ((490, 560), (490, 830)), # rule -> rule_history
        ((620, 450), (670, 650)), # rule -> actual_txn
    ]
    for pt1, pt2 in lines:
        draw.line([pt1, pt2], fill='#5B6B73', width=2)

    image.save('docs/er-diagram.png')
    print("ER diagram generated at docs/er-diagram.png")

if __name__ == '__main__':
    generate_er_diagram()
