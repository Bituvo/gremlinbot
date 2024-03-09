from datetime import datetime, timedelta

weight_function = lambda x: max(-4 * x ** 2 + 0.6, 0.5 * (x + 0.3) ** 2)

def is_eligible_candidate(message):
    if message.attachments:
        if all("image" in attachment.content_type or "video" in attachment.content_type for attachment in message.attachments):
            return True
    return False

def is_last_day_of_month():
    now = datetime.now()
    current_month = now.month
    return (now + timedelta(days=1)).month != current_month
