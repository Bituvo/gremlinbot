from datetime import datetime, timedelta

weight_function = lambda x: max(-4 * x ** 2 + 0.6, 0.5 * (x + 0.3) ** 2)

def is_last_day_of_month():
    now = datetime.now()
    current_month = now.month
    return (now + timedelta(days=1)).month != current_month
